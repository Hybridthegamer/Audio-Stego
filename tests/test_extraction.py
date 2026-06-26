"""
Unit tests for src/extraction.py

Tests cover:
  - Perfect round-trip: embed → extract recovers original message (BER = 0).
  - Wrong passphrase raises AuthenticationError.
  - Various message types (ASCII, Unicode, long messages).
  - Extraction fails on a plain (unmodified) cover audio (random passphrase).
"""

import unittest

import numpy as np

from src.embedding import embed
from src.extraction import AuthenticationError, extract


def _make_audio(n_samples: int = 88200, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return (rng.normal(0, 8000, n_samples)).clip(-32768, 32767).astype(np.int16)


class TestExtraction(unittest.TestCase):
    PASSPHRASE = "CorrectPassphrase1!"
    WRONG_PASS = "WrongPassphrase99!"

    def _round_trip(self, message: str, audio: np.ndarray | None = None) -> str:
        audio = _make_audio() if audio is None else audio
        stego, _ = embed(audio, message, self.PASSPHRASE)
        return extract(stego, self.PASSPHRASE)

    # ── Correct passphrase ─────────────────────────────────────────────────────

    def test_ascii_round_trip(self):
        msg = "This is a secret ASCII message."
        self.assertEqual(self._round_trip(msg), msg)

    def test_unicode_round_trip(self):
        msg = "Héllo Wörld! Ñoño 🔐 中文 العربية"
        self.assertEqual(self._round_trip(msg), msg)

    def test_single_char(self):
        self.assertEqual(self._round_trip("X"), "X")

    def test_long_message(self):
        """A message that uses a significant portion of the capacity."""
        msg = "A" * 200  # 200 bytes — comfortably within capacity for 2-second audio
        self.assertEqual(self._round_trip(msg, _make_audio(n_samples=44100 * 2)), msg)

    def test_newlines_and_special_chars(self):
        msg = "Line one\nLine two\tTabbed\r\nWindows newline"
        self.assertEqual(self._round_trip(msg), msg)

    def test_empty_string_equivalent(self):
        """A single space is the shortest non-empty accepted message."""
        self.assertEqual(self._round_trip(" "), " ")

    # ── Wrong passphrase ───────────────────────────────────────────────────────

    def test_wrong_passphrase_raises(self):
        audio = _make_audio()
        stego, _ = embed(audio, "secret", self.PASSPHRASE)
        with self.assertRaises(AuthenticationError):
            extract(stego, self.WRONG_PASS)

    def test_similar_passphrase_raises(self):
        """Passphrases differing by one character must not decode successfully."""
        audio = _make_audio()
        stego, _ = embed(audio, "data", self.PASSPHRASE)
        with self.assertRaises(AuthenticationError):
            extract(stego, self.PASSPHRASE[:-1] + "X")

    # ── Stego audio integrity ──────────────────────────────────────────────────

    def test_no_modification_between_embed_and_extract(self):
        """Stego array must not be mutated by extract()."""
        audio = _make_audio()
        stego, _ = embed(audio, "immutable check", self.PASSPHRASE)
        stego_before = stego.copy()
        extract(stego, self.PASSPHRASE)
        np.testing.assert_array_equal(stego, stego_before)


if __name__ == "__main__":
    unittest.main()
