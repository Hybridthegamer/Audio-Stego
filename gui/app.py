"""
Presentation Layer — Tkinter GUI for the Audio Steganography System.

Architecture: Presentation Layer (Ch. 3, §3.4.1).
Specification: Python 3.10+, tkinter (Ch. 3, Table 3.1).

GUI structure:
  ┌───────────────────────────────────────────────────────────┐
  │          Audio Steganography System — Title Bar           │
  ├──────────────────────┬────────────────────────────────────┤
  │      [Embed Tab]     │         [Extract Tab]              │
  │  Cover File          │  Stego File                        │
  │  Secret Message      │  Passphrase                        │
  │  Passphrase          │  [Extract] Button                  │
  │  Output File         │  Recovered Message                 │
  │  [Embed] Button      │                                    │
  │  Metrics Panel       │                                    │
  ├───────────────────────────────────────────────────────────┤
  │                   Status Bar                              │
  └───────────────────────────────────────────────────────────┘

Threading: Embedding / extraction run in daemon threads; GUI updates are
posted back to the main thread via widget.after(0, callback).
"""

import math
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import sys

# Add project root to path so 'src' and 'gui' are importable when run as a script
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.file_io import get_audio_info, AudioFormatError
from src.workflow import (
    AuthenticationError,
    CapacityError,
    embed_message,
    extract_message,
)

# ─── Colour palette ───────────────────────────────────────────────────────────
_DARK_BG = "#1e1e2e"
_PANEL_BG = "#2a2a3e"
_ACCENT = "#7c6af7"
_ACCENT_HOVER = "#9a8aff"
_TEXT = "#cdd6f4"
_TEXT_DIM = "#7f849c"
_ENTRY_BG = "#313244"
_GOOD = "#a6e3a1"
_WARN = "#f38ba8"
_INFO = "#89b4fa"
_BORDER = "#45475a"

# ─── Fonts ────────────────────────────────────────────────────────────────────
_FONT_HEADING = ("Segoe UI", 13, "bold")
_FONT_LABEL = ("Segoe UI", 10)
_FONT_MONO = ("Consolas", 10)
_FONT_STATUS = ("Segoe UI", 9)
_FONT_BTN = ("Segoe UI", 11, "bold")
_FONT_METRIC_VAL = ("Consolas", 13, "bold")
_FONT_METRIC_LBL = ("Segoe UI", 8)


class _PlaceholderText(tk.Text):
    """Text widget that displays placeholder text when empty."""

    def __init__(self, master, placeholder="", **kw):
        super().__init__(master, **kw)
        self._placeholder = placeholder
        self._ph_active = False
        self._normal_fg = kw.get("fg", _TEXT)
        self._show_placeholder()
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

    def _show_placeholder(self):
        if not self.get("1.0", "end-1c"):
            self.config(fg=_TEXT_DIM)
            self.insert("1.0", self._placeholder)
            self._ph_active = True

    def _on_focus_in(self, _):
        if self._ph_active:
            self.delete("1.0", tk.END)
            self.config(fg=self._normal_fg)
            self._ph_active = False

    def _on_focus_out(self, _):
        if not self.get("1.0", "end-1c"):
            self._show_placeholder()

    def get_real_text(self) -> str:
        """Return the actual text (empty string when placeholder is shown)."""
        if self._ph_active:
            return ""
        return self.get("1.0", "end-1c")


