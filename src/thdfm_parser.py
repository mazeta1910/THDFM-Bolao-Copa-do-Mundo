from __future__ import annotations

import csv
import re
from pathlib import Path

from src.models import BolaoData, Jogo, Palpite

JOGO_RE = re.compile(r"^Jogo\s+(\d+)$", re.IGNORECASE)
DATA_RE = re.compile(r"^\d+\s+DE\s+JUNHO$", re.IGNORECASE)


def _cell(row: list[str], index: int) -> str:
    if index >= len(row):
        return ""
    return row[index].strip()


def _parse_int(value: str) -> int | None:
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _is_palpite_row(row: list[str]) -> bool:
    nome = _cell(row, 1)
    casa = _cell(row, 2)
    sep = _cell(row, 3).lower()
    fora = _cell(row, 4)

    if not nome or nome.upper() == "PLACAR":
        return False
    if JOGO_RE.match(nome):
        return False
    if DATA_RE.match(nome):
        return False
    if sep != "x":
        return False
    if _parse_int(casa) is None or _parse_int(fora) is None:
        return False
    return True


def parse_thdfm_csv(path: str | Path) -> BolaoData:
    path = Path(path)
    bolao = BolaoData()
    participantes: list[str] = []
    current_date = ""
    current_game: Jogo | None = None

    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        for row in reader:
            label = _cell(row, 1)

            if DATA_RE.match(label):
                current_date = label
                continue

            jogo_match = JOGO_RE.match(label)
            if jogo_match:
                current_game = Jogo(
                    id=int(jogo_match.group(1)),
                    data=current_date,
                    casa=_cell(row, 2),
                    fora=_cell(row, 4),
                )
                bolao.jogos.append(current_game)
                continue

            if label.upper() == "PLACAR" and current_game is not None:
                gols_casa = _parse_int(_cell(row, 2))
                gols_fora = _parse_int(_cell(row, 4))
                if gols_casa is not None and gols_fora is not None:
                    current_game.gols_casa = gols_casa
                    current_game.gols_fora = gols_fora
                continue

            if current_game is not None and _is_palpite_row(row):
                nome = _cell(row, 1)
                palpite_casa = _parse_int(_cell(row, 2))
                palpite_fora = _parse_int(_cell(row, 4))
                if palpite_casa is None or palpite_fora is None:
                    continue

                bolao.palpites.append(
                    Palpite(
                        participante=nome,
                        jogo_id=current_game.id,
                        palpite_casa=palpite_casa,
                        palpite_fora=palpite_fora,
                    )
                )
                if nome not in participantes:
                    participantes.append(nome)

    bolao.participantes = participantes
    bolao.jogos.sort(key=lambda j: j.id)
    return bolao
