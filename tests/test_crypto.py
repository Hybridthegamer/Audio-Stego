"""
Unit tests for src/crypto.py

Tests cover:
  - Key derivation reproducibility (same passphrase + salt → same keys).
  - Key derivation uniqueness (different salts → different keys).
  - AES-256-CBC round-trip (encrypt → decrypt recovers original).
  - Wrong key produces ValueError on decrypt.
  - Header build/parse round-trip.
"""

import os
import struct
import unittest

from src.crypto import (
    AES_BLOCK_SIZE,
    HEADER_SIZE,
    build_header,
    decrypt_payload,
    derive_keys,
    encrypt_payload,
    parse_header,
    random_iv,
    random_salt,
)


class TestDeriveKeys(unittest.TestCase):
    def test_deterministic(self):
        """Same passphrase + salt always produces the same keys."""
        salt = b"\x01" * 16
        k1a, k1b = derive_keys("TestPass1!", salt)
        k2a, k2b = derive_keys("TestPass1!", salt)
        self.assertEqual(k1a, k2a)
        self.assertEqual(k1b, k2b)

    def test_different_salt_different_keys(self):
        """Different salts produce different keys for the same passphrase."""
        ka, _ = derive_keys("SamePassphrase1", b"\x00" * 16)
        kb, _ = derive_keys("SamePassphrase1", b"\xff" * 16)
        self.assertNotEqual(ka, kb)

    def test_key_lengths(self):
        """AES key must be 32 bytes; PRSG seed must be 32 bytes."""
        aes_key, prsg_seed = derive_keys("TestPassphrase99!", b"\xab" * 16)
        self.assertEqual(len(aes_key), 32)
        self.assertEqual(len(prsg_seed), 32)


class TestAES(unittest.TestCase):
    def setUp(self):
        self.passphrase = "SecurePass123!"
        self.salt = random_salt()
        self.aes_key, _ = derive_keys(self.passphrase, self.salt)
        self.iv = random_iv()

    def test_round_trip(self):
        """Encrypt then decrypt recovers original payload."""
        original = "Hello, secret world! 🌍"
        ciphertext = encrypt_payload(original.encode("utf-8"), self.aes_key, self.iv)
        recovered = decrypt_payload(ciphertext, self.aes_key, self.iv)
        self.assertEqual(recovered.decode("utf-8"), original)

    def test_ciphertext_is_padded_multiple(self):
        """Ciphertext length is always a multiple of 16 (PKCS7)."""
        payload = b"short"
        ciphertext = encrypt_payload(payload, self.aes_key, self.iv)
        self.assertEqual(len(ciphertext) % AES_BLOCK_SIZE, 0)

    def test_wrong_key_raises(self):
        """Decrypting with a wrong key raises ValueError (padding error)."""
        ciphertext = encrypt_payload(b"secret data", self.aes_key, self.iv)
        wrong_key = os.urandom(32)
        with self.assertRaises(Exception):
            decrypt_payload(ciphertext, wrong_key, self.iv)

    def test_empty_payload(self):
        """Empty payload round-trips correctly (AES pads to one full block)."""
        ciphertext = encrypt_payload(b"", self.aes_key, self.iv)
        self.assertEqual(len(ciphertext), AES_BLOCK_SIZE)
        recovered = decrypt_payload(ciphertext, self.aes_key, self.iv)
        self.assertEqual(recovered, b"")


class TestHeader(unittest.TestCase):
    def test_round_trip(self):
        """build_header / parse_header are inverse operations."""
        salt = os.urandom(16)
        iv = os.urandom(16)
        payload_len = 256

        header = build_header(salt, iv, payload_len)
        self.assertEqual(len(header), HEADER_SIZE)

        s, i, pl = parse_header(header)
        self.assertEqual(s, salt)
        self.assertEqual(i, iv)
        self.assertEqual(pl, payload_len)

    def test_payload_len_zero(self):
        """payload_len = 0 is encoded and recovered correctly."""
        _, _, pl = parse_header(build_header(b"\x00" * 16, b"\x00" * 16, 0))
        self.assertEqual(pl, 0)

    def test_payload_len_max_uint32(self):
        """payload_len at uint32 maximum is handled correctly."""
        max_val = 2**32 - 1
        _, _, pl = parse_header(build_header(b"\x00" * 16, b"\x00" * 16, max_val))
        self.assertEqual(pl, max_val)


if __name__ == "__main__":
    unittest.main()
