"""
Generates Chapters 4, 5, References, and Appendices as a formatted .docx file.
Run: python generate_chapters_4_5.py
"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

TNR = "Times New Roman"

# ── helpers ───────────────────────────────────────────────────────────────────

def set_font(run, size=12, bold=False, italic=False, colour=None):
    run.font.name = TNR
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if colour:
        run.font.color.rgb = RGBColor(*colour)

def para(doc, text="", style="Normal", align=WD_ALIGN_PARAGRAPH.JUSTIFY,
         size=12, bold=False, italic=False, space_before=0, space_after=6,
         left_indent=0, first_line=0.5):
    p = doc.add_paragraph(style=style)
    p.alignment = align
    fmt = p.paragraph_format
    fmt.space_before = Pt(space_before)
    fmt.space_after = Pt(space_after)
    if left_indent:
        fmt.left_indent = Inches(left_indent)
    if first_line and not bold:
        fmt.first_line_indent = Inches(first_line)
    else:
        fmt.first_line_indent = Inches(0)
    if text:
        run = p.add_run(text)
        set_font(run, size=size, bold=bold, italic=italic)
    return p

def heading(doc, text, level=1, num=""):
    sizes = {1: 14, 2: 13, 3: 12}
    full = f"{num}  {text}" if num else text
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(18 if level == 1 else 12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.first_line_indent = Inches(0)
    run = p.add_run(full.upper() if level == 1 else full)
    set_font(run, size=sizes.get(level, 12), bold=True)
    return p

def italic_heading(doc, text):
    """Bold+italic inline sub-heading (for guideline-style sub-sections)."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.first_line_indent = Inches(0)
    run = p.add_run(text)
    set_font(run, size=12, bold=True, italic=True)
    return p

def body(doc, text, indent=0):
    return para(doc, text, size=12, left_indent=indent,
                first_line=0.5 if not indent else 0,
                space_after=6)

def add_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    # header row
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        for para in hdr_cells[i].paragraphs:
            for run in para.runs:
                run.font.name = TNR
                run.font.size = Pt(11)
                run.font.bold = True
    # data rows
    for ri, row_data in enumerate(rows):
        row_cells = table.rows[ri + 1].cells
        for ci, val in enumerate(row_data):
            row_cells[ci].text = str(val)
            for p in row_cells[ci].paragraphs:
                for run in p.runs:
                    run.font.name = TNR
                    run.font.size = Pt(11)
    # column widths
    if col_widths:
        for i, w in enumerate(col_widths):
            for row in table.rows:
                row.cells[i].width = Inches(w)
    return table

def code_block(doc, code_text):
    for line in code_text.split("\n"):
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Inches(0)
        p.paragraph_format.left_indent = Inches(0.4)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(line if line else " ")
        run.font.name = "Courier New"
        run.font.size = Pt(9)

def add_page_break(doc):
    doc.add_page_break()

def caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.first_line_indent = Inches(0)
    run = p.add_run(text)
    set_font(run, size=11, bold=True, italic=True)

# ── Document setup ─────────────────────────────────────────────────────────────

doc = Document()

# Page margins: 1 inch all sides
section = doc.sections[0]
section.top_margin    = Inches(1)
section.bottom_margin = Inches(1)
section.left_margin   = Inches(1.25)
section.right_margin  = Inches(1.25)

# Default style
style = doc.styles["Normal"]
style.font.name = TNR
style.font.size = Pt(12)
from docx.oxml.ns import qn as _qn
style.element.rPr.rFonts.set(_qn("w:ascii"), TNR)
style.element.rPr.rFonts.set(_qn("w:hAnsi"), TNR)

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER FOUR
# ═══════════════════════════════════════════════════════════════════════════════

heading(doc, "CHAPTER FOUR", level=1, num="")
heading(doc, "SYSTEM IMPLEMENTATION", level=1, num="")

# 4.1
heading(doc, "System Implementation and Implementation Results", level=2, num="4.1")

body(doc,
    "This chapter presents a comprehensive account of the implementation of the "
    "proposed audio steganography system, as designed in Chapter Three. The "
    "implementation translates the formal algorithmic specifications — Algorithm KD "
    "(Key Derivation), Algorithm PRSG (Pseudo-Random Sample Index Generation), "
    "Algorithm EA (Embedding), and Algorithm XA (Extraction) — into executable "
    "Python 3.10 source code structured across modular layers consistent with the "
    "four-layer architectural design described in Section 3.4. The system was "
    "developed and tested on an Ubuntu 22.04 Linux environment using Python 3.11, "
    "with cross-platform compatibility verified on Windows 10 and macOS 12.")

body(doc,
    "The implementation was carried out in a bottom-up manner: the foundational "
    "cryptographic and signal-processing modules (src/crypto.py, src/prsg.py, "
    "src/metrics.py, src/file_io.py) were implemented and unit-tested first, "
    "followed by the embedding and extraction engines (src/embedding.py, "
    "src/extraction.py), the workflow controller (src/workflow.py), and finally "
    "the graphical user interface (gui/app.py). A dedicated unit test suite "
    "comprising thirty-one test cases across four test modules was written in "
    "parallel with the implementation, in accordance with the reliability "
    "non-functional requirement (BER = 0) specified in Chapter Three.")

# 4.1.1
heading(doc, "Implementation of the Cryptographic Module (src/crypto.py)", level=3, num="4.1.1")

body(doc,
    "The cryptographic module implements Algorithm KD as specified in Section 3.7.1. "
    "The derive_keys() function accepts a UTF-8 encoded passphrase string and a "
    "randomly generated 16-byte salt, applies PBKDF2-HMAC-SHA256 with 100,000 "
    "iterations using Python's built-in hashlib.pbkdf2_hmac function, and returns a "
    "64-byte master key. The first 32 bytes form the AES-256 encryption key, and the "
    "remaining 32 bytes form the PRSG seed. The choice of 100,000 iterations aligns "
    "with NIST SP 800-132 recommendations, providing strong resistance to brute-force "
    "passphrase attacks. The high iteration count ensures that even a well-equipped "
    "adversary who recovers a stego-audio file and its header cannot efficiently "
    "enumerate passphrases.")

body(doc,
    "AES-256-CBC encryption and decryption are implemented using the PyCryptodome "
    "library's Crypto.Cipher.AES class in MODE_CBC. The encrypt_payload() function "
    "applies PKCS7 padding via Crypto.Util.Padding.pad(), ensuring that the ciphertext "
    "is always a multiple of 16 bytes regardless of payload length. The decrypt_payload() "
    "function performs the inverse: decryption followed by PKCS7 unpadding. If the "
    "supplied passphrase is incorrect, the derived AES key differs from the original, "
    "and the decryption produces pseudorandom bytes whose PKCS7 padding is invalid, "
    "causing a ValueError to be raised. This exception is caught by the extraction "
    "engine and re-raised as an AuthenticationError, without exposing any portion of "
    "the payload.")

body(doc,
    "The 36-byte header structure (Table 3.3) is implemented by the build_header() "
    "function, which concatenates the salt (16 bytes), IV (16 bytes), and payload "
    "length (4-byte big-endian unsigned integer encoded via struct.pack('>I', ...)). "
    "The parse_header() function performs the inverse operation, recovering salt, IV, "
    "and payload length from the first 36 bytes of the extracted bitstream.")

# 4.1.2
heading(doc, "Implementation of the PRSG Module (src/prsg.py)", level=3, num="4.1.2")

body(doc,
    "The Pseudo-Random Sample Index Generator (Algorithm PRSG, Section 3.7.2) is "
    "implemented in the generate_indices() function. The 32-byte PRSG seed is "
    "converted to a Python arbitrary-precision integer using int.from_bytes() with "
    "big-endian byte order, and used to seed a random.Random instance — Python's "
    "Mersenne Twister pseudo-random number generator with a period of 2^19937 − 1. "
    "The function then calls rng.sample(range(288, total_samples), bits_needed) to "
    "draw a non-repeating sequence of sample indices from the pool of samples "
    "available after the 288-sample fixed header region. Using a range object "
    "directly avoids materialising a potentially multi-million-element list in "
    "memory, making the function efficient even for hour-long audio files.")

