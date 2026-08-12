"""Gera grids 3x3 no estilo Hoops Grid com validacao de solubilidade.

Linhas e colunas sorteiam 3 criterios cada do mesmo pool (times + categorias),
sem repetir o mesmo criterio nos dois eixos. Cada celula exige um minimo de
jogadores validos na base.
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from PIL import Image, ImageDraw

from src.bandeiras import iso_time
from src.bandeiras_img import ALTURA_BANDEIRA, LARGURA_BANDEIRA, imagem_bandeira
from src.criterios_grid import CriterioGrid
from src.flag_cache import baixar_bandeira
from src.gerador_grid import GridJogo, gerar_n_grids
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
LARGURA_ROTULO = 178
ALTURA_ROTULO = 78
LADO_CELULA = 138


def _quebra_rotulo(texto: str, draw, fonte, largura_max: int) -> list[str]:
    palavras = texto.split()
    linhas: list[str] = []
    atual = ""
    for palavra in palavras:
        tentativa = palavra if not atual else f"{atual} {palavra}"
        if int(draw.textlength(tentativa, font=fonte)) <= largura_max:
            atual = tentativa
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas or [texto]


def _desenhar_rotulo_criterio(
    imagem,
    draw,
    x: int,
    y: int,
    largura: int,
    altura: int,
    criterio: CriterioGrid,
    fontes,
    *,
    horizontal: bool,
) -> None:
    draw.rectangle((x, y, x + largura - 1, y + altura - 1), fill=PAL_CABECALHO, outline=PAL_BORDA)

    if criterio.tipo == "time" and criterio.uf:
        codigo = iso_time(criterio.rotulo) or f"BR-{criterio.uf}"
        bandeira = imagem_bandeira(codigo)
        if horizontal:
            bx = x + (largura - LARGURA_BANDEIRA) // 2
            by = y + 8
            imagem.paste(bandeira, (bx, by), bandeira)
            linhas = _quebra_rotulo(criterio.rotulo, draw, fontes["var"], largura - 12)
            ty = y + 8 + ALTURA_BANDEIRA + 4
            for linha in linhas[:2]:
                draw.text((x + largura // 2, ty + 6), linha, font=fontes["var"], fill=PAL_TEXTO, anchor="mm")
                ty += 13
        else:
            bx = x + 10
            by = y + (altura - ALTURA_BANDEIRA) // 2
            imagem.paste(bandeira, (bx, by), bandeira)
            tx = bx + LARGURA_BANDEIRA + 8
            linhas = _quebra_rotulo(criterio.rotulo, draw, fontes["var"], largura - (tx - x) - 8)
            total_h = len(linhas[:2]) * 14
            ty = y + (altura - total_h) // 2
            for linha in linhas[:2]:
                draw.text((tx, ty), linha, font=fontes["var"], fill=PAL_TEXTO, anchor="lt")
                ty += 14
        return

    linhas = _quebra_rotulo(criterio.rotulo, draw, fontes["var"], largura - 16)
    total_h = len(linhas[:3]) * 14
    ty = y + (altura - total_h) // 2
    for linha in linhas[:3]:
        draw.text(
            (x + largura // 2, ty + 7),
            linha,
            font=fontes["var"],
            fill=PAL_TEXTO,
            anchor="mm",
        )
        ty += 14


def renderizar_grid(grid: GridJogo, saida: Path) -> Path:
    for criterio in (*grid.linhas, *grid.colunas):
        if criterio.tipo == "time" and criterio.uf:
            baixar_bandeira(f"BR-{criterio.uf}", forcar=False)

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
        f"seed {grid.seed} · min {grid.minima_celula}+",
        font=fontes["var"],
        fill=PAL_TEXTO_SUAVE,
        anchor="ra",
    )
    draw.text(
        (MARGEM, MARGEM + 34),
        "3 critérios × 3 critérios (sem repetir nos eixos) · solubilidade ok",
        font=fontes["var"],
        fill=PAL_TEXTO_CAB,
    )

    origem_x = MARGEM + LARGURA_ROTULO
    origem_y = MARGEM + ALTURA_TITULO + ALTURA_ROTULO

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

    for indice, criterio in enumerate(grid.colunas):
        _desenhar_rotulo_criterio(
            imagem,
            draw,
            origem_x + indice * LADO_CELULA,
            MARGEM + ALTURA_TITULO,
            LADO_CELULA,
            ALTURA_ROTULO,
            criterio,
            fontes,
            horizontal=True,
        )

    for indice, criterio in enumerate(grid.linhas):
        _desenhar_rotulo_criterio(
            imagem,
            draw,
            MARGEM,
            origem_y + indice * LADO_CELULA,
            LARGURA_ROTULO,
            LADO_CELULA,
            criterio,
            fontes,
            horizontal=False,
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
                (x + LADO_CELULA // 2, y + LADO_CELULA // 2 - 8),
                "?",
                font=fontes["titulo"],
                fill=(70, 70, 70),
                anchor="mm",
            )
            draw.text(
                (x + LADO_CELULA // 2, y + LADO_CELULA // 2 + 18),
                f"{grid.contagens[linha][coluna]} ops",
                font=fontes["var"],
                fill=(90, 90, 90),
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
    print(f"Gerados {len(caminhos)} grids soluveis em {pasta}:")
    for caminho in caminhos:
        print(f"  - {caminho.name}")
    for grid in gerar_n_grids(5):
        linhas = " / ".join(c.rotulo for c in grid.linhas)
        cols = " | ".join(c.rotulo for c in grid.colunas)
        print(f"Grid #{grid.numero}: L[{linhas}]  C[{cols}]  min={grid.minima_celula}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
