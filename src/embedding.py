"""
LSB Embedding Engine.

Implements Algorithm EA (Embedding Algorithm) from Chapter 3, Section 3.7.3.

Embedding pipeline (Ch. 3, §3.5.3):
  1. UTF-8 encode the secret text → payload_bytes.
  2. Generate a random 16-byte salt and 16-byte IV.
  3. Derive AES key + PRSG seed via PBKDF2 (Algorithm KD).
  4. Encrypt payload_bytes → AES-256-CBC ciphertext.
  5. Build 36-byte header: SALT || IV || PAYLOAD_LENGTH (big-endian uint32).
  6. Serialise header + ciphertext as a flat bit array (MSB first per byte).
  7. Embed the first 288 bits (header) into samples[0:288] — one LSB per sample.
  8. Embed the remaining ciphertext bits into PRSG-selected sample indices.
  9. Return modified sample array + quality metrics dict.

The NumPy vectorised approach is used throughout for efficiency on large audio files.
"""

import numpy as np

from .crypto import (
    HEADER_BITS,
    build_header,
    derive_keys,
    encrypt_payload,
    random_iv,
    random_salt,
)
from .metrics import compute_metrics
from .prsg import generate_indices

# Numpy mask to clear the LSB of a signed int16 value
_CLEAR_LSB = np.int16(-2)  # two's-complement 0xFFFE


def _bytes_to_bits(data: bytes) -> np.ndarray:
    """Unpack bytes into a flat uint8 array of 0s and 1s, MSB first."""
    byte_array = np.frombuffer(data, dtype=np.uint8)
    # Unpack 8 bits per byte, MSB first
    bits = np.unpackbits(byte_array)
    return bits.astype(np.uint8)


def embed(
    cover_samples: np.ndarray,
    secret_text: str,
    passphrase: str,
) -> tuple[np.ndarray, dict]:
    """
    Algorithm EA — Audio Steganographic Embedding (Ch. 3, §3.7.3).

    Parameters
    ----------
    cover_samples : 1-D NumPy int16 array of cover audio PCM values.
    secret_text   : Plaintext message to hide (UTF-8).
    passphrase    : User passphrase for key derivation and PRSG seeding.

    Returns
    -------
    (stego_samples, metrics)
      stego_samples : Modified int16 array with hidden payload.
      metrics       : dict with SNR, PSNR, MSE and embedding statistics.
    """
    # Preserve original for metric computation
    cover_copy = cover_samples.copy()
    stego = cover_samples.copy()

    # Step 1 — encode payload
    payload_bytes = secret_text.encode("utf-8")

    # Step 2 — generate cryptographic nonces
    salt = random_salt()
    iv = random_iv()

    # Step 3 — key derivation
    aes_key, prsg_seed = derive_keys(passphrase, salt)

    # Step 4 — AES-256-CBC encryption
    ciphertext = encrypt_payload(payload_bytes, aes_key, iv)
    payload_len = len(ciphertext)  # always a multiple of 16 bytes (PKCS7 padded)

    # Step 5 — assemble header (36 bytes)
    header = build_header(salt, iv, payload_len)

    # Step 6 — serialise header || ciphertext as a bit array
    bitstream = _bytes_to_bits(header + ciphertext)  # shape: (HEADER_BITS + cipher_bits,)

    # Step 7 — embed header into fixed positions: samples[0] … samples[287]
    # Each sample's LSB is replaced with the corresponding header bit.
    header_bits = bitstream[:HEADER_BITS].astype(np.int16)
    stego[:HEADER_BITS] = (stego[:HEADER_BITS] & _CLEAR_LSB) | header_bits

    # Step 8 — embed ciphertext bits into pseudo-randomly selected positions
    cipher_bits = bitstream[HEADER_BITS:]
    indices = generate_indices(prsg_seed, len(stego), len(cipher_bits))
    idx_array = np.array(indices, dtype=np.intp)
    stego[idx_array] = (stego[idx_array] & _CLEAR_LSB) | cipher_bits.astype(np.int16)

    # Step 9 — compute quality metrics
    metrics = compute_metrics(cover_copy, stego)
    metrics["payload_bytes"] = len(payload_bytes)
    metrics["ciphertext_bytes"] = payload_len
    metrics["total_samples"] = len(stego)
    metrics["samples_used"] = HEADER_BITS + len(cipher_bits)
    metrics["capacity_percent"] = round(
        (metrics["samples_used"] / len(stego)) * 100, 4
    )

    return stego, metrics
