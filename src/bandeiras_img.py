from __future__ import annotations

from functools import lru_cache

from src.bandeiras import iso_time
from src.flag_cache import garantir_bandeira

LARGURA_BANDEIRA = 40
ALTURA_BANDEIRA = 28
ESPACO_ENTRE_BANDEIRAS = 8


def _placeholder(iso: str):
    from PIL import Image, ImageDraw, ImageFont

    imagem = Image.new("RGBA", (LARGURA_BANDEIRA, ALTURA_BANDEIRA), (71, 85, 105, 255))
    draw = ImageDraw.Draw(imagem)
    texto = iso.upper()[:3]
    fonte = ImageFont.load_default()
    draw.text(
        (LARGURA_BANDEIRA // 2, ALTURA_BANDEIRA // 2),
        texto,
        font=fonte,
        fill=(241, 245, 249),
        anchor="mm",
    )
    return imagem


@lru_cache(maxsize=64)
def imagem_bandeira(iso: str):
    from PIL import Image

    codigo = iso.upper()
    try:
        caminho = garantir_bandeira(codigo)
        with Image.open(caminho) as original:
            return original.convert("RGBA").resize(
                (LARGURA_BANDEIRA, ALTURA_BANDEIRA),
                Image.Resampling.LANCZOS,
            )
    except Exception:
        return _placeholder(codigo)


def largura_confronto(fonte_x) -> int:
    from PIL import Image, ImageDraw

    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    largura_x = int(draw.textlength("x", font=fonte_x))
    return LARGURA_BANDEIRA + ESPACO_ENTRE_BANDEIRAS + largura_x + ESPACO_ENTRE_BANDEIRAS + LARGURA_BANDEIRA


def colar_confronto(
    imagem,
    centro_x: int,
    centro_y: int,
    casa: str,
    fora: str,
    *,
    fonte_x,
    cor_x: tuple[int, int, int] = (255, 255, 255),
) -> None:
    from PIL import ImageDraw

    iso_casa = iso_time(casa) or "XX"
    iso_fora = iso_time(fora) or "XX"
    bandeira_casa = imagem_bandeira(iso_casa)
    bandeira_fora = imagem_bandeira(iso_fora)

    draw = ImageDraw.Draw(imagem)
    largura_x = int(draw.textlength("x", font=fonte_x))
    largura_total = largura_confronto(fonte_x)
    x_inicio = centro_x - largura_total // 2
    y_bandeira = centro_y - ALTURA_BANDEIRA // 2

    imagem.paste(bandeira_casa, (x_inicio, y_bandeira), bandeira_casa)
    x_meio = x_inicio + LARGURA_BANDEIRA + ESPACO_ENTRE_BANDEIRAS
    draw.text(
        (x_meio + largura_x // 2, centro_y),
        "x",
        font=fonte_x,
        fill=cor_x,
        anchor="mm",
    )
    x_fora = x_meio + largura_x + ESPACO_ENTRE_BANDEIRAS
    imagem.paste(bandeira_fora, (x_fora, y_bandeira), bandeira_fora)
