"""Copia os CSVs de Downloads para data/ se ainda não existirem."""

from __future__ import annotations

import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
DOWNLOADS = Path.home() / "Downloads"

SOURCES = {
    "base/bolao.csv": DOWNLOADS / "BOLÃO THDFM WC26 - Fase de grupos.csv",
    "fontes/classificacao_referencia.csv": DOWNLOADS / "BOLÃO THDFM WC26 - CLASSIFICAÇÃO PROVISÓRIA.csv",
    "fontes/BOLÃO THDFM WC26 - CLASSIFICAÇÃO PROVISÓRIA (1).csv": DOWNLOADS
    / "BOLÃO THDFM WC26 - CLASSIFICAÇÃO PROVISÓRIA (1).csv",
}


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "base").mkdir(parents=True, exist_ok=True)
    (DATA / "fontes").mkdir(parents=True, exist_ok=True)
    for dest_rel, source in SOURCES.items():
        dest = DATA / dest_rel
        if dest.exists():
            print(f"OK (já existe): {dest}")
            continue
        if not source.exists():
            print(f"Pulando {dest_rel}: origem não encontrada em {source}")
            continue
        shutil.copy2(source, dest)
        print(f"Copiado: {source} -> {dest}")


if __name__ == "__main__":
    main()
