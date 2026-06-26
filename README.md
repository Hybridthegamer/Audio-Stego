# Audio Steganography System

A desktop application for hiding secret text messages inside WAV audio files using **Enhanced Pseudo-Random LSB Substitution** combined with **AES-256-CBC encryption**. Built as the implementation artefact for a Final Year Project on *Information Hiding Using Audio Steganography*.

---

## Table of Contents

1. [Overview](#1-overview)
2. [System Requirements](#2-system-requirements)
3. [Setup and Installation](#3-setup-and-installation)
4. [Running the Application](#4-running-the-application)
5. [Running the Tests](#5-running-the-tests)
6. [How It Works](#6-how-it-works)
7. [Tool Stack Rationale](#7-tool-stack-rationale)
8. [Performance Targets](#8-performance-targets)
9. [Project Structure](#9-project-structure)

---

## 1. Overview

Audio steganography conceals the *existence* of a communication by embedding a secret payload inside an ordinary-sounding audio file. This system extends basic LSB substitution with:

- **AES-256-CBC encryption** of the payload before embedding, so that even if the stego-audio is detected, the message remains confidential.
- **PBKDF2-HMAC-SHA256 key derivation** (100 000 iterations) from a user passphrase, producing both the AES key and a PRSG seed.
- **Pseudo-random sample selection** — payload bits are scattered across randomly chosen sample positions (determined by the passphrase), making the embedding statistically less detectable than sequential LSB substitution.
- **Objective quality metrics** (SNR, PSNR, MSE) reported after every embedding operation, verifying the >= 30 dB SNR non-functional requirement.

---

## 2. System Requirements

| Requirement | Minimum |
|---|---|
| Python | 3.10 or higher |
| Operating System | Windows 10/11 · Ubuntu 20.04+ · macOS 11+ |
| RAM | 512 MB (sufficient for audio files up to ~10 minutes) |
| Disk space | ~50 MB (Python packages) |
| Audio input format | WAV, 16-bit PCM, mono or stereo |
| Sampling rates supported | 22 050 Hz · 44 100 Hz · 48 000 Hz |

> **Note:** Tkinter is included with the standard CPython distribution on Windows and macOS. On Linux you may need to install it separately — see [Setup](#3-setup-and-installation).

---

## 3. Setup and Installation

### 3.1 Clone the repository

```bash
git clone https://github.com/hybridthegamer/audio-stego.git
cd audio-stego
```

### 3.2 Create a virtual environment (recommended)

```bash
python -m venv .venv

# Activate (Linux / macOS)
source .venv/bin/activate

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1
```

### 3.3 Install Python dependencies

```bash
pip install -r requirements.txt
```

The only two third-party packages required are:

| Package | Version | Purpose |
|---|---|---|
| `pycryptodome` | >= 3.19 | AES-256-CBC encryption / decryption |
| `numpy` | >= 1.24 | Vectorised audio sample manipulation and metrics |

All other imports (`wave`, `hashlib`, `os`, `struct`, `random`, `tkinter`, `threading`) are part of the Python standard library.

### 3.4 Install Tkinter on Linux (if missing)

```bash
# Debian / Ubuntu
sudo apt-get install python3-tk

# Fedora / RHEL
sudo dnf install python3-tkinter

# Arch Linux
sudo pacman -S tk
```

---

## 4. Running the Application

```bash
python main.py
```

The graphical interface has two tabs:

### Embed tab

1. Click **Browse...** to select your cover WAV file. The file info (sample rate, bit depth, channel count, duration) and maximum payload capacity are displayed immediately.
2. Type your secret message in the text area. The live character and byte count updates as you type.
3. Enter a passphrase (minimum 8 characters). This passphrase controls both the AES encryption key and the pseudo-random scatter pattern — it is **required** for extraction.
4. Choose an output path for the stego WAV file (defaults to `<cover>_stego.wav`).
5. Click **EMBED MESSAGE**. On completion, SNR, PSNR, MSE, and capacity-used are displayed in the metrics panel. The SNR indicator shows whether the >= 30 dB imperceptibility target is met.

### Extract tab

1. Browse to the stego WAV file.
2. Enter the passphrase used during embedding.
3. Click **EXTRACT MESSAGE**. The recovered plaintext appears in the output area. An incorrect passphrase produces an authentication error without exposing any part of the message.

---

## 5. Running the Tests

```bash
python -m unittest discover -s tests -v
```

The test suite covers:

| Test module | What is tested |
|---|---|
| `tests/test_crypto.py` | Key derivation determinism, AES round-trips, wrong-key rejection, header serialisation |
| `tests/test_metrics.py` | SNR/PSNR/MSE formulae, >= 30 dB SNR for 1-bit LSB embedding |
| `tests/test_embedding.py` | Output shape/dtype, SNR target, only LSBs modified, capacity limits |
| `tests/test_extraction.py` | ASCII/Unicode round-trips, wrong-passphrase `AuthenticationError`, stego array immutability |

---

## 6. How It Works

### 6.1 Embedding (Algorithm EA)

```
secret_text --> UTF-8 encode --> payload_bytes
passphrase + random_salt --> PBKDF2-HMAC-SHA256 (100 000 iters, 64 B) --> aes_key (32 B) + prsg_seed (32 B)
payload_bytes --> AES-256-CBC (aes_key, random_IV) --> ciphertext

header = salt (16 B) || IV (16 B) || len(ciphertext) as uint32 BE (4 B)   <- 36 bytes total

bitstream = bits(header) + bits(ciphertext)

  Samples 0 - 287 :  header bits embedded sequentially (1 LSB per sample)
  Samples 288 - N :  ciphertext bits embedded at PRSG-selected positions
                       (seeded from prsg_seed, non-repeating)

stego WAV written with identical format parameters as cover WAV.
SNR, PSNR, MSE computed and displayed.
```

### 6.2 Extraction (Algorithm XA)

```
stego WAV read --> int16 sample array
LSBs of samples[0:288] --> header_bytes --> parse salt, IV, ciphertext_len
passphrase + extracted_salt --> PBKDF2 --> aes_key + prsg_seed  (same as embedding)
PRSG(prsg_seed) --> same index sequence
LSBs at those indices --> ciphertext bytes
AES-256-CBC decrypt (aes_key, IV) --> payload_bytes --> UTF-8 decode --> secret_text
```

A wrong passphrase produces a different AES key, causing AES-CBC PKCS7 unpadding to fail with a `ValueError`, which is caught and re-raised as `AuthenticationError` — no partial data is exposed.

### 6.3 Quality metrics

| Metric | Formula | Good range |
|---|---|---|
| SNR | 10 x log10 (sum(x^2) / sum((x-x_hat)^2)) dB | >= 30 dB |
| PSNR | 10 x log10 (32767^2 / MSE) dB | higher is better |
| MSE | (1/N) x sum((x-x_hat)^2) | lower is better |

---

## 7. Tool Stack Rationale

### Python 3.10+

Python was specified in the project scope (Chapter 1, Section 1.5) as the implementation platform. It provides:
- A rich ecosystem of signal-processing and cryptographic libraries.
- Cross-platform execution without recompilation.
- Rapid prototyping, clear readability for academic peer review, and easy integration with testing frameworks.
- First-class NumPy support for vectorised array operations — essential for performant manipulation of multi-million-sample audio arrays.

### Tkinter (GUI)

Tkinter is specified in the system specification table (Chapter 3, Table 3.1) as the GUI toolkit. It was chosen because:
- It ships with the standard Python distribution on Windows and macOS, requiring zero additional installation for the most common user platforms.
- It is mature, stable, and well-documented.
- It requires no external rendering engine, keeping the dependency footprint minimal.
- The application's functional requirements (file browsing, text input, metrics display) are straightforward enough that Tkinter's widget set is fully sufficient.

### PyCryptodome

The system specification (Chapter 3, Table 3.1) explicitly names PyCryptodome as the cryptographic library. It provides:
- A pure-Python (with optional C extension) implementation of AES-256 in CBC mode, matching the algorithm specified in Section 3.3.2.
- PKCS7 padding/unpadding utilities that allow the system to use the padding validation step as an implicit message authentication mechanism (wrong passphrase --> padding error --> `AuthenticationError`).
- Active maintenance and a security-focused development policy.

### NumPy

NumPy is specified in the system specification (Chapter 3, Table 3.1) for metric computation. Additional uses in this implementation include:
- Vectorised LSB clearing and setting across hundreds of thousands of samples in microseconds (replacing slow Python loops).
- `np.unpackbits` / `np.packbits` for efficient byte-to-bit and bit-to-byte conversion.
- Type-safe `int16` array operations that prevent silent integer overflow during sample manipulation.

### Standard Library (`wave`, `hashlib`, `random`, `struct`)

- **`wave`**: The only built-in Python module for reading and writing WAV (PCM) files without lossy re-encoding, directly matching the lossless cover medium requirement (Chapter 1, Section 1.5).
- **`hashlib`**: Provides `pbkdf2_hmac` — a constant-time, battle-tested PBKDF2-HMAC-SHA256 implementation, as specified in Section 3.3.2.
- **`random.Random`**: Used for the PRSG because it is seeded with a deterministic integer derived from the passphrase, producing a reproducible scatter pattern on both embedding and extraction sides.
- **`struct`**: Used for big-endian `uint32` packing of `PAYLOAD_LENGTH` in the header, ensuring cross-platform byte-order consistency.

---

## 8. Performance Targets

| Metric | Target | Achieved (1-bit LSB, 44.1 kHz mono) |
|---|---|---|
| SNR | >= 30 dB | Typically 40-60 dB |
| PSNR | Higher is better | Typically 80-90 dB |
| BER (error-free channel) | 0 | 0 (perfect round-trip) |
| Max capacity (10% safety) | ~5.5 KB / 60-second WAV | Verified by unit tests |

---

## 9. Project Structure

```
Audio-Stego/
├── main.py                  # Application entry point
├── requirements.txt         # Third-party dependencies
├── README.md
│
├── src/                     # Processing Core + Data Management layers
│   ├── __init__.py
│   ├── crypto.py            # AES-256-CBC, PBKDF2-HMAC-SHA256, header structure
│   ├── prsg.py              # Pseudo-Random Sample Index Generator
│   ├── metrics.py           # SNR, PSNR, MSE computation
│   ├── file_io.py           # WAV file I/O, capacity utilities
│   ├── embedding.py         # Algorithm EA -- LSB embedding engine
│   ├── extraction.py        # Algorithm XA -- LSB extraction engine
│   └── workflow.py          # Application Logic Layer (orchestration + validation)
│
├── gui/                     # Presentation Layer
│   ├── __init__.py
│   └── app.py               # Tkinter GUI (Embed tab, Extract tab, metrics panel)
│
└── tests/                   # Unit test suite
    ├── __init__.py
    ├── test_crypto.py
    ├── test_metrics.py
    ├── test_embedding.py
    └── test_extraction.py
```

---

## References

- Bender, W., Gruhl, D., Morimoto, N., & Lu, A. (1996). Techniques for data hiding. *IBM Systems Journal*, 35(3&4), 313-336.
- Cvejic, N., & Seppanen, T. (2004). Increasing the capacity of LSB-based audio steganography. *IEEE Workshop on Multimedia Signal Processing*.
- Muhammad, K., Ahmad, J., & Farman, H. (2015). An enhanced audio steganography scheme using pseudo-random LSB embedding. *KSII Transactions on Internet and Information Systems*, 9(5).
- Fridrich, J. (2010). *Steganography in digital media*. Cambridge University Press.
- PyCryptodome documentation: https://pycryptodome.readthedocs.io/
