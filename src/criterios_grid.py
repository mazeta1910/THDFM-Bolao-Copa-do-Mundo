"""Criterios unificados do grid (times + categorias).

Linhas e colunas sorteiam do mesmo pool — como no Hoops Grid.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.categorias_grid import CATEGORIAS_GRID
from src.estados_brasil import ESTADOS_BRASIL


@dataclass(frozen=True, slots=True)
class CriterioGrid:
    id: str
    rotulo: str
    tipo: str  # time | conquista | estatistica | era | selecao
    uf: str | None = None  # preenchido so para tipo=time


def _criterios_times() -> tuple[CriterioGrid, ...]:
    return tuple(
        CriterioGrid(
            id=f"time_{estado.uf.lower()}",
            rotulo=estado.nome_time,
            tipo="time",
            uf=estado.uf,
        )
        for estado in ESTADOS_BRASIL
    )


def _criterios_categorias() -> tuple[CriterioGrid, ...]:
    return tuple(
        CriterioGrid(id=cat.id, rotulo=cat.rotulo, tipo=cat.tipo, uf=None)
        for cat in CATEGORIAS_GRID
    )


CRITERIOS_GRID: tuple[CriterioGrid, ...] = _criterios_times() + _criterios_categorias()


def criterios_por_id() -> dict[str, CriterioGrid]:
    return {c.id: c for c in CRITERIOS_GRID}


def criterios_por_tipo() -> dict[str, list[CriterioGrid]]:
    agrupado: dict[str, list[CriterioGrid]] = {}
    for criterio in CRITERIOS_GRID:
        agrupado.setdefault(criterio.tipo, []).append(criterio)
    return agrupado
