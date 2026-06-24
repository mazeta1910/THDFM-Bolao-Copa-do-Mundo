"""Reinicia o bolão para uma nova planilha da fase de grupos."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from src.cli import cmd_reset


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reinicia o bolão THDFM")
    parser.add_argument("--arquivo", help="CSV da fase de grupos")
    parser.add_argument("--sem-baseline", action="store_true")
    args = parser.parse_args()
    raise SystemExit(cmd_reset(args))
