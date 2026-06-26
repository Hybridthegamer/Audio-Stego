"""
Unit tests for src/metrics.py

Tests cover:
  - SNR/PSNR/MSE are infinity when cover == stego (no distortion).
  - MSE is correct for a known distortion.
  - SNR ≥ 30 dB for 1-bit LSB substitution on typical audio (specification target).
  - PSNR is correctly derived from MSE.
"""

import math
import unittest

import numpy as np

from src.metrics import MAX_AMPLITUDE_INT16, compute_metrics


class TestMetrics(unittest.TestCase):
    def test_identical_arrays_inf(self):
        """No distortion → SNR, PSNR = ∞; MSE = 0."""
        arr = np.array([100, -200, 300, -400, 500], dtype=np.int16)
        m = compute_metrics(arr, arr.copy())
        self.assertEqual(m["mse"], 0.0)
        self.assertTrue(math.isinf(m["snr"]))
        self.assertTrue(math.isinf(m["psnr"]))

    def test_mse_known_value(self):
        """MSE for a known single-sample error."""
        cover = np.array([1000] * 100, dtype=np.int16)
        stego = np.array([1000] * 100, dtype=np.int16)
        stego[0] = 1001  # one sample differs by 1
        m = compute_metrics(cover, stego)
        expected_mse = (1.0 ** 2) / 100
        self.assertAlmostEqual(m["mse"], expected_mse, places=6)

    def test_snr_formula(self):
        """SNR matches the formula 10*log10(signal_power/noise_power)."""
        np.random.seed(42)
        cover = np.random.randint(-10000, 10000, size=1000, dtype=np.int16)
        stego = cover.copy()
        # Flip LSB of every sample
        stego = ((stego.astype(np.int32) & ~1) | 1).clip(-32768, 32767).astype(np.int16)
        m = compute_metrics(cover, stego)
        signal_p = float(np.mean(cover.astype(np.float64) ** 2))
        diff = cover.astype(np.float64) - stego.astype(np.float64)
        noise_p = float(np.mean(diff ** 2))
        expected_snr = 10 * math.log10(signal_p / noise_p) if noise_p > 0 else math.inf
        self.assertAlmostEqual(m["snr"], round(expected_snr, 4), places=2)

    def test_psnr_formula(self):
        """PSNR = 10*log10(MAX² / MSE)."""
        cover = np.full(1000, 10000, dtype=np.int16)
        stego = cover.copy()
        stego[::2] += 1  # every other sample flipped by 1
        m = compute_metrics(cover, stego)
        expected_psnr = 10 * math.log10(MAX_AMPLITUDE_INT16 ** 2 / m["mse"])
        self.assertAlmostEqual(m["psnr"], round(expected_psnr, 4), places=2)

    def test_1bit_lsb_meets_snr_target(self):
        """1-bit LSB substitution must achieve SNR ≥ 30 dB (Ch. 3, §3.3.1)."""
        np.random.seed(0)
        # Simulate a loud audio signal
        cover = (np.random.randn(44100) * 10000).clip(-32768, 32767).astype(np.int16)
        stego = cover.copy()
        # Flip LSBs on the first 10% of samples (worst-case at capacity limit)
        n_embed = len(cover) // 10
        stego[:n_embed] = ((stego[:n_embed].astype(np.int32) & ~1) | 1
                           ).clip(-32768, 32767).astype(np.int16)
        m = compute_metrics(cover, stego)
        self.assertGreaterEqual(m["snr"], 30.0,
                                f"SNR {m['snr']} dB is below the 30 dB target.")


if __name__ == "__main__":
    unittest.main()
