"""
LSB Extraction Engine.

Implements Algorithm XA (Extraction Algorithm) from Chapter 3, Section 3.7.4.

Extraction pipeline (Ch. 3, §3.5.3 — reversed):
  1. Read stego audio samples into a 1-D int16 NumPy array.
  2. Extract the first 288 LSBs (samples 0-287) → reconstruct the 36-byte header.
  3. Parse header to recover SALT, IV, and PAYLOAD_LENGTH.
  4. Re-derive AES key + PRSG seed via PBKDF2(passphrase, extracted_salt).
  5. Regenerate the pseudo-random index sequence using the recovered PRSG seed.
  6. Read LSBs at those indices → reconstruct the ciphertext byte array.
  7. Decrypt ciphertext with AES-256-CBC (re-derived key + extracted IV).
  8. UTF-8 decode the plaintext and return it.
  9. Raise AuthenticationError on any decryption / decoding failure.

Security note (Ch. 3, §3.3.1): A wrong passphrase produces an incorrect AES key,
causing AES-CBC unpadding to fail.  This error is caught and re-raised as
AuthenticationError — no portion of the payload is exposed.
"""

import numpy as np

from .crypto import (
    HEADER_BITS,
    HEADER_SIZE,
    derive_keys,
    decrypt_payload,
    parse_header,
)
from .prsg import generate_indices


class AuthenticationError(Exception):
    """Raised when the passphrase is wrong or the stego-audio is corrupted."""


def _bits_to_bytes(bits: np.ndarray) -> bytes:
    """Pack a flat array of 0/1 values (uint8) back into a bytes object, MSB first."""
    # Ensure length is a multiple of 8
    padded = np.zeros(((len(bits) + 7) // 8) * 8, dtype=np.uint8)
    padded[: len(bits)] = bits
    return np.packbits(padded).tobytes()


def extract(stego_samples: np.ndarray, passphrase: str) -> str:
    """
    Algorithm XA — Audio Steganographic Extraction (Ch. 3, §3.7.4).

    Parameters
    ----------
    stego_samples : 1-D NumPy int16 array read from the stego WAV file.
    passphrase    : User passphrase (must match the one used during embedding).

    Returns
    -------
    The recovered plaintext secret message (str).

    Raises
    ------
    AuthenticationError if the passphrase is incorrect or the data is corrupted.
    """
    # Step 2 — extract header bits from fixed positions (samples 0-287)
    header_lsbs = (stego_samples[:HEADER_BITS].astype(np.uint8)) & np.uint8(1)
    header_bytes = _bits_to_bytes(header_lsbs)[:HEADER_SIZE]

    # Step 3 — parse header
    salt, iv, payload_len = parse_header(header_bytes)

    # Step 4 — re-derive keys using the extracted salt
    aes_key, prsg_seed = derive_keys(passphrase, salt)

    # Step 5 — regenerate the same pseudo-random index sequence
    cipher_bit_count = payload_len * 8
    indices = generate_indices(prsg_seed, len(stego_samples), cipher_bit_count)
    idx_array = np.array(indices, dtype=np.intp)

    # Step 6 — read LSBs at those indices to reconstruct the ciphertext
    cipher_lsbs = (stego_samples[idx_array].astype(np.uint8)) & np.uint8(1)
    ciphertext = _bits_to_bytes(cipher_lsbs)[:payload_len]

    # Steps 7-8 — decrypt and decode
    try:
        payload_bytes = decrypt_payload(ciphertext, aes_key, iv)
        return payload_bytes.decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise AuthenticationError(
            "Incorrect passphrase or corrupted stego-audio. "
            "Decryption failed — no message could be recovered."
        ) from exc
