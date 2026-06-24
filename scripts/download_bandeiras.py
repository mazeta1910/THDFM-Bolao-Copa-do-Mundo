"""Baixa bandeiras reais do flagcdn.com para data/flags/."""

from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from src.flag_cache import FLAG_DIR, baixar_todas_bandeiras


def main() -> int:
    forcar = "--forcar" in sys.argv
    print(f"Baixando bandeiras para {FLAG_DIR} ...")
    sucesso, total_falhas, falhas = baixar_todas_bandeiras(forcar=forcar)
    print(f"Concluido: {sucesso} bandeira(s) em cache.")
    if falhas:
        print(f"Falhas ({total_falhas}):")
        for item in falhas:
            print(f"  - {item}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