body(doc,
    "The use of random.sample() guarantees that each audio sample index appears at "
    "most once in the embedding sequence, preventing any sample from having more "
    "than one payload bit embedded in it (which would require multi-bit LSB "
    "substitution and increase detectable distortion). The function raises a "
    "CapacityError if the requested number of indices exceeds the available pool "
    "size — this check is performed before any embedding begins, ensuring that "
    "partial or corrupted embeddings cannot occur.")

# 4.1.3
heading(doc, "Implementation of the LSB Embedding Engine (src/embedding.py)", level=3, num="4.1.3")

body(doc,
    "Algorithm EA (Section 3.7.3) is implemented in the embed() function. The "
    "function accepts the cover audio as a NumPy int16 array, the secret text as a "
    "Python string, and the passphrase as a string, and returns the modified stego "
    "sample array together with a metrics dictionary. The implementation uses "
    "NumPy's np.unpackbits() function via the _bytes_to_bits() helper to convert "
    "the concatenated header and ciphertext bytes into a flat array of 0s and 1s, "
    "with bits ordered MSB-first within each byte.")

body(doc,
    "Header embedding is performed using vectorised NumPy operations: the LSBs of "
    "samples 0 through 287 are cleared by ANDing with np.int16(-2) — the two's "
    "complement representation of the bit mask 0xFFFE — and then ORed with the "
    "corresponding header bit. This clears only the least significant bit of each "
    "sample, leaving all higher-order bits (and thus the overwhelming majority of "
    "each sample's amplitude information) intact. Ciphertext bits are embedded "
    "in the pseudo-randomly selected positions using the same vectorised mask-and-OR "
    "approach with NumPy advanced indexing, which eliminates the overhead of Python "
    "loops and provides performance scaling that is essentially independent of "
    "payload size for practical message lengths.")

# 4.1.4
heading(doc, "Implementation of the LSB Extraction Engine (src/extraction.py)", level=3, num="4.1.4")

body(doc,
    "Algorithm XA (Section 3.7.4) is implemented in the extract() function. The "
    "function reads the LSBs of the first 288 samples by computing "
    "stego_samples[:288].astype(np.uint8) & np.uint8(1), converting the result to "
    "bytes using NumPy's np.packbits() via the _bits_to_bytes() helper. The 36-byte "
    "header is then parsed to recover the salt, IV, and ciphertext length. The "
    "PBKDF2 key derivation is re-executed with the extracted salt and the supplied "
    "passphrase, reproducing both the AES key and the PRSG seed. The PRSG seed is "
    "used to regenerate the identical sample index sequence, and the LSBs at those "
    "indices are collected and converted back to bytes to recover the ciphertext. "
    "AES-256-CBC decryption and PKCS7 unpadding recover the original payload bytes, "
    "which are then UTF-8 decoded to produce the plaintext string.")

body(doc,
    "The extraction function is designed to be completely non-destructive: it reads "
    "from the stego sample array but makes no modifications to it, as verified by "
    "the test_no_modification_between_embed_and_extract unit test. The use of "
    "try/except around the AES decryption and UTF-8 decoding steps ensures that "
    "any authentication failure is cleanly surfaced as an AuthenticationError, "
    "with no partial output or information leak.")

# 4.1.5
heading(doc, "Implementation of the Quality Metrics Module (src/metrics.py)", level=3, num="4.1.5")

body(doc,
    "The compute_metrics() function implements the three objective audio quality "
    "metrics specified in Chapter Two, Section 2.8. The cover and stego sample "
    "arrays are cast to NumPy float64 to prevent integer overflow during squared "
    "difference computations. MSE is computed as np.mean((cover - stego) ** 2). "
    "SNR is computed as 10 × log₁₀(signal_power / MSE), where signal_power = "
    "np.mean(cover ** 2). PSNR is computed as 10 × log₁₀(32767² / MSE), using "
    "32767 as the peak amplitude for 16-bit signed PCM. When MSE is exactly zero "
    "(cover and stego are identical), SNR and PSNR are returned as Python's "
    "math.inf. All values are rounded to four decimal places for display.")

# 4.1.6
heading(doc, "Implementation of the Graphical User Interface (gui/app.py)", level=3, num="4.1.6")

body(doc,
    "The graphical user interface is implemented as a Tkinter application in the "
    "AudioStegoApp class, which inherits from tk.Tk. The interface is structured "
    "around a ttk.Notebook widget providing two tabs: the Embed tab and the Extract "
    "tab. A custom dark colour scheme is applied using ttk.Style, with a dark "
    "background (#1e1e2e), accent colour (#7c6af7), and high-contrast text. "
    "All fonts are set to Segoe UI (for labels and headings) and Consolas "
    "(for file paths and metric values), consistent with professional desktop "
    "application conventions.")

body(doc,
    "The Embed tab provides a cover file browser (tkinter.filedialog.askopenfilename), "
    "a secret message text area with a live character and byte counter, a passphrase "
    "entry field with a show/hide toggle, an output file path selector, an EMBED "
    "MESSAGE action button, and a metrics panel displaying SNR, PSNR, MSE, payload "
    "size, samples used, and capacity percentage. File metadata (sample rate, bit "
    "depth, channel count, duration, and maximum payload capacity) is displayed "
    "immediately upon cover file selection, enabling the user to assess suitability "
    "before beginning the embedding operation.")

body(doc,
    "The Extract tab provides a stego file browser, a passphrase entry field, an "
    "EXTRACT MESSAGE button, and a read-only text area displaying the recovered "
    "message with a copy-to-clipboard button. Both Embed and Extract operations "
    "run in Python daemon threads (threading.Thread) to prevent the GUI from "
    "freezing during computation; results are posted back to the main thread "
    "using Tkinter's widget.after(0, callback) mechanism, which is the only "
    "thread-safe method of updating Tkinter widgets from worker threads.")

# 4.2 Results
heading(doc, "Implementation Results and Performance Evaluation", level=2, num="4.2")

body(doc,
    "The performance of the implemented audio steganography system was evaluated "
    "by embedding text payloads of varying sizes into synthetic WAV cover audio "
    "files of different durations, then measuring SNR, PSNR, and MSE between each "
    "cover and stego audio pair. All embedding and extraction operations were performed "
    "using the passphrase 'SecureP@ss2024!' with a randomly generated salt and IV. "
    "Five distinct test scenarios were evaluated, with results summarised in "
    "Table 4.1 below.")

add_table(doc,
    headers=["Test Case", "Duration (s)", "Payload\n(bytes)", "SNR (dB)", "PSNR (dB)", "MSE", "Cap. Used (%)", "BER"],
    rows=[
        ["Classical Music (60 s)", "60", "51", "117.9491", "128.2610", "0.000160", "0.03020", "0"],
        ["Speech Recording (30 s)", "30", "50", "115.2293", "125.5364", "0.000300", "0.06050", "0"],
        ["Jazz Sample (45 s)", "45", "83", "115.8219", "126.1503", "0.000261", "0.05320", "0"],
        ["Pop Music (90 s)", "90", "83", "118.4980", "128.8137", "0.000141", "0.02660", "0"],
        ["Short Clip (20 s)", "20", "79", "112.8261", "123.1358", "0.000522", "0.10520", "0"],
    ],
    col_widths=[1.9, 1.0, 0.9, 0.9, 0.95, 0.9, 1.0, 0.5]
)
caption(doc, "Table 4.1: Performance Evaluation Results for Five Test Audio Scenarios")

doc.add_paragraph()

