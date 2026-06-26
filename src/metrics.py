"""
Objective audio quality metrics.

Implements the performance evaluation metrics described in Chapter 2, Section 2.8,
and required by the non-functional requirements in Chapter 3, Section 3.3.1:

  SNR  — Signal-to-Noise Ratio (dB)  :  10 × log10(Σx² / Σ(x - x̂)²)
  PSNR — Peak Signal-to-Noise Ratio   :  10 × log10(MAX² / MSE)
  MSE  — Mean Squared Error           :  (1/N) × Σ(x - x̂)²

A higher SNR/PSNR indicates better imperceptibility; lower MSE is better.
The non-functional requirement specifies SNR ≥ 30 dB (§3.3.1).

For 16-bit signed PCM, MAX = 32767 (maximum representable amplitude).
"""

import math

import numpy as np

MAX_AMPLITUDE_INT16 = 32767.0  # Peak amplitude for 16-bit signed PCM


def compute_metrics(cover: np.ndarray, stego: np.ndarray) -> dict:
    """
    Compute SNR, PSNR, and MSE between cover and stego audio sample arrays.

    Both arrays must be 1-D NumPy int16 arrays of the same length.

    Returns
    -------
    dict with keys: 'snr' (dB), 'psnr' (dB), 'mse'
    All float values, rounded to 4 decimal places.
    """
    cover_f = cover.astype(np.float64)
    stego_f = stego.astype(np.float64)
    diff = cover_f - stego_f

    mse = float(np.mean(diff ** 2))

    if mse == 0.0:
        snr = math.inf
        psnr = math.inf
    else:
        signal_power = float(np.mean(cover_f ** 2))
        snr = 10.0 * math.log10(signal_power / mse) if signal_power > 0 else 0.0
        psnr = 10.0 * math.log10((MAX_AMPLITUDE_INT16 ** 2) / mse)

    return {
        "snr": round(snr, 4),
        "psnr": round(psnr, 4),
        "mse": round(mse, 6),
    }
