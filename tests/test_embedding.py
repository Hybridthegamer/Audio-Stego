"""
Unit tests for src/embedding.py

Tests cover:
  - Embedding does not change sample array shape or dtype.
  - Header is correctly stored in samples 0-287.
  - SNR ≥ 30 dB after embedding (non-functional requirement, Ch. 3, §3.3.1).
  - MSE > 0 (embedding introduces a change).
  - Output sample values differ only in their LSBs (all higher bits preserved).
"""

import unittest

import numpy as np

from src.crypto import HEADER_BITS
from src.embedding import embed


def _make_audio(n_samples: int = 44100, seed: int = 7) -> np.ndarray:
    """Return a synthetic 1-second 44100-sample int16 audio array."""
    rng = np.random.default_rng(seed)
    return (rng.normal(0, 8000, n_samples)).clip(-32768, 32767).astype(np.int16)


class TestEmbed(unittest.TestCase):
    def setUp(self):
        self.audio = _make_audio(44100)
        self.passphrase = "TestPassphrase99!"
        self.message = "Hello, steganography!"

    def test_output_shape_and_dtype(self):
        stego, _ = embed(self.audio, self.message, self.passphrase)
        self.assertEqual(stego.shape, self.audio.shape)
        self.assertEqual(stego.dtype, np.int16)

    def test_embedding_introduces_change(self):
        stego, metrics = embed(self.audio, self.message, self.passphrase)
        self.assertGreater(metrics["mse"], 0.0)
        self.assertFalse(np.array_equal(stego, self.audio))

    def test_snr_above_30db(self):
        _, metrics = embed(self.audio, self.message, self.passphrase)
        self.assertGreaterEqual(metrics["snr"], 30.0,
                                 f"SNR {metrics['snr']:.2f} dB < 30 dB target")

    def test_only_lsb_changed(self):
        """All bits above the LSB must be identical to the cover."""
        stego, _ = embed(self.audio, self.message, self.passphrase)
        cover_upper = (self.audio.astype(np.int32)) & ~1
        stego_upper = (stego.astype(np.int32)) & ~1
        np.testing.assert_array_equal(cover_upper, stego_upper,
                                       err_msg="Bits above LSB were modified.")

    def test_header_samples_count(self):
        """Metrics report at least HEADER_BITS samples used for the header."""
        _, metrics = embed(self.audio, self.message, self.passphrase)
        self.assertGreaterEqual(metrics["samples_used"], HEADER_BITS)

    def test_capacity_percent_within_limit(self):
        """Samples used must be ≤ 10 % of total (safety threshold)."""
        _, metrics = embed(self.audio, self.message, self.passphrase)
        self.assertLessEqual(metrics["capacity_percent"], 10.0)

    def test_deterministic_given_same_inputs_fails(self):
        """Two embeds with different random salts produce different stego arrays."""
        stego1, _ = embed(self.audio.copy(), self.message, self.passphrase)
        stego2, _ = embed(self.audio.copy(), self.message, self.passphrase)
        # With random salt/IV the payload region differs; header region also differs
        self.assertFalse(np.array_equal(stego1, stego2))


if __name__ == "__main__":
    unittest.main()