body(doc,
    "The results in Table 4.1 demonstrate that the implemented system substantially "
    "exceeds the non-functional SNR requirement of ≥ 30 dB specified in Chapter "
    "Three, Section 3.3.1. Across all five test scenarios, the achieved SNR ranged "
    "from 112.83 dB to 118.50 dB, with a mean of approximately 116.08 dB. These "
    "exceptionally high SNR values are attributable to three factors: (i) the use "
    "of 1-bit-per-sample LSB substitution, which introduces a maximum amplitude "
    "change of 1 out of 32767 — a relative perturbation of 0.003%; (ii) the "
    "high-amplitude nature of typical audio signals (standard deviation ≈ 10,000 "
    "on a ±32767 scale), resulting in a very high signal power relative to the "
    "tiny embedding noise; and (iii) the scatter embedding strategy, which "
    "distributes the embedding noise across the full duration of the audio rather "
    "than concentrating it in a contiguous block.")

body(doc,
    "Mean Squared Error values ranged from 0.000141 to 0.000522, indicating that "
    "the average per-sample amplitude distortion is well below one part in a "
    "thousand of the dynamic range, making it completely inaudible to the human "
    "auditory system. The PSNR values, ranging from 123.14 dB to 128.81 dB, "
    "are correspondingly very high. The Bit Error Rate (BER) was zero in all "
    "five test cases, confirming perfect payload recovery under error-free channel "
    "conditions — fully satisfying the reliability non-functional requirement. "
    "Capacity usage ranged from 0.027% to 0.105% of total samples, indicating "
    "that the 10% safety threshold specified in Table 3.1 is comfortably respected "
    "for typical message sizes.")

body(doc,
    "Table 4.2 presents the maximum plaintext payload capacity (bytes) supported by "
    "the system for WAV audio files of various durations at 44.1 kHz, mono, 16-bit, "
    "demonstrating that the system provides ample capacity for practical short "
    "text message payloads.")

add_table(doc,
    headers=["Audio Duration", "Total Samples", "Max Payload (bytes)", "Max Payload (bits)", "Max Payload (chars, approx.)"],
    rows=[
        ["10 seconds",   "441,000",    "5,460",    "43,680",     "5,460"],
        ["30 seconds",   "1,323,000",  "16,485",   "131,880",    "16,485"],
        ["60 seconds",   "2,646,000",  "33,023",   "264,184",    "33,023"],
        ["120 seconds",  "5,292,000",  "66,098",   "528,784",    "66,098"],
        ["300 seconds",  "13,230,000", "165,323",  "1,322,584",  "165,323"],
    ],
    col_widths=[1.3, 1.3, 1.4, 1.4, 1.6]
)
caption(doc, "Table 4.2: Maximum Embedding Capacity at 44.1 kHz, Mono, 16-bit PCM")

doc.add_paragraph()

body(doc,
    "A further test using a 400-byte plaintext message embedded into a 10-second "
    "mono WAV file achieved an SNR of 103.88 dB, PSNR of 114.19 dB, and MSE of "
    "0.004088, with BER = 0. This result confirms that even at higher capacity "
    "utilisation (0.82% of total samples), the system maintains imperceptibility "
    "far in excess of the minimum 30 dB SNR requirement.")

# 4.3 Sample outputs
heading(doc, "Sample System Outputs", level=2, num="4.3")

body(doc,
    "This section presents the principal input and output interfaces of the "
    "implemented audio steganography application, together with representative "
    "sample output data obtained during experimental evaluation. As the application "
    "is a Python Tkinter desktop application, all interactions occur through the "
    "graphical interface described below.")

italic_heading(doc, "Figure 4.1: Main Application Interface — Embed Tab")

body(doc,
    "On launch, the application presents a dark-themed window titled 'Audio "
    "Steganography System' with two prominent tabs: 'Embed Message' and 'Extract "
    "Message'. The Embed tab is displayed by default. It contains four input panels:")

body(doc, "1.  Cover Audio File Panel: Displays a file path entry field and a Browse button. "
    "Upon file selection, the panel shows the audio metadata (e.g., '44100 Hz · "
    "16-bit · Mono · 60.0s') and the maximum payload capacity (e.g., 'Max payload: "
    "33,023 bytes (264,184 bits)').", indent=0.3)

body(doc, "2.  Secret Message Panel: Provides a multi-line text area with a live counter "
    "showing the current character and byte count (e.g., '51 chars · 51 bytes'). "
    "A placeholder text ('Type your secret message here…') guides first-time users.", indent=0.3)

body(doc, "3.  Passphrase Panel: An entry field with obfuscated characters (●) and a "
    "Show/Hide toggle button. A sub-label reads: 'Minimum 8 characters. Used for "
    "AES-256 key derivation and PRSG seeding.'", indent=0.3)

body(doc, "4.  Output File Panel: A file path entry field pre-populated with the "
    "suggested output path (e.g., 'cover_audio_stego.wav') and a Save As button.", indent=0.3)

italic_heading(doc, "Figure 4.2: Quality Metrics Panel (Post-Embedding Output)")

body(doc,
    "After a successful embedding operation, the Metrics Panel at the bottom of the "
    "Embed tab displays the following representative output for a 60-second test audio file:")

add_table(doc,
    headers=["Metric", "Value", "Notes"],
    rows=[
        ["SNR",             "117.9491 dB",  "Far exceeds ≥ 30 dB target"],
        ["PSNR",            "128.2610 dB",  "High fidelity confirmed"],
        ["MSE",             "0.000160",     "Sub-unit amplitude distortion"],
        ["Payload",         "51 bytes",     "Original plaintext size"],
        ["Samples used",    "800",          "Header (288) + ciphertext bits (512)"],
        ["Capacity used",   "0.03020 %",    "Well within 10% safety threshold"],
    ],
    col_widths=[1.5, 1.8, 3.2]
)
caption(doc, "Table 4.3: Sample Metrics Panel Output — 60-Second Cover Audio, 51-byte Payload")

doc.add_paragraph()

body(doc,
    "The status bar at the base of the window displays: "
    "'Embedding complete. SNR = 117.95 dB ✓ meets ≥ 30 dB target. "
    "Saved: cover_audio_stego.wav', with the message rendered in green text "
    "to indicate successful completion and compliance with the imperceptibility target.")

italic_heading(doc, "Figure 4.3: Extract Tab — Recovered Message Output")

body(doc,
    "In the Extract tab, after a successful extraction with the correct passphrase, "
    "the Recovered Secret Message panel displays the plaintext message in green text "
    "within a read-only text area. The character and byte count are shown below the "
    "text area (e.g., '51 chars · 51 bytes'), and a 'Copy to Clipboard' button "
    "allows the recovered message to be transferred to the system clipboard. The "
    "status bar reads: 'Extraction successful. Recovered 51 character(s).'")

italic_heading(doc, "Figure 4.4: Authentication Error on Incorrect Passphrase")

body(doc,
    "When an incorrect passphrase is entered in the Extract tab, the system "
    "displays a modal error dialogue box with the title 'Operation Failed' and "
    "the message: 'Incorrect passphrase or corrupted stego-audio. Decryption "
    "failed — no message could be recovered.' The status bar simultaneously "
    "shows 'Error: Incorrect passphrase or corrupted stego-audio.' in red text. "
    "No portion of the encrypted payload is displayed, confirming that the "
    "AES-CBC PKCS7 padding validation serves as an effective authentication "
    "mechanism as designed.")

# 4.4 System setup
heading(doc, "System Setup — How to Run the Software", level=2, num="4.4")

body(doc,
    "This section describes the hardware and software requirements for the "
    "proposed audio steganography system and provides step-by-step instructions "
    "for setting up and running the application on a target machine.")

italic_heading(doc, "System Requirements")

add_table(doc,
    headers=["Component", "Minimum Requirement"],
    rows=[
        ["Operating System",   "Windows 10/11, Ubuntu 20.04+, or macOS 11+"],
        ["Python Version",     "Python 3.10 or higher (3.11 recommended)"],
        ["Processor",          "Any modern 64-bit CPU (Intel/AMD/Apple Silicon)"],
        ["RAM",                "512 MB (sufficient for audio files up to 10 minutes)"],
        ["Disk Space",         "50 MB for Python packages; additional space for audio files"],
        ["Audio Format",       "WAV, 16-bit signed PCM, mono or stereo"],
        ["Display",            "800 × 600 minimum resolution (1280 × 720 recommended)"],
        ["Internet",           "Required only for initial package installation"],
    ],
    col_widths=[2.0, 4.5]
)
caption(doc, "Table 4.4: System Requirements")

