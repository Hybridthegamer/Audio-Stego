"""
Pseudo-Random Sample Index Generator (PRSG).

Implements Algorithm PRSG from Chapter 3, Section 3.7.2.

The PRSG converts a 32-byte seed (derived via PBKDF2) into an integer and uses
Python's built-in random.Random to draw a non-repeating sequence of audio sample
indices.  The first HEADER_BITS (288) sample positions are reserved for the fixed
header and excluded from the PRSG pool.

Why random.sample on a range?
  - Python 3's random.sample accepts a range object and samples it in O(k) time
    without expanding the full range into a list, keeping memory overhead low for
    large audio files.
  - Deterministic given the same seed, so the extraction side can reproduce the
    exact same index sequence using only the stored salt.
"""

import random

from .crypto import HEADER_BITS  # 288 — samples 0-287 are reserved for header


class CapacityError(Exception):
    """Raised when the payload is too large for the selected cover audio."""


def generate_indices(prsg_seed: bytes, total_samples: int, bits_needed: int) -> list[int]:
    """
    Algorithm PRSG — Pseudo-Random Sample Index Generation (Ch. 3, §3.7.2).

    Parameters
    ----------
    prsg_seed     : 32-byte seed derived from the passphrase via PBKDF2.
    total_samples : Total number of int16 samples in the cover audio array.
    bits_needed   : Number of unique sample indices required (one per payload bit).

    Returns
    -------
    A list of `bits_needed` unique integers drawn from range(HEADER_BITS, total_samples).
    """
    # Convert seed bytes to a large integer for seeding Python's Mersenne Twister
    seed_int = int.from_bytes(prsg_seed, byteorder="big")
    rng = random.Random(seed_int)

    # Exclude the first HEADER_BITS samples (fixed header positions 0-287)
    available_pool = range(HEADER_BITS, total_samples)

    if bits_needed > len(available_pool):
        raise CapacityError(
            f"Payload requires {bits_needed} sample positions, but only "
            f"{len(available_pool)} are available after the reserved header region. "
            "Use a longer cover audio file or a shorter message."
        )

    return rng.sample(available_pool, bits_needed)
