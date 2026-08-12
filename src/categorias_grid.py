"""Categorias nao-time do grid (estilo Hoops Grid).

No Hoops Grid um eixo e de times e o outro mistura conquistas, eras e
estatisticas — nao sao 6 times aleatorios.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CategoriaGrid:
    id: str
    rotulo: str
    tipo: str  # conquista | estatistica | era | selecao


# Pool curado (nao aleatorio "solto"): o sorteio escolhe 3 daqui por grid.
CATEGORIAS_GRID: tuple[CategoriaGrid, ...] = (
    CategoriaGrid("brasileiro", "Campeão Brasileiro", "conquista"),
    CategoriaGrid("copa_brasil", "Campeão Copa do Brasil", "conquista"),
    CategoriaGrid("libertadores", "Campeão Libertadores", "conquista"),
    CategoriaGrid("sudamericana", "Campeão Sul-Americana", "conquista"),
    CategoriaGrid("mundial", "Campeão Mundial", "conquista"),
    CategoriaGrid("selecao", "Jogou na Seleção", "selecao"),
    CategoriaGrid("copa_mundo", "Disputou Copa do Mundo", "selecao"),
    CategoriaGrid("artilheiro_br", "Artilheiro do Brasileirão", "estatistica"),
    CategoriaGrid("10_gols", "10+ gols (temporada)", "estatistica"),
    CategoriaGrid("20_gols", "20+ gols (temporada)", "estatistica"),
    CategoriaGrid("100_jogos", "100+ jogos pelo clube", "estatistica"),
    CategoriaGrid("anos_90", "Jogou nos anos 90", "era"),
    CategoriaGrid("anos_2000", "Jogou nos anos 2000", "era"),
    CategoriaGrid("anos_2010", "Jogou nos anos 2010", "era"),
    CategoriaGrid("anos_2020", "Jogou nos anos 2020", "era"),
)


def categorias_por_tipo() -> dict[str, list[CategoriaGrid]]:
    agrupado: dict[str, list[CategoriaGrid]] = {}
    for categoria in CATEGORIAS_GRID:
        agrupado.setdefault(categoria.tipo, []).append(categoria)
    return agrupado