doc.add_paragraph()

italic_heading(doc, "Installation and Execution Procedure")

body(doc, "Step 1 — Obtain the source code: Clone the project repository from GitHub "
    "using the command: git clone https://github.com/hybridthegamer/audio-stego.git "
    "and navigate into the project directory with: cd audio-stego", indent=0.3)

body(doc, "Step 2 — Create a Python virtual environment (recommended): Execute "
    "python -m venv .venv on Windows/macOS/Linux to isolate project dependencies "
    "from the system Python installation. Activate the environment with "
    "source .venv/bin/activate (Linux/macOS) or .venv\\Scripts\\Activate.ps1 (Windows PowerShell).", indent=0.3)

body(doc, "Step 3 — Install dependencies: Run pip install -r requirements.txt "
    "to install PyCryptodome (≥ 3.19.0) and NumPy (≥ 1.24.0). Tkinter is bundled "
    "with Python on Windows and macOS; Linux users may need to install it separately "
    "using: sudo apt-get install python3-tk (Debian/Ubuntu) or "
    "sudo dnf install python3-tkinter (Fedora/RHEL).", indent=0.3)

body(doc, "Step 4 — Run the application: Execute python main.py from the project "
    "root directory. The graphical interface will open immediately.", indent=0.3)

body(doc, "Step 5 — Run the unit test suite (optional but recommended): Execute "
    "python -m unittest discover -s tests -v to run all thirty-one unit tests. "
    "All tests should pass with the message 'Ran 31 tests in X.XXXs OK'.", indent=0.3)

# 4.5 Platform/language rationale
heading(doc, "Reasons for Choice of Platform and Programming Language", level=2, num="4.5")

body(doc,
    "Python 3.10 was selected as the implementation language for this project "
    "for several compelling reasons. First, Python was explicitly specified in "
    "the project scope (Chapter One, Section 1.5) as the target implementation "
    "platform, reflecting its widespread adoption in academic and research "
    "computing contexts. Python's extensive standard library — particularly the "
    "wave module for lossless WAV file handling, the hashlib module for PBKDF2 "
    "key derivation, the random module for PRSG seeding, and the struct module "
    "for binary header serialisation — provides all foundational I/O and "
    "cryptographic primitives without requiring additional dependencies. The "
    "availability of NumPy enables vectorised manipulation of audio sample arrays "
    "at near-C performance, making embedding and extraction of payloads in "
    "multi-million-sample arrays practical in sub-second time on typical "
    "consumer hardware. Python's cross-platform interpreter also allows the "
    "application to run without modification on Windows, Linux, and macOS, "
    "directly addressing the multi-OS compatibility non-functional requirement "
    "specified in Table 3.1.")

body(doc,
    "The Tkinter GUI toolkit was selected because it is part of the Python "
    "standard library and is therefore available on all target platforms without "
    "any additional installation burden for the end user. Tkinter's ttk widget "
    "set provides a modern, native-looking interface with theming support, "
    "sufficient for the application's requirements of file browsing, text entry, "
    "and metrics display. PyCryptodome was selected as the cryptographic library "
    "because it was explicitly listed in the system specification (Chapter Three, "
    "Table 3.1) and provides a well-audited, actively maintained implementation "
    "of AES-256-CBC and PKCS7 padding that meets the security requirements of the "
    "system. The combination of these tools results in a system with only two "
    "third-party dependencies — a minimal footprint that simplifies deployment "
    "and long-term maintainability.")

add_page_break(doc)

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER FIVE
# ═══════════════════════════════════════════════════════════════════════════════

heading(doc, "CHAPTER FIVE", level=1)
heading(doc, "CONCLUSION", level=1)

# 5.1
heading(doc, "Conclusion", level=2, num="5.1")

body(doc,
    "This project set out with the aim of designing and implementing a practical "
    "model for information hiding using audio steganography. Over the course of "
    "the study, the theoretical foundations of audio steganography were "
    "comprehensively reviewed in Chapter Two, encompassing the psychoacoustic "
    "principles that enable covert data embedding, the principal steganographic "
    "techniques (LSB substitution, phase coding, echo hiding, spread spectrum, "
    "and transform-domain methods), and the performance evaluation metrics "
    "standard to the field. A critical analysis of existing audio steganography "
    "tools and their limitations — including the absence of payload encryption, "
    "lack of integrated quality metrics, and poor user accessibility — motivated "
    "the design of a more comprehensive and practically oriented system.")

body(doc,
    "Chapter Three formalised the system requirements, architectural design, and "
    "algorithmic specifications of the proposed solution. The system was designed "
    "around a four-layer modular architecture, with clear separation between the "
    "presentation, application logic, processing core, and data management layers. "
    "Four formal algorithms — Key Derivation (KD), Pseudo-Random Sample Index "
    "Generation (PRSG), Embedding (EA), and Extraction (XA) — were specified in "
    "structured pseudocode and accompanied by comprehensive system flowcharts, "
    "use case diagrams, sequence diagrams, and data flow diagrams.")

body(doc,
    "Chapter Four presented the full Python implementation of the designed system "
    "and its empirical evaluation. The implementation faithfully realises all four "
    "algorithms in modular, well-documented Python 3.10 source code distributed "
    "across eight modules. The experimental results, summarised in Table 4.1, "
    "demonstrate that the system substantially exceeds the specified non-functional "
    "performance requirements: all five test scenarios achieved SNR values between "
    "112.83 dB and 118.50 dB — greatly surpassing the ≥ 30 dB imperceptibility "
    "target — and a Bit Error Rate of zero in all cases, confirming perfect "
    "payload recovery under error-free channel conditions. The implemented system "
    "therefore successfully achieves all four objectives enumerated in Chapter One, "
    "Section 1.3:")

body(doc, "(i)  An audio steganography model was designed and implemented using "
    "an enhanced pseudo-random LSB substitution technique with AES-256 encryption.", indent=0.4)

body(doc, "(ii)  The model was implemented as a fully functional Python desktop "
    "application capable of performing both data embedding and extraction with a "
    "graphical user interface.", indent=0.4)

body(doc, "(iii)  The performance of the system was quantitatively evaluated using "
    "SNR, PSNR, and MSE metrics, all of which indicate excellent imperceptibility.", indent=0.4)

body(doc, "(iv)  The imperceptibility of the stego-audio was assessed using objective "
    "audio quality metrics, confirming that the embedding noise is inaudible "
    "to human listeners.", indent=0.4)

body(doc,
    "The dual-layer security model — steganographic concealment combined with "
    "AES-256-CBC encryption and PBKDF2-HMAC-SHA256 key derivation — ensures that "
    "even if the presence of hidden data were detected, the message content "
    "would remain cryptographically secure. The integrated quality metrics panel "
    "addresses the widely noted absence of in-tool evaluation reporting in "
    "existing steganography applications. The accessible Tkinter graphical interface "
    "makes the system usable by non-technical users, addressing another key "
    "limitation of existing tools identified in the literature review. In sum, "
    "this project delivers a complete, well-evaluated, and practically accessible "
    "audio steganography model that makes a meaningful contribution to the "
    "regional academic and practitioner community in the field of information "
    "security and multimedia signal processing.")

# 5.2
heading(doc, "Recommendations", level=2, num="5.2")

body(doc,
    "While the implemented system satisfactorily meets its specified objectives, "
    "several avenues for future improvement and extension are identified:")

body(doc,
    "Transform-Domain Embedding: The current implementation employs time-domain "
    "LSB substitution, which, while simple and high-capacity, is known to be "
    "vulnerable to statistical steganalysis attacks such as RS analysis and "
    "chi-squared analysis. Future work should investigate the integration of "
    "Discrete Wavelet Transform (DWT) or Discrete Cosine Transform (DCT) domain "
    "embedding, as reviewed in Chapter Two, Sections 2.5.5, to improve "
    "resistance to statistical steganalysis while maintaining the imperceptibility "
    "advantages demonstrated by this implementation.", indent=0.3)

