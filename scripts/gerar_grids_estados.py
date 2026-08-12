"""Gera grids 3x3 no estilo Hoops Grid.

Estrutura (como no Hoops Grid):
- Linhas  = times (aqui: times dos estados brasileiros)
- Colunas = categorias curadas (conquistas / estatisticas / eras)

Nao sao 6 times aleatorios nos dois eixos.
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
from src.categorias_grid import CATEGORIAS_GRID, CategoriaGrid, categorias_por_tipo
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
LARGURA_ROTULO = 178
ALTURA_ROTULO = 78
LADO_CELULA = 138


@dataclass(frozen=True, slots=True)
class GridJogo:
    numero: int
    seed: int
    times: tuple[EstadoBrasil, ...]  # linhas (eixo de times)
    categorias: tuple[CategoriaGrid, ...]  # colunas (eixo de categorias)


def _escolher_times(rng: random.Random) -> tuple[EstadoBrasil, ...]:
    return tuple(rng.sample(list(ESTADOS_BRASIL), TAMANHO))


def _escolher_categorias(rng: random.Random) -> tuple[CategoriaGrid, ...]:
    """Sorteia 3 categorias priorizando tipos distintos (estilo Hoops Grid)."""
    por_tipo = categorias_por_tipo()
    tipos = list(por_tipo.keys())
    rng.shuffle(tipos)

    escolhidas: list[CategoriaGrid] = []
    tipos_usados: set[str] = set()

    # 1) tenta pegar tipos diferentes primeiro
    for tipo in tipos:
        if len(escolhidas) >= TAMANHO:
            break
        candidatas = [c for c in por_tipo[tipo] if c not in escolhidas]
        if not candidatas:
            continue
        escolhidas.append(rng.choice(candidatas))
        tipos_usados.add(tipo)

    # 2) completa se ainda faltar
    resto = [c for c in CATEGORIAS_GRID if c not in escolhidas]
    while len(escolhidas) < TAMANHO and resto:
        escolhidas.append(resto.pop(rng.randrange(len(resto))))

    rng.shuffle(escolhidas)
    return tuple(escolhidas[:TAMANHO])


def gerar_grid_aleatorio(numero: int, *, seed: int | None = None) -> GridJogo:
    if seed is None:
        seed = random.randint(1, 10_000_000)
    rng = random.Random(seed)
    return GridJogo(
        numero=numero,
        seed=seed,
        times=_escolher_times(rng),
        categorias=_escolher_categorias(rng),
    )


def gerar_n_grids(n: int = 5, *, seed_base: int = 20260811) -> list[GridJogo]:
    grids: list[GridJogo] = []
    rng = random.Random(seed_base)
    usados: set[tuple[str, ...]] = set()
    tentativas = 0
    while len(grids) < n and tentativas < n * 80:
        tentativas += 1
        seed = rng.randint(1, 10_000_000)
        grid = gerar_grid_aleatorio(len(grids) + 1, seed=seed)
        chave = tuple(e.uf for e in grid.times) + tuple(c.id for c in grid.categorias)
        if chave in usados:
            continue
        usados.add(chave)
        grids.append(grid)
    if len(grids) < n:
        raise RuntimeError(f"Nao foi possivel gerar {n} grids distintos.")
    return grids


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
    bx = x + 12
    by = y + (altura - ALTURA_BANDEIRA) // 2
    imagem.paste(bandeira, (bx, by), bandeira)

    texto = estado.nome_time
    tx = bx + LARGURA_BANDEIRA + 10
    linhas = _quebra_rotulo(texto, draw, fontes["var"], largura - (tx - x) - 10)
    total_h = len(linhas) * 14
    ty = y + (altura - total_h) // 2
    for linha in linhas:
        draw.text((tx, ty), linha, font=fontes["var"], fill=PAL_TEXTO, anchor="lt")
        ty += 14


def _desenhar_rotulo_categoria(
    draw,
    x: int,
    y: int,
    largura: int,
    altura: int,
    categoria: CategoriaGrid,
    fontes,
) -> None:
    draw.rectangle((x, y, x + largura - 1, y + altura - 1), fill=PAL_CABECALHO, outline=PAL_BORDA)
    linhas = _quebra_rotulo(categoria.rotulo, draw, fontes["var"], largura - 16)
    total_h = len(linhas) * 14
    ty = y + (altura - total_h) // 2
    for linha in linhas:
        draw.text(
            (x + largura // 2, ty + 7),
            linha,
            font=fontes["var"],
            fill=PAL_TEXTO,
            anchor="mm",
        )
        ty += 14


def renderizar_grid(grid: GridJogo, saida: Path) -> Path:
    for estado in grid.times:
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
        f"seed {grid.seed}",
        font=fontes["var"],
        fill=PAL_TEXTO_SUAVE,
        anchor="ra",
    )
    draw.text(
        (MARGEM, MARGEM + 34),
        "Times (linhas) × Categorias (colunas) — estilo Hoops Grid",
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
        (MARGEM + LARGURA_ROTULO // 2, MARGEM + ALTURA_TITULO + ALTURA_ROTULO // 2 - 8),
        "TIME",
        font=fontes["var"],
        fill=PAL_TEXTO_SUAVE,
        anchor="mm",
    )
    draw.text(
        (MARGEM + LARGURA_ROTULO // 2, MARGEM + ALTURA_TITULO + ALTURA_ROTULO // 2 + 10),
        "× CAT.",
        font=fontes["var"],
        fill=PAL_TEXTO_SUAVE,
        anchor="mm",
    )

    # Colunas = categorias
    for indice, categoria in enumerate(grid.categorias):
        _desenhar_rotulo_categoria(
            draw,
            origem_x + indice * LADO_CELULA,
            MARGEM + ALTURA_TITULO,
            LADO_CELULA,
            ALTURA_ROTULO,
            categoria,
            fontes,
        )

    # Linhas = times dos estados
    for indice, estado in enumerate(grid.times):
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
        times = " / ".join(e.nome_time for e in grid.times)
        cats = " | ".join(c.rotulo for c in grid.categorias)
        print(f"Grid #{grid.numero}: times [{times}]  cats [{cats}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
