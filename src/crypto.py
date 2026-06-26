"""
Cryptographic primitives for the Audio Steganography System.

Implements Algorithm KD (Key Derivation) from Chapter 3, Section 3.7.1:
  - PBKDF2-HMAC-SHA256 with 100,000 iterations, producing a 64-byte master key.
  - First 32 bytes → AES-256 key; last 32 bytes → PRSG seed.
  - AES-256-CBC encryption/decryption via PyCryptodome.
  - 36-byte header: SALT (16B) || IV (16B) || PAYLOAD_LENGTH (4B big-endian uint32).
"""

import hashlib
import os
import struct

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# Header layout (fixed, prepended to every embedded bitstream)
HEADER_SIZE = 36          # bytes: 16 (salt) + 16 (IV) + 4 (payload_len)
HEADER_BITS = HEADER_SIZE * 8  # 288 bits → occupies audio samples 0-287

PBKDF2_ITERATIONS = 100_000
PBKDF2_DKLEN = 64         # 64 bytes → 32 for AES key + 32 for PRSG seed
AES_KEY_SIZE = 32         # AES-256
AES_BLOCK_SIZE = 16       # CBC block size
SALT_SIZE = 16
IV_SIZE = 16
PAYLOAD_LEN_SIZE = 4      # uint32 big-endian


def derive_keys(passphrase: str, salt: bytes) -> tuple[bytes, bytes]:
    """
    Algorithm KD — Key Derivation from Passphrase (Ch. 3, §3.7.1).

    Applies PBKDF2-HMAC-SHA256 to derive a 64-byte master key, then splits it:
      aes_key   = master_key[0:32]  → used for AES-256-CBC encryption
      prsg_seed = master_key[32:64] → used to seed the PRSG
    """
    master_key = hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=passphrase.encode("utf-8"),
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
        dklen=PBKDF2_DKLEN,
    )
    aes_key = master_key[:AES_KEY_SIZE]
    prsg_seed = master_key[AES_KEY_SIZE:]
    return aes_key, prsg_seed


def encrypt_payload(payload_bytes: bytes, aes_key: bytes, iv: bytes) -> bytes:
    """Encrypt payload_bytes with AES-256-CBC. Returns PKCS7-padded ciphertext."""
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(payload_bytes, AES_BLOCK_SIZE))


def decrypt_payload(ciphertext: bytes, aes_key: bytes, iv: bytes) -> bytes:
    """
    Decrypt ciphertext with AES-256-CBC and unpad.

    Raises ValueError on padding error (wrong passphrase or corrupted data).
    """
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ciphertext), AES_BLOCK_SIZE)


def build_header(salt: bytes, iv: bytes, payload_len: int) -> bytes:
    """
    Assemble the 36-byte embedded header (Table 3.3, Ch. 3):
      SALT (16B) || IV (16B) || PAYLOAD_LENGTH (4B big-endian uint32)
    """
    return salt + iv + struct.pack(">I", payload_len)


def parse_header(header_bytes: bytes) -> tuple[bytes, bytes, int]:
    """
    Parse the 36-byte header produced by build_header().
    Returns (salt, iv, payload_len).
    """
    salt = header_bytes[:SALT_SIZE]
    iv = header_bytes[SALT_SIZE: SALT_SIZE + IV_SIZE]
    (payload_len,) = struct.unpack(">I", header_bytes[SALT_SIZE + IV_SIZE:])
    return salt, iv, payload_len


def random_salt() -> bytes:
    return os.urandom(SALT_SIZE)


def random_iv() -> bytes:
    return os.urandom(IV_SIZE)