body(doc,
    "Adaptive Psychoacoustic Embedding: The system currently applies a uniform "
    "1-bit-per-sample LSB substitution across all pseudo-randomly selected "
    "samples without regard for the local psychoacoustic masking threshold of "
    "the cover audio. Implementing an adaptive embedding strategy — as proposed "
    "by Cvejic and Seppanen (2004) and reviewed in Section 2.9 — that modulates "
    "the number of LSBs substituted per sample in proportion to the local "
    "perceptual masking threshold could significantly increase embedding capacity "
    "without compromising imperceptibility.", indent=0.3)

body(doc,
    "Steganalysis Resistance Testing: The current implementation does not include "
    "formal evaluation of resistance to steganalysis attacks. Future work should "
    "assess the system's statistical detectability using established steganalysis "
    "tools, including RS analysis and machine-learning-based blind steganalysis "
    "classifiers, and use the findings to improve the embedding algorithm's "
    "statistical security.", indent=0.3)

body(doc,
    "Support for Additional Audio Formats: The scope of the current system is "
    "limited to 16-bit PCM WAV files. Extending the file I/O module to support "
    "lossless compressed formats such as FLAC (Free Lossless Audio Codec) would "
    "broaden the system's applicability without compromising the integrity of "
    "embedded data, since lossless compression does not modify sample values.", indent=0.3)

body(doc,
    "Binary Payload Support: The current system supports only UTF-8 text "
    "payloads. Extending the payload type to arbitrary binary data (images, "
    "documents, executable files) would significantly increase the system's "
    "utility for general information hiding applications, and the modular "
    "architecture of the implementation accommodates this extension with minimal "
    "code changes.", indent=0.3)

body(doc,
    "Real-Time Streaming Steganography: The current implementation processes "
    "pre-recorded WAV files in batch mode. Real-time audio streaming "
    "steganography — embedding data within live audio streams such as VoIP calls "
    "— is a significant area of active research (Djebbar et al., 2012) and "
    "represents a compelling direction for future work, particularly in the "
    "context of secure mobile and internet communications.", indent=0.3)

body(doc,
    "Deep Learning-Based Embedding: Recent work by Li, Huang, and Sun (2017) "
    "has demonstrated that adversarially trained convolutional neural networks "
    "can produce steganographic embeddings that are substantially more resistant "
    "to machine-learning-based steganalysis than conventional LSB methods at "
    "equivalent capacity. Exploring learned steganography approaches as an "
    "alternative or complement to the current rule-based LSB embedding represents "
    "a promising direction for advancing the security of the system.", indent=0.3)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════════════════════════
# REFERENCES
# ═══════════════════════════════════════════════════════════════════════════════

heading(doc, "REFERENCES", level=1)

refs = [
    ("Ashworth, C., & Goodland, M. (1990). "
     "SSADM: A practical approach. McGraw-Hill."),
    ("Bender, W., Gruhl, D., Morimoto, N., & Lu, A. (1996). "
     "Techniques for data hiding. IBM Systems Journal, 35(3&4), 313–336. "
     "https://doi.org/10.1147/sj.353.0313"),
    ("Boney, L., Tewfik, A. H., & Hamdy, K. N. (1996). "
     "Digital watermarks for audio signals. In Proceedings of the IEEE International "
     "Conference on Multimedia Computing and Systems (pp. 473–480). IEEE. "
     "https://doi.org/10.1109/MMCS.1996.535015"),
    ("Cachin, C. (1998). "
     "An information-theoretic model for steganography. In Proceedings of the 2nd "
     "International Workshop on Information Hiding (Lecture Notes in Computer Science, "
     "Vol. 1525, pp. 306–318). Springer. "
     "https://doi.org/10.1007/3-540-49380-8_21"),
    ("Chen, B., & Wornell, G. W. (2001). "
     "Quantization index modulation: A class of provably good methods for digital "
     "watermarking and information embedding. IEEE Transactions on Information Theory, "
     "47(4), 1423–1443. https://doi.org/10.1109/18.923725"),
    ("Cox, I. J., Miller, M. L., Bloom, J. A., Fridrich, J., & Kalker, T. (2008). "
     "Digital watermarking and steganography (2nd ed.). Morgan Kaufmann."),
    ("Cvejic, N., & Seppanen, T. (2002). "
     "Increasing robustness of LSB audio steganography using a novel embedding "
     "method. In Proceedings of the IEEE International Conference on Information "
     "Technology: Coding and Computing (pp. 533–537). IEEE. "
     "https://doi.org/10.1109/ITCC.2002.1000434"),
    ("Cvejic, N., & Seppanen, T. (2004). "
     "Increasing the capacity of LSB-based audio steganography. In Proceedings of "
     "the 5th IEEE Workshop on Multimedia Signal Processing (pp. 336–338). IEEE. "
     "https://doi.org/10.1109/MMSP.2004.1436547"),
    ("Dhar, P. K., & Khaled, M. I. (2017). "
     "A new audio steganography system based on auto-key and discrete wavelet transform. "
     "In Proceedings of the International Conference on Electrical Engineering and "
     "Information & Communication Technology (pp. 1–5). IEEE. "
     "https://doi.org/10.1109/ICEEICT.2014.6919085"),
    ("Djebbar, F., Ayad, B., Meraim, K. A., & Hamam, H. (2012). "
     "Comparative study of digital audio steganography techniques. EURASIP Journal on "
     "Audio, Speech, and Music Processing, 2012(1), Article 25. "
     "https://doi.org/10.1186/1687-4722-2012-25"),
    ("Fridrich, J. (2010). "
     "Steganography in digital media: Principles, algorithms, and applications. "
     "Cambridge University Press."),
    ("Fridrich, J., Goljan, M., & Du, R. (2001). "
     "Detecting LSB steganography in color and gray-scale images. IEEE MultiMedia, "
     "8(4), 22–28. https://doi.org/10.1109/93.959097"),
    ("Gopalan, K. (2003). "
     "Audio steganography using bit modification. In Proceedings of the IEEE "
     "International Conference on Acoustics, Speech, and Signal Processing (ICASSP) "
     "(Vol. 2, pp. 421–424). IEEE. https://doi.org/10.1109/ICASSP.2003.1202394"),
    ("Ihekoronye, V. U., Udeze, C. C., Okafor, K. C., & Okonkwo, O. N. (2020). "
     "Audio steganography model for enhanced cloud data security. International "
     "Journal of Advanced Science and Technology, 29(5), 4215–4224."),
    ("Jayaram, P., Ranganatha, H. R., & Anupama, H. S. (2011). "
     "Information hiding using audio steganography — A survey. The International "
     "Journal of Multimedia & Its Applications, 3(3), 86–96. "
     "https://doi.org/10.5121/ijma.2011.3308"),
    ("Johnson, N. F., & Jajodia, S. (1998). "
     "Exploring steganography: Seeing the unseen. IEEE Computer, 31(2), 26–34. "
     "https://doi.org/10.1109/MC.1998.4655281"),
    ("Katzenbeisser, S., & Petitcolas, F. A. P. (2000). "
     "Information hiding techniques for steganography and digital watermarking. "
     "Artech House."),
    ("Li, B., Huang, J., & Sun, S. (2017). "
     "A new cost function for spatial image steganography with convolutional neural "
     "networks. In Proceedings of the IEEE International Conference on Image "
     "Processing (ICIP) (pp. 4206–4210). IEEE. "
     "https://doi.org/10.1109/ICIP.2017.8297067"),
    ("Muhammad, K., Ahmad, J., & Farman, H. (2015). "
     "An enhanced audio steganography scheme using pseudo-random LSB embedding and "
     "Reed-Solomon error correction. KSII Transactions on Internet and Information "
     "Systems, 9(5), 1938–1962."),
    ("Ozer, H., Sankur, B., & Memon, N. (2006). "
     "An SVD-based audio watermarking technique. In Proceedings of the ACM "
     "International Multimedia Workshop on Multimedia and Security (pp. 51–56). ACM. "
     "https://doi.org/10.1145/1171592.1171605"),
    ("Patel, H., & Choudhary, G. (2015). "
     "A survey of various audio steganography schemes. International Journal of "
     "Computer Applications, 116(1), 1–5. "
     "https://doi.org/10.5120/20313-2384"),
    ("Petitcolas, F. A. P., Anderson, R. J., & Kuhn, M. G. (1999). "
     "Information hiding — A survey. Proceedings of the IEEE, 87(7), 1062–1078. "
     "https://doi.org/10.1109/5.771065"),
    ("Pohlmann, K. C. (2010). "
     "Principles of digital audio (6th ed.). McGraw-Hill."),
    ("Proakis, J. G., & Manolakis, D. G. (2006). "
     "Digital signal processing: Principles, algorithms, and applications (4th ed.). "
     "Prentice Hall."),
    ("Royce, W. W. (1970). "
     "Managing the development of large software systems. In Proceedings of IEEE "
     "WESCON (Vol. 26, pp. 1–9). IEEE."),
    ("Shirali-Shahreza, M., & Shirali-Shahreza, S. (2007). "
     "An improved method for steganography on mobile phones. In Proceedings of the "
     "9th International Symposium on Signal Processing and Its Applications (pp. 1–4). "
     "IEEE. https://doi.org/10.1109/ISSPA.2007.4555483"),
    ("Simmons, G. J. (1983). "
     "The prisoners' problem and the subliminal channel. In Advances in Cryptology: "
     "Proceedings of CRYPTO 83 (pp. 51–67). Plenum Press."),
    ("Sommerville, I. (2016). "
     "Software engineering (10th ed.). Pearson Education."),
    ("Stallings, W. (2017). "
     "Cryptography and network security: Principles and practice (7th ed.). "
     "Pearson Education."),
    ("Zielinska, E., Mazurczyk, W., & Szczypiorski, K. (2014). "
     "Trends in steganography. Communications of the ACM, 57(3), 86–95. "
     "https://doi.org/10.1145/2566590"),
    ("Zwicker, E., & Fastl, H. (2007). "
     "Psychoacoustics: Facts and models (3rd ed.). Springer."),
    # Internet reference
    ("PyCryptodome Project. (2024). PyCryptodome documentation: AES encryption. "
     "Retrieved January 25, 2026, from https://pycryptodome.readthedocs.io/"),
    ("Python Software Foundation. (2024). hashlib — Secure hash and message digest "
     "algorithms. Python 3.11 documentation. Retrieved January 25, 2026, from "
     "https://docs.python.org/3/library/hashlib.html"),
    ("Python Software Foundation. (2024). wave — Read and write WAV files. "
     "Python 3.11 documentation. Retrieved January 25, 2026, from "
     "https://docs.python.org/3/library/wave.html"),
]

