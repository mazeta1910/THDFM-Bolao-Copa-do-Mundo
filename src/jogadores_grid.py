"""Base de jogadores e consulta de intersecao para solubilidade do grid."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from src.criterios_grid import CriterioGrid
from src.data_paths import DATA_DIR

JOGADORES_GRID_JSON = DATA_DIR / "base" / "jogadores_grid.json"


@dataclass(frozen=True, slots=True)
class JogadorGrid:
    nome: str
    ufs: frozenset[str]
    tags: frozenset[str]


def _carregar_jogadores(path: Path | None = None) -> tuple[JogadorGrid, ...]:
    caminho = path or JOGADORES_GRID_JSON
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    jogadores: list[JogadorGrid] = []
    for item in dados.get("jogadores", []):
        jogadores.append(
            JogadorGrid(
                nome=str(item["nome"]),
                ufs=frozenset(str(u).upper() for u in item.get("ufs", [])),
                tags=frozenset(str(t) for t in item.get("tags", [])),
            )
        )
    return tuple(jogadores)


@lru_cache(maxsize=1)
def jogadores_grid() -> tuple[JogadorGrid, ...]:
    return _carregar_jogadores()


def _atende(jogador: JogadorGrid, criterio: CriterioGrid) -> bool:
    if criterio.tipo == "time":
        return bool(criterio.uf and criterio.uf.upper() in jogador.ufs)
    return criterio.id in jogador.tags


def jogadores_na_intersecao(
    linha: CriterioGrid,
    coluna: CriterioGrid,
    *,
    base: tuple[JogadorGrid, ...] | None = None,
) -> list[JogadorGrid]:
    pool = base if base is not None else jogadores_grid()
    return [j for j in pool if _atende(j, linha) and _atende(j, coluna)]


def contar_intersecao(
    linha: CriterioGrid,
    coluna: CriterioGrid,
    *,
    base: tuple[JogadorGrid, ...] | None = None,
) -> int:
    return len(jogadores_na_intersecao(linha, coluna, base=base))


def celula_soluvel(
    linha: CriterioGrid,
    coluna: CriterioGrid,
    *,
    minimo: int,
    base: tuple[JogadorGrid, ...] | None = None,
) -> bool:
    if linha.id == coluna.id:
        return False
    return contar_intersecao(linha, coluna, base=base) >= minimo
