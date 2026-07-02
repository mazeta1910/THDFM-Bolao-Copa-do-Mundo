"""Gera PNG de escopo: classificação com miniaturas (issue #4)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.cli import carregar_bolao
from src.data_paths import DATA_DIR
from src.image_export import (
    ALTURA_RODAPE,
    ALTURA_TITULO_TABELA,
    MARGEM,
    PAL_BORDA,
    PAL_CABECALHO,
    PAL_LINHA_IMPAR,
    PAL_LINHA_LIDER,
    PAL_LINHA_PAR,
    PAL_TEXTO,
    PAL_TEXTO_CAB,
    PAL_TEXTO_LIDER,
    PAL_TEXTO_SUAVE,
    PAL_TITULO_LARANJA,
    PADDING_NOME,
    _COLUNAS_PONTOS,
    _carregar_fontes,
    _desenhar_coluna_posicao,
    _layout_classificacao,
    _largura_nome,
)
from src.participantes_avatars import (
    ALTURA_LINHA_AVATAR,
    AVATAR_TAMANHO,
    desenhar_avatar,
    largura_extra_avatar,
)
from src.ranking import classificacao_ativa, gerar_classificacao
from src.snapshot import carregar_snapshot
from src.data_paths import SNAPSHOT_JSON


def renderizar_preview(classificacao, *, limite: int | None = None):
    from PIL import Image, ImageDraw

    if limite is not None:
        classificacao = classificacao[:limite]
    fontes = _carregar_fontes()
    extra = largura_extra_avatar()
    largura_nome = _largura_nome(classificacao, fontes["linha"]) + extra
    layout = _layout_classificacao(largura_nome, mostrar_rod=True, fonte_cab=fontes["cab"])
    largura = layout["largura_total"]
    larguras_pontos = layout["larguras_pontos"]

    altura_titulo = 52
    altura_nota = 36
    altura_linha = ALTURA_LINHA_AVATAR
    altura = (
        MARGEM
        + altura_titulo
        + altura_nota
        + ALTURA_TITULO_TABELA
        + altura_linha * len(classificacao)
        + ALTURA_RODAPE
        + MARGEM
    )

    imagem = Image.new("RGB", (largura, altura), (18, 18, 18))
    draw = ImageDraw.Draw(imagem)
    y = MARGEM

    draw.text(
        (MARGEM, y),
        "PREVIEW — Classificação com miniaturas",
        font=fontes["secao"],
        fill=PAL_TITULO_LARANJA,
    )
    y += 28
    draw.text(
        (MARGEM, y),
        "Escopo issue #4 · foto real ou iniciais coloridas (fallback)",
        font=fontes["sub"],
        fill=PAL_TEXTO_SUAVE,
    )
    y += altura_nota - 8

    x_pos = layout["pos"]
    x_nome = layout["nome"]
    x_soma = layout["soma"]
    x_rod = layout.get("rod")
    centro_cab = y + ALTURA_TITULO_TABELA // 2

    draw.rectangle((MARGEM, y, largura - MARGEM, y + ALTURA_TITULO_TABELA), fill=PAL_CABECALHO)
    draw.text((x_pos + 38, centro_cab), "Pos", font=fontes["cab"], fill=PAL_TEXTO_CAB, anchor="mm")
    draw.text((x_nome + PADDING_NOME + extra, centro_cab), "Participante", font=fontes["cab"], fill=PAL_TEXTO_CAB, anchor="lm")
    for (rotulo, _), x_col, largura_col in zip(_COLUNAS_PONTOS, layout["pontos"], larguras_pontos, strict=True):
        draw.text((x_col + largura_col // 2, centro_cab), rotulo, font=fontes["cab"], fill=PAL_TEXTO_CAB, anchor="mm")
    draw.text((x_soma + 23, centro_cab), "Pts", font=fontes["cab"], fill=PAL_TEXTO_CAB, anchor="mm")
    if x_rod is not None:
        draw.text((x_rod + 26, centro_cab), "Rod", font=fontes["cab"], fill=PAL_TEXTO_CAB, anchor="mm")
    y += ALTURA_TITULO_TABELA

    for indice, linha in enumerate(classificacao):
        eh_lider = linha.posicao == 1
        cor = PAL_LINHA_LIDER if eh_lider else (PAL_LINHA_PAR if indice % 2 == 0 else PAL_LINHA_IMPAR)
        draw.rectangle((MARGEM, y, largura - MARGEM, y + altura_linha), fill=cor)
        draw.line((MARGEM, y + altura_linha, largura - MARGEM, y + altura_linha), fill=PAL_BORDA, width=1)

        nome = linha.participante.strip()
        cor_texto = PAL_TEXTO_LIDER if eh_lider else PAL_TEXTO
        centro_y = y + altura_linha // 2

        _desenhar_coluna_posicao(draw, x_pos, y, altura_linha, linha.posicao, None, fontes=fontes)

        ax = x_nome + PADDING_NOME
        ay = y + (altura_linha - AVATAR_TAMANHO) // 2
        desenhar_avatar(imagem, draw, ax, ay, AVATAR_TAMANHO, nome)
        draw.text(
            (ax + extra, centro_y),
            nome,
            font=fontes["linha"],
            fill=cor_texto,
            anchor="lm",
        )

        for (_, campo), x_col, largura_col in zip(_COLUNAS_PONTOS, layout["pontos"], larguras_pontos, strict=True):
            draw.text(
                (x_col + largura_col // 2, centro_y),
                str(getattr(linha, campo)),
                font=fontes["linha"],
                fill=cor_texto,
                anchor="mm",
            )
        draw.text((x_soma + 23, centro_y), str(linha.soma), font=fontes["linha"], fill=cor_texto, anchor="mm")
        if x_rod is not None:
            draw.text((x_rod + 26, centro_y), "—", font=fontes["var"], fill=PAL_TEXTO_SUAVE, anchor="mm")
        y += altura_linha

    rodape = (
        f"{len(classificacao)} participantes · miniatura {AVATAR_TAMANHO}px · dados atuais do bolão"
    )
    draw.text((MARGEM, y + 8), rodape, font=fontes["sub"], fill=PAL_TEXTO_SUAVE)
    return imagem


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Preview da classificação com miniaturas")
    parser.add_argument("--top", type=int, default=0, help="Limitar a N primeiros (0 = tabela inteira)")
    args = parser.parse_args()

    bolao = carregar_bolao()
    snap = carregar_snapshot(SNAPSHOT_JSON)
    baseline = set(snap["jogos_ids"]) if snap else set()
    classificacao = classificacao_ativa(bolao, jogos_ids_baseline=baseline)
    if not classificacao:
        classificacao = gerar_classificacao(bolao)

    from src.participantes_avatars import carregar_mapa_arquivos, resolver_foto_participante

    mapa = carregar_mapa_arquivos()
    com_foto = []
    sem_foto = []
    for linha in classificacao:
        nome = linha.participante.strip()
        if resolver_foto_participante(nome, mapa=mapa):
            com_foto.append(nome)
        else:
            sem_foto.append(nome)

    limite = args.top if args.top > 0 else None
    saida = DATA_DIR / "ultimo" / "png" / "classificacao_preview_avatars.png"
    saida.parent.mkdir(parents=True, exist_ok=True)
    renderizar_preview(classificacao, limite=limite).save(saida, format="PNG")
    print(f"Preview salvo em: {saida}")
    print(f"Com foto: {len(com_foto)}/{len(classificacao)}")
    if sem_foto:
        print("Sem foto (fallback iniciais):", ", ".join(sem_foto))


if __name__ == "__main__":
    main()