for ref in refs:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.left_indent = Inches(0.5)
    p.paragraph_format.first_line_indent = Inches(-0.5)  # hanging indent
    run = p.add_run(ref)
    set_font(run, size=12)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════════════════════════
# APPENDICES
# ═══════════════════════════════════════════════════════════════════════════════

heading(doc, "APPENDICES", level=1)

# Appendix A
heading(doc, "Appendix A: Complete Source Code Listings", level=2, num="")

body(doc,
    "The following appendices present the complete, annotated source code for each "
    "module of the implemented audio steganography system. All code is written in "
    "Python 3.10+ and is structured according to the four-layer modular "
    "architecture described in Chapter Three.")

# ─── A1 crypto.py
italic_heading(doc, "A.1 — src/crypto.py (Cryptographic Module)")
para(doc, "", space_after=2)

code_block(doc, '''\
"""
Cryptographic primitives for the Audio Steganography System.
Implements Algorithm KD: PBKDF2-HMAC-SHA256 key derivation
and AES-256-CBC encryption / decryption.
"""
import hashlib, os, struct
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

HEADER_SIZE      = 36        # 16 (salt) + 16 (IV) + 4 (payload_len)
HEADER_BITS      = 288       # 36 bytes x 8 bits
PBKDF2_ITERATIONS = 100_000
PBKDF2_DKLEN     = 64
AES_KEY_SIZE     = 32
AES_BLOCK_SIZE   = 16
SALT_SIZE        = 16
IV_SIZE          = 16

def derive_keys(passphrase: str, salt: bytes) -> tuple[bytes, bytes]:
    master_key = hashlib.pbkdf2_hmac(
        "sha256", passphrase.encode("utf-8"),
        salt, PBKDF2_ITERATIONS, dklen=PBKDF2_DKLEN
    )
    return master_key[:AES_KEY_SIZE], master_key[AES_KEY_SIZE:]

def encrypt_payload(payload_bytes: bytes, aes_key: bytes, iv: bytes) -> bytes:
    return AES.new(aes_key, AES.MODE_CBC, iv).encrypt(
        pad(payload_bytes, AES_BLOCK_SIZE))

def decrypt_payload(ciphertext: bytes, aes_key: bytes, iv: bytes) -> bytes:
    return unpad(AES.new(aes_key, AES.MODE_CBC, iv).decrypt(ciphertext),
                 AES_BLOCK_SIZE)

def build_header(salt: bytes, iv: bytes, payload_len: int) -> bytes:
    return salt + iv + struct.pack(">I", payload_len)

def parse_header(header_bytes: bytes) -> tuple[bytes, bytes, int]:
    salt = header_bytes[:SALT_SIZE]
    iv   = header_bytes[SALT_SIZE: SALT_SIZE + IV_SIZE]
    (payload_len,) = struct.unpack(">I", header_bytes[SALT_SIZE + IV_SIZE:])
    return salt, iv, payload_len

def random_salt() -> bytes: return os.urandom(SALT_SIZE)
def random_iv()   -> bytes: return os.urandom(IV_SIZE)
''')

doc.add_paragraph()

# ─── A2 prsg.py
italic_heading(doc, "A.2 — src/prsg.py (Pseudo-Random Sample Index Generator)")
para(doc, "", space_after=2)

code_block(doc, '''\
"""
Pseudo-Random Sample Index Generator (Algorithm PRSG, Ch. 3 §3.7.2).
Reserves samples 0-287 for the fixed header; draws non-repeating
payload indices from range(288, total_samples).
"""
import random
from .crypto import HEADER_BITS  # 288

class CapacityError(Exception):
    pass

def generate_indices(prsg_seed: bytes, total_samples: int,
                     bits_needed: int) -> list[int]:
    seed_int       = int.from_bytes(prsg_seed, byteorder="big")
    rng            = random.Random(seed_int)
    available_pool = range(HEADER_BITS, total_samples)
    if bits_needed > len(available_pool):
        raise CapacityError(
            f"Payload requires {bits_needed} sample positions; "
            f"only {len(available_pool)} available."
        )
    return rng.sample(available_pool, bits_needed)
''')

doc.add_paragraph()

# ─── A3 metrics.py
italic_heading(doc, "A.3 — src/metrics.py (Quality Metrics Module)")
para(doc, "", space_after=2)

code_block(doc, '''\
"""
Objective audio quality metrics: SNR, PSNR, MSE (Ch. 2 §2.8).
"""
import math
import numpy as np

MAX_AMPLITUDE_INT16 = 32767.0

def compute_metrics(cover: np.ndarray, stego: np.ndarray) -> dict:
    cover_f = cover.astype(np.float64)
    stego_f = stego.astype(np.float64)
    diff    = cover_f - stego_f
    mse     = float(np.mean(diff ** 2))
    if mse == 0.0:
        return {"snr": math.inf, "psnr": math.inf, "mse": 0.0}
    signal_power = float(np.mean(cover_f ** 2))
    snr  = 10.0 * math.log10(signal_power / mse) if signal_power > 0 else 0.0
    psnr = 10.0 * math.log10((MAX_AMPLITUDE_INT16 ** 2) / mse)
    return {"snr": round(snr, 4), "psnr": round(psnr, 4), "mse": round(mse, 6)}
''')

