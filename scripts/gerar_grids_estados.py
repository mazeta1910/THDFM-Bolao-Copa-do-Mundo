"""Gera grids 3x3 aleatorios no estilo do jogo (Immaculate Grid / Futebol Grid).

Eixos = times dos estados brasileiros. Cada celula fica vazia para o jogador
preencher com um atleta que combine linha + coluna.
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from PIL import Image, ImageDraw

from src.bandeiras import iso_time
from src.bandeiras_img import ALTURA_BANDEIRA, LARGURA_BANDEIRA, imagem_bandeira
from src.estados_brasil import ESTADOS_BRASIL, EstadoBrasil
from src.flag_cache import baixar_bandeira
from src.image_export import (
    PAL_BORDA,
    PAL_CABECALHO,
    PAL_FUNDO,
    PAL_TEXTO,
    PAL_TEXTO_CAB,
    PAL_TEXTO_SUAVE,
    PAL_TITULO_LARANJA,
    _carregar_fontes,
)

TAMANHO = 3
MARGEM = 20
ALTURA_TITULO = 56
LARGURA_ROTULO = 168
ALTURA_ROTULO = 72
LADO_CELULA = 132


@dataclass(frozen=True, slots=True)
class GridJogo:
    numero: int
    seed: int
    colunas: tuple[EstadoBrasil, ...]
    linhas: tuple[EstadoBrasil, ...]


def _escolher_estados(rng: random.Random, quantidade: int) -> tuple[EstadoBrasil, ...]:
    return tuple(rng.sample(list(ESTADOS_BRASIL), quantidade))


def gerar_grid_aleatorio(numero: int, *, seed: int | None = None) -> GridJogo:
    if seed is None:
        seed = random.randint(1, 10_000_000)
    rng = random.Random(seed)
    escolhidos = _escolher_estados(rng, TAMANHO * 2)
    return GridJogo(
        numero=numero,
        seed=seed,
        colunas=escolhidos[:TAMANHO],
        linhas=escolhidos[TAMANHO:],
    )


def gerar_n_grids(n: int = 5, *, seed_base: int = 20260811) -> list[GridJogo]:
    """Gera N grids determinísticos a partir de seed_base (reproduzível nos testes)."""
    grids: list[GridJogo] = []
    rng = random.Random(seed_base)
    usados: set[tuple[str, ...]] = set()
    tentativas = 0
    while len(grids) < n and tentativas < n * 50:
        tentativas += 1
        seed = rng.randint(1, 10_000_000)
        grid = gerar_grid_aleatorio(len(grids) + 1, seed=seed)
        chave = tuple(e.uf for e in (*grid.colunas, *grid.linhas))
        if chave in usados:
            continue
        usados.add(chave)
        grids.append(grid)
    if len(grids) < n:
        raise RuntimeError(f"Nao foi possivel gerar {n} grids distintos.")
    return grids


def _texto_curto(estado: EstadoBrasil) -> str:
    return estado.nome_time.replace("Time ", "")


def _desenhar_rotulo_time(
    imagem,
    draw,
    x: int,
    y: int,
    largura: int,
    altura: int,
    estado: EstadoBrasil,
    fontes,
) -> None:
    draw.rectangle((x, y, x + largura - 1, y + altura - 1), fill=PAL_CABECALHO, outline=PAL_BORDA)
    codigo = iso_time(estado.nome_time) or estado.codigo
    bandeira = imagem_bandeira(codigo)
    bx = x + (largura - LARGURA_BANDEIRA) // 2
    by = y + 10
    imagem.paste(bandeira, (bx, by), bandeira)
    draw.text(
        (x + largura // 2, y + altura - 14),
        _texto_curto(estado),
        font=fontes["var"],
        fill=PAL_TEXTO,
        anchor="mm",
    )


def renderizar_grid(grid: GridJogo, saida: Path) -> Path:
    for estado in (*grid.colunas, *grid.linhas):
        baixar_bandeira(estado.codigo, forcar=False)

    fontes = _carregar_fontes()
    largura = MARGEM * 2 + LARGURA_ROTULO + LADO_CELULA * TAMANHO
    altura = MARGEM * 2 + ALTURA_TITULO + ALTURA_ROTULO + LADO_CELULA * TAMANHO
    imagem = Image.new("RGB", (largura, altura), PAL_FUNDO)
    draw = ImageDraw.Draw(imagem)

    draw.text(
        (MARGEM, MARGEM + 6),
        f"GRID #{grid.numero}",
        font=fontes["titulo"],
        fill=PAL_TITULO_LARANJA,
    )
    draw.text(
        (largura - MARGEM, MARGEM + 12),
        f"seed {grid.seed} · 9 tentativas",
        font=fontes["var"],
        fill=PAL_TEXTO_SUAVE,
        anchor="ra",
    )
    draw.text(
        (MARGEM, MARGEM + 34),
        "Encontre um jogador para cada cruzamento (linha × coluna)",
        font=fontes["var"],
        fill=PAL_TEXTO_CAB,
    )

    origem_x = MARGEM + LARGURA_ROTULO
    origem_y = MARGEM + ALTURA_TITULO + ALTURA_ROTULO

    # Canto superior esquerdo
    draw.rectangle(
        (MARGEM, MARGEM + ALTURA_TITULO, origem_x - 1, origem_y - 1),
        fill=PAL_FUNDO,
        outline=PAL_BORDA,
    )
    draw.text(
        (MARGEM + LARGURA_ROTULO // 2, MARGEM + ALTURA_TITULO + ALTURA_ROTULO // 2),
        "×",
        font=fontes["titulo"],
        fill=PAL_TEXTO_SUAVE,
        anchor="mm",
    )

    for indice, estado in enumerate(grid.colunas):
        _desenhar_rotulo_time(
            imagem,
            draw,
            origem_x + indice * LADO_CELULA,
            MARGEM + ALTURA_TITULO,
            LADO_CELULA,
            ALTURA_ROTULO,
            estado,
            fontes,
        )

    for indice, estado in enumerate(grid.linhas):
        _desenhar_rotulo_time(
            imagem,
            draw,
            MARGEM,
            origem_y + indice * LADO_CELULA,
            LARGURA_ROTULO,
            LADO_CELULA,
            estado,
            fontes,
        )

    for linha in range(TAMANHO):
        for coluna in range(TAMANHO):
            x = origem_x + coluna * LADO_CELULA
            y = origem_y + linha * LADO_CELULA
            draw.rectangle(
                (x, y, x + LADO_CELULA - 1, y + LADO_CELULA - 1),
                fill=(18, 18, 18),
                outline=PAL_BORDA,
            )
            draw.text(
                (x + LADO_CELULA // 2, y + LADO_CELULA // 2),
                "?",
                font=fontes["titulo"],
                fill=(70, 70, 70),
                anchor="mm",
            )

    saida.parent.mkdir(parents=True, exist_ok=True)
    imagem.save(saida)
    return saida


def gerar_cinco_grids(pasta: Path, *, seed_base: int = 20260811) -> list[Path]:
    caminhos: list[Path] = []
    for grid in gerar_n_grids(5, seed_base=seed_base):
        caminho = pasta / f"grid_jogo_{grid.numero:02d}.png"
        caminhos.append(renderizar_grid(grid, caminho))
    return caminhos


def main() -> int:
    pasta = BASE / "data" / "ultimo" / "png"
    caminhos = gerar_cinco_grids(pasta)
    print(f"Gerados {len(caminhos)} grids de jogo em {pasta}:")
    for caminho in caminhos:
        print(f"  - {caminho.name}")
    for grid in gerar_n_grids(5):
        cols = " | ".join(e.nome_time for e in grid.colunas)
        rows = " / ".join(e.nome_time for e in grid.linhas)
        print(f"Grid #{grid.numero}: colunas [{cols}]  linhas [{rows}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
