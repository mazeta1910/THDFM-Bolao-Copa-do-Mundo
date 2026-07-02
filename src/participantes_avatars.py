"""Avatares dos participantes (foto ou iniciais) — preview da issue #4."""

from __future__ import annotations

import json
import hashlib
import unicodedata
from pathlib import Path

from src.data_paths import PARTICIPANTES_DIR, PARTICIPANTES_MANIFEST

AVATAR_TAMANHO = 44
AVATAR_ESPACO = 12
ALTURA_LINHA_AVATAR = 52
EXTENSOES_FOTO = (".png", ".jpg", ".jpeg", ".webp")


def carregar_mapa_arquivos(manifest: Path | None = None) -> dict[str, str]:
    caminho = manifest or PARTICIPANTES_MANIFEST
    if not caminho.is_file():
        return {}
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    return {
        item["nome"].strip(): item["arquivo"].strip()
        for item in dados.get("participantes", [])
        if item.get("nome") and item.get("arquivo")
    }


def iniciais_participante(nome: str) -> str:
    partes = [p for p in nome.replace("(", " ").replace(")", " ").split() if p]
    if not partes:
        return "?"
    if len(partes) == 1:
        return partes[0][:2].upper()
    return (partes[0][0] + partes[1][0]).upper()


def cor_avatar(nome: str) -> tuple[int, int, int]:
    digest = hashlib.md5(nome.strip().lower().encode("utf-8")).hexdigest()
    r = 80 + int(digest[0:2], 16) % 120
    g = 80 + int(digest[2:4], 16) % 120
    b = 80 + int(digest[4:6], 16) % 120
    return (r, g, b)


def resolver_foto_participante(
    nome: str,
    *,
    mapa: dict[str, str] | None = None,
    pasta: Path | None = None,
) -> Path | None:
    mapa = mapa if mapa is not None else carregar_mapa_arquivos()
    arquivo = mapa.get(nome.strip())
    if not arquivo:
        return None
    base = pasta or PARTICIPANTES_DIR
    stem = Path(arquivo).stem
    for ext in EXTENSOES_FOTO:
        candidato = base / f"{stem}{ext}"
        if candidato.is_file():
            return candidato
    candidato = base / arquivo
    if candidato.is_file():
        return candidato
    return None


def desenhar_avatar(
    base_image,
    draw,
    x: int,
    y: int,
    tamanho: int,
    nome: str,
    *,
    mapa: dict[str, str] | None = None,
    pasta: Path | None = None,
) -> None:
    from PIL import Image, ImageDraw

    cx = x + tamanho // 2
    cy = y + tamanho // 2
    raio = tamanho // 2
    foto = resolver_foto_participante(nome, mapa=mapa, pasta=pasta)

    if foto is not None:
        try:
            img = Image.open(foto).convert("RGBA")
            img = img.resize((tamanho, tamanho), Image.Resampling.LANCZOS)
            mascara = Image.new("L", (tamanho, tamanho), 0)
            ImageDraw.Draw(mascara).ellipse((0, 0, tamanho - 1, tamanho - 1), fill=255)
            recorte = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
            recorte.paste(img, (0, 0), mascara)
            base_image.paste(recorte, (x, y), recorte)
            draw.ellipse(
                (x, y, x + tamanho - 1, y + tamanho - 1),
                outline=(90, 90, 90),
                width=1,
            )
            return
        except OSError:
            pass

    cor = cor_avatar(nome)
    draw.ellipse((x, y, x + tamanho - 1, y + tamanho - 1), fill=cor, outline=(90, 90, 90), width=1)
    iniciais = iniciais_participante(nome)
    fonte_tamanho = 11 if len(iniciais) > 1 else 13
    from src.image_export import _carregar_fontes

    fontes = _carregar_fontes()
    fonte = fontes["var"]
    draw.text((cx, cy), iniciais, font=fonte, fill=(255, 255, 255), anchor="mm")


def largura_extra_avatar() -> int:
    return AVATAR_TAMANHO + AVATAR_ESPACO