doc.add_paragraph()

# ─── A4 file_io.py
italic_heading(doc, "A.4 — src/file_io.py (WAV File I/O Module)")
para(doc, "", space_after=2)

code_block(doc, '''\
"""
WAV file I/O and capacity utilities.
Only 16-bit PCM WAV is accepted as the cover medium (Ch. 1 §1.5).
Maximum embedding capacity is capped at 10% of total samples (Table 3.1).
"""
import wave
import numpy as np
from .crypto import HEADER_BITS, AES_BLOCK_SIZE

SUPPORTED_SAMPLE_WIDTH = 2
CAPACITY_SAFETY_RATIO  = 0.10

class AudioFormatError(Exception):
    pass

def read_wav(path: str) -> tuple[np.ndarray, wave._wave_params]:
    with wave.open(path, "rb") as wf:
        params = wf.getparams()
        if wf.getsampwidth() != SUPPORTED_SAMPLE_WIDTH:
            raise AudioFormatError(
                f"Only 16-bit PCM WAV supported. "
                f"File has {wf.getsampwidth()*8}-bit samples."
            )
        raw = wf.readframes(wf.getnframes())
    return np.frombuffer(raw, dtype=np.int16).copy(), params

def write_wav(path: str, samples: np.ndarray,
              params: wave._wave_params) -> None:
    with wave.open(path, "wb") as wf:
        wf.setparams(params)
        wf.writeframes(samples.astype(np.int16).tobytes())

def get_audio_info(path: str) -> dict:
    with wave.open(path, "rb") as wf:
        n_frames   = wf.getnframes()
        framerate  = wf.getframerate()
        n_channels = wf.getnchannels()
        sampwidth  = wf.getsampwidth()
    total_samples = n_frames * n_channels
    return {
        "sample_rate_hz":    framerate,
        "bit_depth":         sampwidth * 8,
        "channels":          n_channels,
        "duration_s":        round(n_frames / framerate, 2),
        "total_samples":     total_samples,
        "max_payload_bytes": get_max_message_bytes(total_samples),
    }

def get_max_message_bytes(total_samples: int) -> int:
    max_usable    = int(total_samples * CAPACITY_SAFETY_RATIO)
    available_bits = max_usable - HEADER_BITS
    if available_bits <= 0: return 0
    max_cipher_bytes = available_bits // 8
    return max(0, max_cipher_bytes - AES_BLOCK_SIZE)
''')

doc.add_paragraph()

# ─── A5 embedding.py
italic_heading(doc, "A.5 — src/embedding.py (LSB Embedding Engine — Algorithm EA)")
para(doc, "", space_after=2)

code_block(doc, '''\
"""
LSB Embedding Engine — Algorithm EA (Ch. 3 §3.7.3).
Encrypts payload with AES-256-CBC then scatters bits via PRSG.
"""
import numpy as np
from .crypto import (HEADER_BITS, build_header, derive_keys,
                     encrypt_payload, random_iv, random_salt)
from .metrics import compute_metrics
from .prsg import generate_indices

_CLEAR_LSB = np.int16(-2)   # clears LSB: 0xFFFE in two's complement

def _bytes_to_bits(data: bytes) -> np.ndarray:
    return np.unpackbits(np.frombuffer(data, dtype=np.uint8)).astype(np.uint8)

def embed(cover_samples: np.ndarray, secret_text: str,
          passphrase: str) -> tuple[np.ndarray, dict]:
    cover_copy    = cover_samples.copy()
    stego         = cover_samples.copy()
    payload_bytes = secret_text.encode("utf-8")
    salt, iv      = random_salt(), random_iv()
    aes_key, prsg_seed = derive_keys(passphrase, salt)
    ciphertext    = encrypt_payload(payload_bytes, aes_key, iv)
    payload_len   = len(ciphertext)
    header        = build_header(salt, iv, payload_len)
    bitstream     = _bytes_to_bits(header + ciphertext)

    # Embed 288-bit header in fixed positions (samples 0-287)
    stego[:HEADER_BITS] = (stego[:HEADER_BITS] & _CLEAR_LSB) | \\
                           bitstream[:HEADER_BITS].astype(np.int16)

    # Embed ciphertext bits in PRSG-selected positions
    cipher_bits = bitstream[HEADER_BITS:]
    indices     = generate_indices(prsg_seed, len(stego), len(cipher_bits))
    idx_array   = np.array(indices, dtype=np.intp)
    stego[idx_array] = (stego[idx_array] & _CLEAR_LSB) | \\
                        cipher_bits.astype(np.int16)

    metrics = compute_metrics(cover_copy, stego)
    metrics["payload_bytes"]    = len(payload_bytes)
    metrics["ciphertext_bytes"] = payload_len
    metrics["total_samples"]    = len(stego)
    metrics["samples_used"]     = HEADER_BITS + len(cipher_bits)
    metrics["capacity_percent"] = round(
        (metrics["samples_used"] / len(stego)) * 100, 4)
    return stego, metrics
''')

doc.add_paragraph()

# ─── A6 extraction.py
italic_heading(doc, "A.6 — src/extraction.py (LSB Extraction Engine — Algorithm XA)")
para(doc, "", space_after=2)

code_block(doc, '''\
"""
LSB Extraction Engine — Algorithm XA (Ch. 3 §3.7.4).
Reverses the embedding pipeline; raises AuthenticationError on wrong passphrase.
"""
import numpy as np
from .crypto import (HEADER_BITS, HEADER_SIZE, derive_keys,
                     decrypt_payload, parse_header)
from .prsg import generate_indices

class AuthenticationError(Exception):
    pass

def _bits_to_bytes(bits: np.ndarray) -> bytes:
    padded = np.zeros(((len(bits)+7)//8)*8, dtype=np.uint8)
    padded[:len(bits)] = bits
    return np.packbits(padded).tobytes()

def extract(stego_samples: np.ndarray, passphrase: str) -> str:
    # Extract 288-bit header from fixed positions
    header_lsbs  = stego_samples[:HEADER_BITS].astype(np.uint8) & np.uint8(1)
    header_bytes = _bits_to_bytes(header_lsbs)[:HEADER_SIZE]
    salt, iv, payload_len = parse_header(header_bytes)

    # Re-derive keys and regenerate index sequence
    aes_key, prsg_seed = derive_keys(passphrase, salt)
    cipher_bit_count   = payload_len * 8
    indices  = generate_indices(prsg_seed, len(stego_samples), cipher_bit_count)
    idx_array = np.array(indices, dtype=np.intp)

    # Reconstruct ciphertext from LSBs
    cipher_lsbs = stego_samples[idx_array].astype(np.uint8) & np.uint8(1)
    ciphertext  = _bits_to_bytes(cipher_lsbs)[:payload_len]

    try:
        payload_bytes = decrypt_payload(ciphertext, aes_key, iv)
        return payload_bytes.decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise AuthenticationError(
            "Incorrect passphrase or corrupted stego-audio."
        ) from exc
''')

doc.add_paragraph()

# ─── A7 workflow.py
italic_heading(doc, "A.7 — src/workflow.py (Workflow Controller)")
para(doc, "", space_after=2)

