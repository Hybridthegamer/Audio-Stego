"""
Entry point for the Audio Steganography System desktop application.

Usage:
    python main.py

Requirements: See requirements.txt.
Python 3.10+ required (Ch. 3, Table 3.1).
"""

import sys
import os

# Ensure the project root is on sys.path so 'src' and 'gui' are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import AudioStegoApp


def main():
    app = AudioStegoApp()
    app.mainloop()


if __name__ == "__main__":
    main()
