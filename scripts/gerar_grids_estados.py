"""Gera 5 grids PNG (um por regiao) com os times dos estados."""

from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from PIL import Image, ImageDraw

from src.bandeiras import iso_time, sigla_time
from src.bandeiras_img import ALTURA_BANDEIRA, LARGURA_BANDEIRA, imagem_bandeira
from src.estados_brasil import ESTADOS_BRASIL, EstadoBrasil
from src.flag_cache import baixar_bandeira
from src.image_export import (
    PAL_CABECALHO,
    PAL_FUNDO,
    PAL_LINHA_IMPAR,
    PAL_LINHA_PAR,
    PAL_TEXTO,
    PAL_TEXTO_CAB,
    PAL_TITULO_LARANJA,
    _carregar_fontes,
)

REGIOES: list[tuple[str, tuple[str, ...]]] = [
    ("Norte", ("AC", "AP", "AM", "PA", "RO", "RR", "TO")),
    ("Nordeste", ("AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE")),
    ("Centro-Oeste", ("DF", "GO", "MT", "MS")),
    ("Sudeste", ("ES", "MG", "RJ", "SP")),
    ("Sul", ("PR", "RS", "SC")),
]

MARGEM = 24
ALTURA_TITULO = 52
ALTURA_CAB = 40
ALTURA_LINHA = 48
LARGURA = 520


def _por_uf() -> dict[str, EstadoBrasil]:
    return {estado.uf: estado for estado in ESTADOS_BRASIL}


def gerar_grid_regiao(regiao: str, ufs: tuple[str, ...], saida: Path) -> Path:
    for uf in ufs:
        baixar_bandeira(f"BR-{uf}", forcar=False)

    fontes = _carregar_fontes()
    mapa = _por_uf()
    estados = [mapa[uf] for uf in ufs]
    altura = MARGEM + ALTURA_TITULO + ALTURA_CAB + ALTURA_LINHA * len(estados) + MARGEM
    imagem = Image.new("RGB", (LARGURA, altura), PAL_FUNDO)
    draw = ImageDraw.Draw(imagem)

    draw.text(
        (MARGEM, MARGEM + 8),
        f"GRID — {regiao.upper()}",
        font=fontes["titulo"],
        fill=PAL_TITULO_LARANJA,
    )
    draw.text(
        (LARGURA - MARGEM, MARGEM + 14),
        f"{len(estados)} times",
        font=fontes["var"],
        fill=PAL_TEXTO_CAB,
        anchor="ra",
    )

    y = MARGEM + ALTURA_TITULO
    draw.rectangle((0, y, LARGURA, y + ALTURA_CAB), fill=PAL_CABECALHO)
    draw.text((MARGEM, y + ALTURA_CAB // 2), "#", font=fontes["cab"], fill=PAL_TEXTO_CAB, anchor="lm")
    draw.text(
        (MARGEM + 40, y + ALTURA_CAB // 2),
        "Time",
        font=fontes["cab"],
        fill=PAL_TEXTO_CAB,
        anchor="lm",
    )
    draw.text(
        (LARGURA - MARGEM, y + ALTURA_CAB // 2),
        "UF",
        font=fontes["cab"],
        fill=PAL_TEXTO_CAB,
        anchor="rm",
    )

    y += ALTURA_CAB
    for indice, estado in enumerate(estados, start=1):
        fundo = PAL_LINHA_PAR if indice % 2 == 0 else PAL_LINHA_IMPAR
        draw.rectangle((0, y, LARGURA, y + ALTURA_LINHA), fill=fundo)
        centro = y + ALTURA_LINHA // 2
        draw.text((MARGEM, centro), str(indice), font=fontes["linha"], fill=PAL_TEXTO, anchor="lm")

        codigo = iso_time(estado.nome_time) or estado.codigo
        bandeira = imagem_bandeira(codigo)
        bx = MARGEM + 36
        by = centro - ALTURA_BANDEIRA // 2
        imagem.paste(bandeira, (bx, by), bandeira)

        draw.text(
            (bx + LARGURA_BANDEIRA + 12, centro),
            estado.nome_time,
            font=fontes["linha"],
            fill=PAL_TEXTO,
            anchor="lm",
        )
        draw.text(
            (LARGURA - MARGEM, centro),
            sigla_time(estado.nome_time),
            font=fontes["linha"],
            fill=PAL_TEXTO,
            anchor="rm",
        )
        y += ALTURA_LINHA

    saida.parent.mkdir(parents=True, exist_ok=True)
    imagem.save(saida)
    return saida


def gerar_cinco_grids(pasta: Path) -> list[Path]:
    gerados: list[Path] = []
    for regiao, ufs in REGIOES:
        slug = regiao.lower().replace(" ", "-").replace("ô", "o").replace("é", "e")
        caminho = pasta / f"grid_{slug}.png"
        gerados.append(gerar_grid_regiao(regiao, ufs, caminho))
    return gerados


def main() -> int:
    pasta = BASE / "data" / "ultimo" / "png"
    caminhos = gerar_cinco_grids(pasta)
    print(f"Gerados {len(caminhos)} grids em {pasta}:")
    for caminho in caminhos:
        print(f"  - {caminho.name} ({caminho.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