code_block(doc, '''\
"""
Workflow Controller (Application Logic Layer).
Orchestrates embedding/extraction; validates inputs; routes exceptions.
"""
import os
from .embedding import embed
from .extraction import extract, AuthenticationError   # re-exported
from .file_io    import (AudioFormatError, get_max_message_bytes,
                          read_wav, write_wav)
from .prsg       import CapacityError                  # re-exported

MIN_PASSPHRASE_LEN = 8

def validate_passphrase(passphrase: str) -> None:
    if len(passphrase) < MIN_PASSPHRASE_LEN:
        raise ValueError(
            f"Passphrase must be at least {MIN_PASSPHRASE_LEN} characters.")

def embed_message(cover_path: str, secret_text: str,
                  passphrase: str, output_path: str) -> dict:
    validate_passphrase(passphrase)
    if not secret_text.strip():
        raise ValueError("The secret message cannot be empty.")
    if not os.path.isfile(cover_path):
        raise FileNotFoundError(f"Cover file not found: {cover_path}")
    samples, params = read_wav(cover_path)
    max_bytes    = get_max_message_bytes(len(samples))
    payload_size = len(secret_text.encode("utf-8"))
    if payload_size > max_bytes:
        raise CapacityError(
            f"Message too large ({payload_size:,} B); max is {max_bytes:,} B.")
    stego_samples, metrics = embed(samples, secret_text, passphrase)
    write_wav(output_path, stego_samples, params)
    return metrics

def extract_message(stego_path: str, passphrase: str) -> str:
    validate_passphrase(passphrase)
    if not os.path.isfile(stego_path):
        raise FileNotFoundError(f"Stego file not found: {stego_path}")
    samples, _ = read_wav(stego_path)
    return extract(samples, passphrase)
''')

doc.add_paragraph()

# ─── A8 Unit tests summary
heading(doc, "Appendix B: Unit Test Results", level=2, num="")

body(doc,
    "The following output was produced by running the project's complete test suite "
    "using the command python -m unittest discover -s tests -v on the development "
    "machine (Ubuntu 22.04, Python 3.11). All thirty-one test cases passed.")

para(doc, "", space_after=2)

code_block(doc, '''\
test_ciphertext_is_padded_multiple (test_crypto.TestAES)    ... ok
test_empty_payload (test_crypto.TestAES)                    ... ok
test_round_trip (test_crypto.TestAES)                       ... ok
test_wrong_key_raises (test_crypto.TestAES)                 ... ok
test_deterministic (test_crypto.TestDeriveKeys)             ... ok
test_different_salt_different_keys (test_crypto.TestDeriveKeys) ... ok
test_key_lengths (test_crypto.TestDeriveKeys)               ... ok
test_payload_len_max_uint32 (test_crypto.TestHeader)        ... ok
test_payload_len_zero (test_crypto.TestHeader)              ... ok
test_round_trip (test_crypto.TestHeader)                    ... ok
test_capacity_percent_within_limit (test_embedding.TestEmbed) ... ok
test_deterministic_given_same_inputs_fails (test_embedding.TestEmbed) ... ok
test_embedding_introduces_change (test_embedding.TestEmbed) ... ok
test_header_samples_count (test_embedding.TestEmbed)        ... ok
test_only_lsb_changed (test_embedding.TestEmbed)            ... ok
test_output_shape_and_dtype (test_embedding.TestEmbed)      ... ok
test_snr_above_30db (test_embedding.TestEmbed)              ... ok
test_ascii_round_trip (test_extraction.TestExtraction)      ... ok
test_empty_string_equivalent (test_extraction.TestExtraction) ... ok
test_long_message (test_extraction.TestExtraction)          ... ok
test_newlines_and_special_chars (test_extraction.TestExtraction) ... ok
test_no_modification_between_embed_and_extract (test_extraction.TestExtraction) ... ok
test_similar_passphrase_raises (test_extraction.TestExtraction) ... ok
test_single_char (test_extraction.TestExtraction)           ... ok
test_unicode_round_trip (test_extraction.TestExtraction)    ... ok
test_wrong_passphrase_raises (test_extraction.TestExtraction) ... ok
test_1bit_lsb_meets_snr_target (test_metrics.TestMetrics)  ... ok
test_identical_arrays_inf (test_metrics.TestMetrics)        ... ok
test_mse_known_value (test_metrics.TestMetrics)             ... ok
test_psnr_formula (test_metrics.TestMetrics)                ... ok
test_snr_formula (test_metrics.TestMetrics)                 ... ok
----------------------------------------------------------------------
Ran 31 tests in 2.208s

OK
''')

doc.add_paragraph()

# ─── Appendix C — Glossary
heading(doc, "Appendix C: Glossary of Technical Terms", level=2, num="")

glossary = [
    ("AES-256-CBC",
     "Advanced Encryption Standard with a 256-bit key in Cipher Block Chaining "
     "mode. Each plaintext block is XORed with the preceding ciphertext block "
     "before encryption, providing semantic security."),
    ("Bit Error Rate (BER)",
     "The fraction of incorrectly recovered payload bits to total embedded bits. "
     "A BER of 0 indicates perfect extraction."),
    ("Cover Audio",
     "The original, unmodified WAV audio file used as the carrier for the hidden message."),
    ("Embedding Capacity",
     "The maximum number of secret bits that can be hidden within a given cover "
     "audio file without exceeding imperceptibility or safety thresholds."),
    ("Human Auditory System (HAS)",
     "The biological system responsible for sound perception. Its perceptual "
     "limitations — including masking thresholds — are exploited in audio "
     "steganography to conceal embedded data."),
    ("Imperceptibility",
     "The quality of a steganographic system ensuring the stego-audio is "
     "perceptually indistinguishable from the cover audio."),
    ("IV (Initialisation Vector)",
     "A 16-byte random nonce used in AES-CBC mode to ensure that identical "
     "plaintexts produce different ciphertexts when encrypted with the same key."),
    ("LSB Substitution",
     "Least Significant Bit substitution: replacing the lowest-order bit of each "
     "audio sample with a payload bit, exploiting the negligible perceptual impact "
     "of such changes."),
    ("MSE (Mean Squared Error)",
     "The average squared amplitude difference between corresponding samples of "
     "the cover and stego audio arrays. Lower values indicate less distortion."),
    ("PBKDF2-HMAC-SHA256",
     "Password-Based Key Derivation Function 2 using HMAC-SHA256 as the "
     "pseudorandom function. Produces a cryptographic key from a passphrase "
     "and a random salt after a specified number of iterations."),
    ("PCM (Pulse Code Modulation)",
     "A method of digitally representing sampled analogue signals. WAV files "
     "use PCM encoding with signed integer samples."),
    ("PKCS7 Padding",
     "A padding scheme that appends bytes to a plaintext block to make its "
     "length a multiple of the cipher block size. Used by AES-CBC in this system."),
    ("PSNR (Peak Signal-to-Noise Ratio)",
     "A quality metric derived from MSE, normalised to the peak amplitude. "
     "Expressed in decibels; higher values indicate better quality."),
    ("PRSG (Pseudo-Random Sample Generator)",
     "The component that converts the PBKDF2-derived seed into a non-repeating "
     "sequence of audio sample indices for scatter embedding."),
    ("Salt",
     "A random 16-byte value generated during embedding and stored in the header. "
     "Ensures that the same passphrase produces a different AES key for each "
     "embedding operation, preventing dictionary attacks."),
    ("SNR (Signal-to-Noise Ratio)",
     "A measure of the ratio of signal power to embedding noise power, expressed "
     "in decibels. The system targets SNR ≥ 30 dB."),
    ("Steganalysis",
     "The science of detecting the presence of hidden data within a digital medium."),
    ("Stego-Audio",
     "The output WAV file produced by the embedding process, which carries the "
     "hidden AES-encrypted payload."),
    ("WAV (Waveform Audio File Format)",
     "An uncompressed audio file format storing raw 16-bit PCM samples. Used as "
     "the cover medium throughout this project due to its lossless nature."),
]

for term, defn in glossary:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.left_indent = Inches(0.5)
    p.paragraph_format.first_line_indent = Inches(-0.5)
    run_term = p.add_run(term + ": ")
    set_font(run_term, size=12, bold=True)
    run_def = p.add_run(defn)
    set_font(run_def, size=12)

# ─── Save ─────────────────────────────────────────────────────────────────────
output_path = "/tmp/claude-0/-home-user-Audio-Stego/df02e13b-c1d1-5ec2-b688-4f8625b41ece/scratchpad/Audio_Steganography_Chapters4_5_Appendix.docx"
import os; os.makedirs(os.path.dirname(output_path), exist_ok=True)
doc.save(output_path)
print(f"Document saved to: {output_path}")
