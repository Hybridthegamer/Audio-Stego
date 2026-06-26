"""
WAV file I/O and capacity utilities.

Scope (Ch. 1, §1.5): Only 16-bit PCM WAV files are supported as the cover medium.
WAV is uncompressed and provides a lossless baseline — lossy formats (MP3, AAC)
would destroy LSB-embedded data upon re-encoding.

System specifications (Ch. 3, Table 3.1):
  - Supported format: WAV PCM, 16-bit, 44.1 kHz or 22.05 kHz, mono or stereo.
  - Stereo files are treated as a flat interleaved sample array (L, R, L, R, …).
  - The output stego-audio is written with identical format parameters.

Capacity safety threshold: at most 10 % of total samples are used for embedding
(header + ciphertext), as specified in Table 3.1.
"""

import wave

import numpy as np

from .crypto import HEADER_BITS, AES_BLOCK_SIZE

# 16-bit signed PCM is the only supported sample width (2 bytes per sample)
SUPPORTED_SAMPLE_WIDTH = 2

# 10 % safety threshold on total samples used for embedding (Ch. 3, Table 3.1)
CAPACITY_SAFETY_RATIO = 0.10


class AudioFormatError(Exception):
    """Raised when the WAV file does not meet format requirements."""


def read_wav(path: str) -> tuple[np.ndarray, wave._wave_params]:
    """
    Read a WAV file and return (samples, params).

    samples : 1-D NumPy int16 array of PCM values (interleaved for stereo).
    params  : namedtuple returned by wave.getparams(), used for writing stego output.

    Raises AudioFormatError if the file is not 16-bit PCM.
    """
    with wave.open(path, "rb") as wf:
        params = wf.getparams()
        if wf.getsampwidth() != SUPPORTED_SAMPLE_WIDTH:
            raise AudioFormatError(
                f"Only 16-bit PCM WAV files are supported. "
                f"'{path}' has {wf.getsampwidth() * 8}-bit samples."
            )
        raw = wf.readframes(wf.getnframes())

    samples = np.frombuffer(raw, dtype=np.int16).copy()
    return samples, params


def write_wav(path: str, samples: np.ndarray, params: wave._wave_params) -> None:
    """Write a NumPy int16 sample array to a WAV file using the given params."""
    with wave.open(path, "wb") as wf:
        wf.setparams(params)
        wf.writeframes(samples.astype(np.int16).tobytes())


def get_audio_info(path: str) -> dict:
    """
    Return a human-readable dictionary of WAV file metadata.
    Used by the GUI to display file information to the user.
    """
    with wave.open(path, "rb") as wf:
        params = wf.getparams()
        n_frames = wf.getnframes()
        framerate = wf.getframerate()
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()

    duration_s = n_frames / framerate
    total_samples = n_frames * n_channels  # interleaved samples

    return {
        "sample_rate_hz": framerate,
        "bit_depth": sampwidth * 8,
        "channels": n_channels,
        "duration_s": round(duration_s, 2),
        "total_samples": total_samples,
        "max_payload_bytes": get_max_message_bytes(total_samples),
    }


def get_max_message_bytes(total_samples: int) -> int:
    """
    Compute the maximum plaintext message size (bytes) that can be safely embedded.

    Calculation:
      max_usable_samples = floor(total_samples × CAPACITY_SAFETY_RATIO)
      available_for_cipher_bits = max_usable_samples − HEADER_BITS
      max_ciphertext_bytes = available_for_cipher_bits ÷ 8
      max_payload_bytes = max_ciphertext_bytes − AES_BLOCK_SIZE   (worst-case padding)
    """
    max_usable = int(total_samples * CAPACITY_SAFETY_RATIO)
    available_bits = max_usable - HEADER_BITS
    if available_bits <= 0:
        return 0
    max_cipher_bytes = available_bits // 8
    max_payload = max(0, max_cipher_bytes - AES_BLOCK_SIZE)
    return max_payload
