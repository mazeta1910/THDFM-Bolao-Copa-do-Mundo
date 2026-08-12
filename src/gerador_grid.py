"""Geracao aleatoria de grids com validacao de solubilidade (estilo Hoops Grid).

Para cada dia:
- sorteia 3 criterios para linhas e 3 para colunas
- normalmente sem repetir o mesmo criterio nos dois eixos
- valida cada intersecao no banco (minimo de respostas)
- monta sequencialmente e retrocede (backtracking) se falhar
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from src.criterios_grid import CRITERIOS_GRID, CriterioGrid
from src.jogadores_grid import celula_soluvel, contar_intersecao, jogadores_grid

TAMANHO = 3
MIN_RESPOSTAS_CELULA = 5


@dataclass(frozen=True, slots=True)
class GridJogo:
    numero: int
    seed: int
    linhas: tuple[CriterioGrid, ...]
    colunas: tuple[CriterioGrid, ...]
    contagens: tuple[tuple[int, ...], ...]

    @property
    def minima_celula(self) -> int:
        return min(min(linha) for linha in self.contagens)


def _eixos_ok(linhas: list[CriterioGrid], colunas: list[CriterioGrid]) -> bool:
    ids_linha = {c.id for c in linhas}
    ids_coluna = {c.id for c in colunas}
    if ids_linha & ids_coluna:
        return False
    # Evita eixo 100% time x 100% time demais? Permitido, mas normalmente
    # misturado — nao bloqueamos aqui; a solubilidade decide.
    return True


def _contagens(
    linhas: list[CriterioGrid],
    colunas: list[CriterioGrid],
) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(contar_intersecao(linha, coluna) for coluna in colunas)
        for linha in linhas
    )


def _celulas_atuais_soluveis(
    linhas: list[CriterioGrid],
    colunas: list[CriterioGrid],
    *,
    minimo: int,
) -> bool:
    if not _eixos_ok(linhas, colunas):
        return False
    for linha in linhas:
        for coluna in colunas:
            if not celula_soluvel(linha, coluna, minimo=minimo):
                return False
    return True


def _candidatos(rng: random.Random, usados: set[str]) -> list[CriterioGrid]:
    pool = [c for c in CRITERIOS_GRID if c.id not in usados]
    rng.shuffle(pool)
    return pool


def gerar_grid_soluvel(
    numero: int = 1,
    *,
    seed: int | None = None,
    minimo: int = MIN_RESPOSTAS_CELULA,
    max_tentativas: int = 400,
) -> GridJogo:
    """Monta o grid sequencialmente com re-roll/backtracking por solubilidade."""
    if seed is None:
        seed = random.randint(1, 10_000_000)
    if not jogadores_grid():
        raise RuntimeError("Base de jogadores do grid vazia.")

    rng = random.Random(seed)

    for tentativa in range(max_tentativas):
        # Subseed por tentativa para variar os re-rolls mantendo reproducibilidade.
        local = random.Random(seed + tentativa * 9973)
        linhas: list[CriterioGrid] = []
        colunas: list[CriterioGrid] = []

        # 1) primeira linha + tres colunas (valida a 1a fileira)
        usados: set[str] = set()
        cand_linhas = _candidatos(local, usados)
        ok_primeira = False
        for cand_linha in cand_linhas:
            linhas = [cand_linha]
            usados_tmp = {cand_linha.id}
            colunas = []
            cand_cols = _candidatos(local, usados_tmp)
            sucesso_cols = True
            for _ in range(TAMANHO):
                escolhida = None
                for cand in cand_cols:
                    if cand.id in usados_tmp:
                        continue
                    prova = colunas + [cand]
                    if _celulas_atuais_soluveis(linhas, prova, minimo=minimo):
                        escolhida = cand
                        break
                if escolhida is None:
                    sucesso_cols = False
                    break
                colunas.append(escolhida)
                usados_tmp.add(escolhida.id)
                cand_cols = [c for c in cand_cols if c.id not in usados_tmp]
            if sucesso_cols and len(colunas) == TAMANHO:
                usados = usados_tmp
                ok_primeira = True
                break
        if not ok_primeira:
            continue

        # 2) demais linhas, validando as 3 celulas novas a cada linha
        sucesso = True
        for _ in range(TAMANHO - 1):
            cand_linhas = _candidatos(local, usados)
            escolhida = None
            for cand in cand_linhas:
                prova = linhas + [cand]
                if _celulas_atuais_soluveis(prova, colunas, minimo=minimo):
                    escolhida = cand
                    break
            if escolhida is None:
                sucesso = False
                break
            linhas.append(escolhida)
            usados.add(escolhida.id)

        if not sucesso or len(linhas) != TAMANHO:
            continue

        contagens = _contagens(linhas, colunas)
        return GridJogo(
            numero=numero,
            seed=seed,
            linhas=tuple(linhas),
            colunas=tuple(colunas),
            contagens=contagens,
        )

    raise RuntimeError(
        f"Nao foi possivel gerar grid soluvel (seed={seed}, minimo={minimo})."
    )


def gerar_n_grids(
    n: int = 5,
    *,
    seed_base: int = 20260811,
    minimo: int = MIN_RESPOSTAS_CELULA,
) -> list[GridJogo]:
    grids: list[GridJogo] = []
    rng = random.Random(seed_base)
    usados: set[tuple[str, ...]] = set()
    tentativas = 0
    while len(grids) < n and tentativas < n * 80:
        tentativas += 1
        seed = rng.randint(1, 10_000_000)
        grid = gerar_grid_soluvel(
            len(grids) + 1,
            seed=seed,
            minimo=minimo,
        )
        chave = tuple(c.id for c in grid.linhas) + tuple(c.id for c in grid.colunas)
        if chave in usados:
            continue
        usados.add(chave)
        grids.append(grid)
    if len(grids) < n:
        raise RuntimeError(f"Nao foi possivel gerar {n} grids distintos.")
    return grids
