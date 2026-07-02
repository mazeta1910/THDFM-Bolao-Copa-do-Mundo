"""Composição do logo do bolão sobre PNGs exportados (issue #5)."""

from __future__ import annotations

from pathlib import Path

from src.data_paths import DATA_DIR
from src.image_export import PAL_FUNDO, PAL_TITULO_LARANJA

LOGO_PATH = DATA_DIR / "logo_bolao.png"
ALTURA_MAX_LOGO = 76
PADDING_FAIXA_LOGO = 6


def _logo_sem_margens(logo):
    """Remove padding escuro do arquivo do logo."""
    rgba = logo.convert("RGBA")
    pixels = rgba.load()
    largura, altura = rgba.size
    min_x, min_y = largura, altura
    max_x, max_y = 0, 0
    for y in range(altura):
        for x in range(largura):
            vermelho, verde, azul, alpha = pixels[x, y]
            if alpha > 10 and (vermelho > 20 or verde > 20 or azul > 20):
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    if min_x < max_x and min_y < max_y:
        return rgba.crop((min_x, min_y, max_x + 1, max_y + 1))
    return rgba


def compor_faixa_logo(
    imagem,
    logo_path: Path | None = None,
    *,
    altura_max: int = ALTURA_MAX_LOGO,
):
    """Logo inteiro, sem recorte — escala proporcional dentro da faixa."""
    from PIL import Image, ImageDraw

    caminho = logo_path or LOGO_PATH
    logo = _logo_sem_margens(Image.open(caminho))
    largura = imagem.width
    escala = min(largura / logo.width, altura_max / logo.height)
    nova_largura = max(1, int(logo.width * escala))
    nova_altura = max(1, int(logo.height * escala))
    logo = logo.resize((nova_largura, nova_altura), Image.Resampling.LANCZOS)

    altura_faixa = nova_altura + PADDING_FAIXA_LOGO
    resultado = Image.new("RGB", (largura, imagem.height + altura_faixa), PAL_FUNDO)
    x_logo = (largura - nova_largura) // 2
    y_logo = (altura_faixa - nova_altura) // 2
    resultado.paste(logo, (x_logo, y_logo), logo)
    resultado.paste(imagem, (0, altura_faixa))

    draw = ImageDraw.Draw(resultado)
    draw.line((0, altura_faixa - 1, largura, altura_faixa - 1), fill=PAL_TITULO_LARANJA, width=2)
    return resultado


def salvar_png_com_logo(imagem, path: str | Path) -> None:
    """Salva PNG aplicando a faixa do logo quando o arquivo existir."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if LOGO_PATH.is_file():
        imagem = compor_faixa_logo(imagem, LOGO_PATH)
    imagem.save(path, format="PNG")
