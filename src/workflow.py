"""
Workflow Controller — Application Logic Layer.

Orchestrates the embedding and extraction pipelines as described in
Chapter 3, Section 3.4.1 (System Architecture) and Section 3.5.3 (Processing Design).

Responsibilities:
  - Input validation (passphrase length, file existence, format checks, capacity).
  - Calling File I/O → Embedding/Extraction modules in the correct order.
  - Returning results or propagating typed exceptions to the GUI layer.

Non-functional requirement (Ch. 3, §3.3.1):
  - Passphrase minimum length: 8 characters.
  - Target SNR ≥ 30 dB (enforced by 1-bit-per-sample LSB; validated post-embed).
"""

import os

from .embedding import embed
from .extraction import extract, AuthenticationError  # noqa: F401 — re-exported
from .file_io import (
    AudioFormatError,  # noqa: F401 — re-exported
    get_audio_info,
    get_max_message_bytes,
    read_wav,
    write_wav,
)
from .prsg import CapacityError  # noqa: F401 — re-exported

MIN_PASSPHRASE_LEN = 8  # enforced by §3.3.1 non-functional requirements


def validate_passphrase(passphrase: str) -> None:
    if len(passphrase) < MIN_PASSPHRASE_LEN:
        raise ValueError(
            f"Passphrase must be at least {MIN_PASSPHRASE_LEN} characters long."
        )


def embed_message(
    cover_path: str,
    secret_text: str,
    passphrase: str,
    output_path: str,
) -> dict:
    """
    Full embedding workflow (Ch. 3, §3.5.3 — Embedding Operation).

    Parameters
    ----------
    cover_path  : Path to the input cover WAV file.
    secret_text : Plaintext message to embed.
    passphrase  : User passphrase (≥ 8 characters).
    output_path : Path where the stego WAV file will be written.

    Returns
    -------
    metrics dict containing SNR, PSNR, MSE and embedding statistics.

    Raises
    ------
    ValueError        : Empty message, short passphrase, or non-WAV output extension.
    FileNotFoundError : Cover file does not exist.
    AudioFormatError  : WAV file is not 16-bit PCM.
    CapacityError     : Payload is too large for the selected cover audio.
    """
    validate_passphrase(passphrase)

    if not secret_text.strip():
        raise ValueError("The secret message cannot be empty.")

    if not os.path.isfile(cover_path):
        raise FileNotFoundError(f"Cover audio file not found: {cover_path}")

    samples, params = read_wav(cover_path)  # raises AudioFormatError if not 16-bit

    max_bytes = get_max_message_bytes(len(samples))
    payload_size = len(secret_text.encode("utf-8"))
    if payload_size > max_bytes:
        raise CapacityError(
            f"Message is too large ({payload_size:,} bytes). "
            f"Maximum capacity for this audio file: {max_bytes:,} bytes "
            f"({max_bytes * 8:,} bits)."
        )

    stego_samples, metrics = embed(samples, secret_text, passphrase)
    write_wav(output_path, stego_samples, params)

    return metrics


def extract_message(stego_path: str, passphrase: str) -> str:
    """
    Full extraction workflow (Ch. 3, §3.5.3 — Extraction Operation).

    Parameters
    ----------
    stego_path : Path to the stego WAV file.
    passphrase : Passphrase used during embedding.

    Returns
    -------
    The recovered plaintext secret message.

    Raises
    ------
    ValueError           : Short passphrase.
    FileNotFoundError    : Stego file does not exist.
    AudioFormatError     : WAV file is not 16-bit PCM.
    AuthenticationError  : Wrong passphrase or corrupted stego-audio.
    """
    validate_passphrase(passphrase)

    if not os.path.isfile(stego_path):
        raise FileNotFoundError(f"Stego audio file not found: {stego_path}")

    samples, _ = read_wav(stego_path)
    return extract(samples, passphrase)