class AudioStegoApp(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.title("Audio Steganography System")
        self.geometry("820x700")
        self.minsize(760, 640)
        self.configure(bg=_DARK_BG)
        self.resizable(True, True)

        self._setup_style()
        self._build_ui()

    # ── Style ──────────────────────────────────────────────────────────────────

    def _setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(".", background=_DARK_BG, foreground=_TEXT, borderwidth=0)
        style.configure("TFrame", background=_DARK_BG)
        style.configure("TLabel", background=_DARK_BG, foreground=_TEXT,
                         font=_FONT_LABEL)
        style.configure("Dim.TLabel", background=_DARK_BG, foreground=_TEXT_DIM,
                         font=_FONT_STATUS)
        style.configure("Panel.TFrame", background=_PANEL_BG)
        style.configure("Panel.TLabel", background=_PANEL_BG, foreground=_TEXT,
                         font=_FONT_LABEL)
        style.configure("PanelDim.TLabel", background=_PANEL_BG, foreground=_TEXT_DIM,
                         font=_FONT_STATUS)
        style.configure("Heading.TLabel", background=_DARK_BG, foreground=_ACCENT,
                         font=_FONT_HEADING)
        style.configure("PanelHeading.TLabel", background=_PANEL_BG, foreground=_ACCENT,
                         font=("Segoe UI", 10, "bold"))

        # Notebook (tabs)
        style.configure("TNotebook", background=_DARK_BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=_PANEL_BG, foreground=_TEXT_DIM,
                         font=("Segoe UI", 10), padding=[16, 6])
        style.map("TNotebook.Tab",
                  background=[("selected", _ACCENT)],
                  foreground=[("selected", "#ffffff")])

        # Buttons
        style.configure("Accent.TButton",
                         background=_ACCENT, foreground="#ffffff",
                         font=_FONT_BTN, padding=[24, 10], borderwidth=0)
        style.map("Accent.TButton",
                  background=[("active", _ACCENT_HOVER), ("pressed", _ACCENT)])

        style.configure("Small.TButton",
                         background=_ENTRY_BG, foreground=_TEXT,
                         font=_FONT_STATUS, padding=[8, 4], borderwidth=0)
        style.map("Small.TButton",
                  background=[("active", _BORDER)])

        style.configure("Ghost.TButton",
                         background=_PANEL_BG, foreground=_INFO,
                         font=_FONT_STATUS, padding=[6, 3], borderwidth=0)
        style.map("Ghost.TButton",
                  background=[("active", _ENTRY_BG)])

        # Separator
        style.configure("TSeparator", background=_BORDER)

        # Entry
        style.configure("TEntry", fieldbackground=_ENTRY_BG, foreground=_TEXT,
                         insertcolor=_TEXT, borderwidth=1, relief="flat")

        # Scrollbar
        style.configure("TScrollbar", background=_PANEL_BG,
                         troughcolor=_DARK_BG, borderwidth=0, arrowsize=12)

    # ── UI Builder ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ─ App title
        hdr = tk.Frame(self, bg=_DARK_BG)
        hdr.pack(fill="x", padx=20, pady=(14, 4))
        tk.Label(hdr, text="🔐 Audio Steganography System",
                 font=("Segoe UI", 16, "bold"), fg=_ACCENT, bg=_DARK_BG
                 ).pack(side="left")
        tk.Label(hdr, text="LSB + AES-256 | Information Hiding via Audio",
                 font=_FONT_STATUS, fg=_TEXT_DIM, bg=_DARK_BG
                 ).pack(side="left", padx=(12, 0), pady=(4, 0))

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=(4, 0))

        # ─ Notebook (tabs)
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill="both", expand=True, padx=20, pady=10)

        self._build_embed_tab()
        self._build_extract_tab()

        # ─ Status bar
        self._status_var = tk.StringVar(value="Ready.")
        self._status_colour = tk.StringVar(value=_TEXT_DIM)
        status_bar = tk.Frame(self, bg=_PANEL_BG, height=28)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)
        self._status_lbl = tk.Label(
            status_bar, textvariable=self._status_var,
            font=_FONT_STATUS, fg=_TEXT_DIM, bg=_PANEL_BG, anchor="w", padx=14
        )
        self._status_lbl.pack(fill="both", expand=True)

    # ── Embed Tab ──────────────────────────────────────────────────────────────

    def _build_embed_tab(self):
        frame = ttk.Frame(self._notebook)
        self._notebook.add(frame, text="  Embed Message  ")
        frame.columnconfigure(0, weight=1)

        # --- Cover file row
        self._cover_var = tk.StringVar()
        self._cover_info_var = tk.StringVar(value="No file selected.")
        self._embed_cap_var = tk.StringVar()

        row = self._card(frame, "Cover Audio File (WAV)", row=0)
        file_row = tk.Frame(row, bg=_PANEL_BG)
        file_row.pack(fill="x")
        tk.Entry(file_row, textvariable=self._cover_var,
                 bg=_ENTRY_BG, fg=_TEXT, insertbackground=_TEXT,
                 relief="flat", font=_FONT_MONO, bd=0
                 ).pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 6))
        ttk.Button(file_row, text="Browse…", style="Small.TButton",
                   command=self._browse_cover).pack(side="left")

        info_row = tk.Frame(row, bg=_PANEL_BG)
        info_row.pack(fill="x", pady=(4, 0))
        tk.Label(info_row, textvariable=self._cover_info_var,
                 font=_FONT_STATUS, fg=_TEXT_DIM, bg=_PANEL_BG).pack(side="left")
        tk.Label(info_row, textvariable=self._embed_cap_var,
                 font=_FONT_STATUS, fg=_INFO, bg=_PANEL_BG).pack(side="left", padx=(10, 0))

        # --- Secret message
        self._char_count_var = tk.StringVar(value="0 chars · 0 bytes")
        msg_row = self._card(frame, "Secret Message", row=1)
        tc_row = tk.Frame(msg_row, bg=_PANEL_BG)
        tc_row.pack(fill="x")
        tk.Label(tc_row, text="Enter the text you want to hide:",
                 font=_FONT_STATUS, fg=_TEXT_DIM, bg=_PANEL_BG).pack(side="left")
        tk.Label(tc_row, textvariable=self._char_count_var,
                 font=_FONT_STATUS, fg=_INFO, bg=_PANEL_BG).pack(side="right")

        self._msg_text = _PlaceholderText(
            msg_row,
            placeholder="Type your secret message here…",
            height=5, bg=_ENTRY_BG, fg=_TEXT, insertbackground=_TEXT,
            relief="flat", font=_FONT_LABEL, wrap="word", bd=0,
            selectbackground=_ACCENT, selectforeground="#ffffff",
        )
        self._msg_text.pack(fill="both", pady=(4, 0))
        self._msg_text.bind("<KeyRelease>", self._on_message_change)

        # --- Passphrase (embed)
        self._embed_pass_var = tk.StringVar()
        self._embed_pass_show = False
        pass_row = self._card(frame, "Passphrase", row=2)
        pk_row = tk.Frame(pass_row, bg=_PANEL_BG)
        pk_row.pack(fill="x")
        self._embed_pass_entry = tk.Entry(
            pk_row, textvariable=self._embed_pass_var,
            show="●", bg=_ENTRY_BG, fg=_TEXT, insertbackground=_TEXT,
            relief="flat", font=_FONT_LABEL, bd=0,
        )
        self._embed_pass_entry.pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 6))
        ttk.Button(pk_row, text="Show", style="Small.TButton",
                   command=lambda: self._toggle_pass(
                       self._embed_pass_entry, "embed"
                   )).pack(side="left")
        tk.Label(pass_row, text="Minimum 8 characters. Used for AES-256 key derivation and PRSG seeding.",
                 font=_FONT_STATUS, fg=_TEXT_DIM, bg=_PANEL_BG).pack(anchor="w", pady=(3, 0))

        # --- Output file
        self._output_var = tk.StringVar()
        out_row = self._card(frame, "Output Stego File", row=3)
        of_row = tk.Frame(out_row, bg=_PANEL_BG)
        of_row.pack(fill="x")
        tk.Entry(of_row, textvariable=self._output_var,
                 bg=_ENTRY_BG, fg=_TEXT, insertbackground=_TEXT,
                 relief="flat", font=_FONT_MONO, bd=0
                 ).pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 6))
        ttk.Button(of_row, text="Save As…", style="Small.TButton",
                   command=self._browse_output).pack(side="left")

        # --- Embed button
        btn_frame = tk.Frame(frame, bg=_DARK_BG)
        btn_frame.grid(row=4, column=0, pady=10, sticky="ew")
        self._embed_btn = ttk.Button(btn_frame, text="EMBED MESSAGE",
                                      style="Accent.TButton",
                                      command=self._run_embed)
        self._embed_btn.pack()

        # --- Metrics panel
        metrics_card = self._card(frame, "Quality Metrics", row=5)
        grid = tk.Frame(metrics_card, bg=_PANEL_BG)
        grid.pack(fill="x")

        self._snr_var = tk.StringVar(value="—")
        self._psnr_var = tk.StringVar(value="—")
        self._mse_var = tk.StringVar(value="—")
        self._payload_var = tk.StringVar(value="—")
        self._samples_var = tk.StringVar(value="—")
        self._cap_pct_var = tk.StringVar(value="—")

        metrics_data = [
            ("SNR", self._snr_var, "dB"),
            ("PSNR", self._psnr_var, "dB"),
            ("MSE", self._mse_var, ""),
        ]
        for col, (lbl, var, unit) in enumerate(metrics_data):
            cell = tk.Frame(grid, bg=_PANEL_BG)
            cell.grid(row=0, column=col, padx=18, pady=6)
            tk.Label(cell, textvariable=var, font=_FONT_METRIC_VAL,
                     fg=_GOOD, bg=_PANEL_BG).pack()
            tk.Label(cell, text=f"{lbl}  {unit}", font=_FONT_METRIC_LBL,
                     fg=_TEXT_DIM, bg=_PANEL_BG).pack()

        extra = tk.Frame(metrics_card, bg=_PANEL_BG)
        extra.pack(fill="x", pady=(2, 0))
        for lbl, var in [("Payload", self._payload_var),
                          ("Samples used", self._samples_var),
                          ("Capacity used", self._cap_pct_var)]:
            tk.Label(extra, text=f"{lbl}:", font=_FONT_STATUS, fg=_TEXT_DIM,
                     bg=_PANEL_BG).pack(side="left", padx=(0, 2))
            tk.Label(extra, textvariable=var, font=("Consolas", 9),
                     fg=_TEXT, bg=_PANEL_BG).pack(side="left", padx=(0, 20))

        frame.rowconfigure(1, weight=1)

    # ── Extract Tab ────────────────────────────────────────────────────────────

    def _build_extract_tab(self):
        frame = ttk.Frame(self._notebook)
        self._notebook.add(frame, text="  Extract Message  ")
        frame.columnconfigure(0, weight=1)

        # --- Stego file
        self._stego_var = tk.StringVar()
        self._stego_info_var = tk.StringVar(value="No file selected.")
        row = self._card(frame, "Stego Audio File (WAV)", row=0)
        sf_row = tk.Frame(row, bg=_PANEL_BG)
        sf_row.pack(fill="x")
        tk.Entry(sf_row, textvariable=self._stego_var,
                 bg=_ENTRY_BG, fg=_TEXT, insertbackground=_TEXT,
                 relief="flat", font=_FONT_MONO, bd=0
                 ).pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 6))
        ttk.Button(sf_row, text="Browse…", style="Small.TButton",
                   command=self._browse_stego).pack(side="left")
        tk.Label(row, textvariable=self._stego_info_var,
                 font=_FONT_STATUS, fg=_TEXT_DIM, bg=_PANEL_BG).pack(anchor="w", pady=(4, 0))

        # --- Passphrase (extract)
        self._extract_pass_var = tk.StringVar()
        self._extract_pass_show = False
        ep_row = self._card(frame, "Passphrase", row=1)
        ek_row = tk.Frame(ep_row, bg=_PANEL_BG)
        ek_row.pack(fill="x")
        self._extract_pass_entry = tk.Entry(
            ek_row, textvariable=self._extract_pass_var,
            show="●", bg=_ENTRY_BG, fg=_TEXT, insertbackground=_TEXT,
            relief="flat", font=_FONT_LABEL, bd=0,
        )
        self._extract_pass_entry.pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 6))
        ttk.Button(ek_row, text="Show", style="Small.TButton",
                   command=lambda: self._toggle_pass(
                       self._extract_pass_entry, "extract"
                   )).pack(side="left")
        tk.Label(ep_row, text="Must match the passphrase used during embedding.",
                 font=_FONT_STATUS, fg=_TEXT_DIM, bg=_PANEL_BG).pack(anchor="w", pady=(3, 0))

        # --- Extract button
        btn_frame = tk.Frame(frame, bg=_DARK_BG)
        btn_frame.grid(row=2, column=0, pady=10, sticky="ew")
        self._extract_btn = ttk.Button(btn_frame, text="EXTRACT MESSAGE",
                                        style="Accent.TButton",
                                        command=self._run_extract)
        self._extract_btn.pack()

        # --- Recovered message
        msg_card = self._card(frame, "Recovered Secret Message", row=3)
        self._recovered_text = tk.Text(
            msg_card, height=8, bg=_ENTRY_BG, fg=_GOOD,
            insertbackground=_TEXT, relief="flat", font=_FONT_LABEL,
            wrap="word", bd=0, state="disabled",
            selectbackground=_ACCENT, selectforeground="#ffffff",
        )
        self._recovered_text.pack(fill="both", expand=True)

        copy_row = tk.Frame(msg_card, bg=_PANEL_BG)
        copy_row.pack(fill="x", pady=(6, 0))
        ttk.Button(copy_row, text="Copy to Clipboard", style="Ghost.TButton",
                   command=self._copy_recovered).pack(side="right")
        self._recovered_chars_var = tk.StringVar(value="")
        tk.Label(copy_row, textvariable=self._recovered_chars_var,
                 font=_FONT_STATUS, fg=_TEXT_DIM, bg=_PANEL_BG).pack(side="left")

        frame.rowconfigure(3, weight=1)

    # ── Card helper ────────────────────────────────────────────────────────────

    def _card(self, parent, title: str, row: int) -> tk.Frame:
        """Create a labelled panel card and return its inner content frame."""
        outer = tk.Frame(parent, bg=_DARK_BG)
        outer.grid(row=row, column=0, sticky="ew", padx=6, pady=4)
        outer.columnconfigure(0, weight=1)

        tk.Label(outer, text=title, font=("Segoe UI", 9, "bold"),
                 fg=_TEXT_DIM, bg=_DARK_BG).pack(anchor="w", pady=(0, 2))

        inner = tk.Frame(outer, bg=_PANEL_BG)
        inner.pack(fill="both", padx=0, ipadx=12, ipady=8)
        inner.columnconfigure(0, weight=1)
        return inner

    # ── File browsers ──────────────────────────────────────────────────────────

    def _browse_cover(self):
        path = filedialog.askopenfilename(
            title="Select Cover WAV File",
            filetypes=[("WAV audio", "*.wav"), ("All files", "*.*")]
        )
        if not path:
            return
        self._cover_var.set(path)
        self._load_cover_info(path)
        # Auto-suggest output path
        base, _ = os.path.splitext(path)
        self._output_var.set(base + "_stego.wav")

    def _load_cover_info(self, path: str):
        try:
            info = get_audio_info(path)
            ch = "Stereo" if info["channels"] == 2 else "Mono"
            self._cover_info_var.set(
                f"{info['sample_rate_hz']} Hz · {info['bit_depth']}-bit · "
                f"{ch} · {info['duration_s']}s"
            )
            self._embed_cap_var.set(
                f"Max payload: {info['max_payload_bytes']:,} bytes "
                f"({info['max_payload_bytes'] * 8:,} bits)"
            )
        except (AudioFormatError, Exception) as exc:
            self._cover_info_var.set(f"Error: {exc}")
            self._embed_cap_var.set("")

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            title="Save Stego WAV File",
            defaultextension=".wav",
            filetypes=[("WAV audio", "*.wav")]
        )
        if path:
            self._output_var.set(path)

    def _browse_stego(self):
        path = filedialog.askopenfilename(
            title="Select Stego WAV File",
            filetypes=[("WAV audio", "*.wav"), ("All files", "*.*")]
        )
        if not path:
            return
        self._stego_var.set(path)
        try:
            info = get_audio_info(path)
            ch = "Stereo" if info["channels"] == 2 else "Mono"
            self._stego_info_var.set(
                f"{info['sample_rate_hz']} Hz · {info['bit_depth']}-bit · "
                f"{ch} · {info['duration_s']}s"
            )
        except Exception as exc:
            self._stego_info_var.set(f"Error: {exc}")

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _toggle_pass(self, entry: tk.Entry, which: str):
        current = entry.cget("show")
        entry.config(show="" if current else "●")

    def _on_message_change(self, _event=None):
        text = self._msg_text.get_real_text()
        n_chars = len(text)
        n_bytes = len(text.encode("utf-8"))
        self._char_count_var.set(f"{n_chars:,} chars · {n_bytes:,} bytes")

    def _set_status(self, msg: str, colour: str = _TEXT_DIM):
        self._status_var.set(msg)
        self._status_lbl.configure(fg=colour)

    def _copy_recovered(self):
        text = self._recovered_text.get("1.0", "end-1c")
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self._set_status("Recovered message copied to clipboard.", _INFO)

    def _set_buttons_state(self, state: str):
        self._embed_btn.config(state=state)
        self._extract_btn.config(state=state)

    # ── Core operations (threaded) ─────────────────────────────────────────────

    def _run_embed(self):
        cover = self._cover_var.get().strip()
        secret = self._msg_text.get_real_text()
        passphrase = self._embed_pass_var.get()
        output = self._output_var.get().strip()

        if not cover:
            messagebox.showerror("Missing Input", "Please select a cover WAV file.")
            return
        if not secret:
            messagebox.showerror("Missing Input", "Please enter a secret message.")
            return
        if not passphrase:
            messagebox.showerror("Missing Input", "Please enter a passphrase.")
            return
        if not output:
            messagebox.showerror("Missing Input", "Please specify an output file path.")
            return

        self._set_buttons_state("disabled")
        self._set_status("Embedding… please wait.", _INFO)

        def _worker():
            try:
                metrics = embed_message(cover, secret, passphrase, output)
                self.after(0, self._on_embed_success, metrics, output)
            except Exception as exc:
                self.after(0, self._on_operation_error, str(exc))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_embed_success(self, metrics: dict, output_path: str):
        snr = metrics["snr"]
        psnr = metrics["psnr"]
        mse = metrics["mse"]

        self._snr_var.set(f"{'∞' if math.isinf(snr) else f'{snr:.2f}'}")
        self._psnr_var.set(f"{'∞' if math.isinf(psnr) else f'{psnr:.2f}'}")
        self._mse_var.set(f"{mse:.6f}")
        self._payload_var.set(f"{metrics['payload_bytes']:,} bytes")
        self._samples_var.set(f"{metrics['samples_used']:,}")
        self._cap_pct_var.set(f"{metrics['capacity_percent']:.4f} %")

        snr_ok = math.isinf(snr) or snr >= 30.0
        colour = _GOOD if snr_ok else _WARN
        status = (
            f"Embedding complete. SNR = {snr:.2f} dB "
            f"({'✓ meets ≥ 30 dB target' if snr_ok else '⚠ below 30 dB target'}). "
            f"Saved: {os.path.basename(output_path)}"
        )
        self._set_status(status, colour)
        self._set_buttons_state("normal")

    def _run_extract(self):
        stego = self._stego_var.get().strip()
        passphrase = self._extract_pass_var.get()

        if not stego:
            messagebox.showerror("Missing Input", "Please select a stego WAV file.")
            return
        if not passphrase:
            messagebox.showerror("Missing Input", "Please enter the passphrase.")
            return

        self._set_buttons_state("disabled")
        self._set_status("Extracting… please wait.", _INFO)

        # Clear previous result
        self._recovered_text.config(state="normal")
        self._recovered_text.delete("1.0", tk.END)
        self._recovered_text.config(state="disabled")
        self._recovered_chars_var.set("")

        def _worker():
            try:
                message = extract_message(stego, passphrase)
                self.after(0, self._on_extract_success, message)
            except Exception as exc:
                self.after(0, self._on_operation_error, str(exc))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_extract_success(self, message: str):
        self._recovered_text.config(state="normal")
        self._recovered_text.delete("1.0", tk.END)
        self._recovered_text.insert("1.0", message)
        self._recovered_text.config(state="disabled")

        n_chars = len(message)
        n_bytes = len(message.encode("utf-8"))
        self._recovered_chars_var.set(f"{n_chars:,} chars · {n_bytes:,} bytes")

        self._set_status(
            f"Extraction successful. Recovered {n_chars:,} character(s).", _GOOD
        )
        self._set_buttons_state("normal")

    def _on_operation_error(self, error_msg: str):
        self._set_status(f"Error: {error_msg}", _WARN)
        self._set_buttons_state("normal")
        messagebox.showerror("Operation Failed", error_msg)
