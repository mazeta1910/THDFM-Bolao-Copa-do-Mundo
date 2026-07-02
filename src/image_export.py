from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.models import ClassificacaoLinha, ClassificacaoPremioLinha
from src.snapshot import formatar_mudanca_posicao, formatar_variacao
from src.participantes_avatars import (
    ALTURA_LINHA_AVATAR,
    AVATAR_TAMANHO,
    carregar_mapa_arquivos,
    desenhar_avatar,
    largura_extra_avatar,
)

# Paleta classificação (estilo planilha Excel THDFM)
PAL_FUNDO = (18, 18, 18)
PAL_LINHA_PAR = (24, 24, 24)
PAL_LINHA_IMPAR = (18, 18, 18)
PAL_CABECALHO = (42, 42, 42)
PAL_TEXTO_CAB = (255, 255, 255)
PAL_TEXTO = (255, 255, 255)
PAL_TEXTO_SUAVE = (170, 170, 170)
PAL_DESTAQUE = (255, 255, 255)
PAL_SECUNDARIO = (140, 140, 140)
PAL_POSITIVO = (120, 220, 140)
PAL_NEGATIVO = (220, 120, 120)
PAL_SETA_SUBIU = (74, 222, 128)
PAL_SETA_DESCEU = (248, 113, 113)
PAL_TITULO_LARANJA = (237, 125, 49)
PAL_BORDA = (55, 55, 55)
PAL_LINHA_LIDER = (58, 48, 14)
PAL_ZONA_LIDER = (184, 134, 11)
PAL_TEXTO_LIDER = (255, 232, 160)

# Zonas na coluna Pos (igual à planilha: 1-6, 7-13, 14-20, 21+)
PAL_ZONA_AZUL = (31, 78, 121)
PAL_ZONA_VERDE = (56, 118, 29)
PAL_ZONA_NEUTRA = (48, 48, 48)
PAL_ZONA_VERMELHA = (192, 80, 77)
ZONA_AZUL_ATE = 6
ZONA_VERDE_ATE = 13
ZONA_NEUTRA_ATE = 20

MARGEM = 24
ALTURA_LINHA = 34
ALTURA_TITULO_TABELA = 38
ALTURA_RODAPE = 34
LARGURA_COL_POS = 76
LARGURA_COL_PONTO = 52
LARGURA_COL_SOMA = 46
LARGURA_COL_VAR = 52
PADDING_NOME = 16
ESPACO_ENTRE_SECOES = 32

_cache_mapa_fotos: dict[str, str] | None = None


def _mapa_fotos_participantes() -> dict[str, str]:
    global _cache_mapa_fotos
    if _cache_mapa_fotos is None:
        _cache_mapa_fotos = carregar_mapa_arquivos()
    return _cache_mapa_fotos


def _altura_linha_tabela() -> int:
    return ALTURA_LINHA_AVATAR


def _extra_coluna_participante() -> int:
    return largura_extra_avatar()


def _desenhar_participante_com_avatar(
    imagem,
    draw,
    x_nome: int,
    y: int,
    altura_linha: int,
    nome: str,
    *,
    cor_texto: tuple[int, int, int],
    fonte,
) -> None:
    extra = _extra_coluna_participante()
    ax = x_nome + PADDING_NOME
    ay = y + (altura_linha - AVATAR_TAMANHO) // 2
    desenhar_avatar(
        imagem,
        draw,
        ax,
        ay,
        AVATAR_TAMANHO,
        nome,
        mapa=_mapa_fotos_participantes(),
    )
    draw.text(
        (ax + extra, y + altura_linha // 2),
        nome,
        font=fonte,
        fill=cor_texto,
        anchor="lm",
    )


_COLUNAS_PONTOS = (
    ("Placar", "placar"),
    ("Vencedor", "vencedor"),
    ("Gols casa", "gols_casa"),
    ("Gols fora", "gols_fora"),
)


def _carregar_fontes():
    from PIL import ImageFont

    tamanhos = {
        "titulo": 26,
        "secao": 20,
        "secao_grande": 24,
        "secao_menor": 15,
        "sub": 15,
        "cab": 14,
        "linha": 15,
        "var": 14,
    }
    candidatos = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    def buscar(negrito: bool) -> str | None:
        ordem = candidatos if negrito else candidatos[1::2] + candidatos[::2]
        for caminho in ordem:
            if Path(caminho).exists():
                return caminho
        return None

    def fonte(negrito: bool, tamanho: int):
        caminho = buscar(negrito)
        if caminho:
            return ImageFont.truetype(caminho, tamanho)
        return ImageFont.load_default()

    return {
        "titulo": fonte(True, tamanhos["titulo"]),
        "secao": fonte(True, tamanhos["secao"]),
        "secao_grande": fonte(True, tamanhos["secao_grande"]),
        "secao_menor": fonte(True, tamanhos["secao_menor"]),
        "sub": fonte(False, tamanhos["sub"]),
        "cab": fonte(True, tamanhos["cab"]),
        "linha": fonte(False, tamanhos["linha"]),
        "var": fonte(True, tamanhos["var"]),
        "confronto": fonte(False, 16),
        "crumb": fonte(False, 12),
    }


def _layout_classificacao(
    largura_nome: int,
    *,
    mostrar_rod: bool = True,
    fonte_cab=None,
) -> dict[str, int | list[int]]:
    from PIL import Image, ImageDraw

    x = MARGEM
    layout: dict[str, int | list[int]] = {"pos": x}
    x += LARGURA_COL_POS
    layout["nome"] = x
    x += largura_nome

    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    larguras_pontos: list[int] = []
    for rotulo, _ in _COLUNAS_PONTOS:
        if fonte_cab is not None:
            largura = int(draw.textlength(rotulo, font=fonte_cab)) + 16
            larguras_pontos.append(max(LARGURA_COL_PONTO, largura))
        else:
            larguras_pontos.append(LARGURA_COL_PONTO)
    layout["larguras_pontos"] = larguras_pontos
    layout["pontos"] = []
    for largura in larguras_pontos:
        layout["pontos"].append(x)
        x += largura
    layout["soma"] = x
    x += LARGURA_COL_SOMA
    if mostrar_rod:
        layout["rod"] = x
        x += LARGURA_COL_VAR
    layout["largura_total"] = x + MARGEM
    return layout


def exportar_classificacao_fase_png(
    classificacao: list[ClassificacaoLinha],
    path: str | Path,
    *,
    titulo: str,
    rodape: str,
    jogos_realizados: int,
    total_jogos: int,
) -> None:
    imagem = renderizar_classificacao_png(
        classificacao,
        jogos_realizados=jogos_realizados,
        total_jogos=total_jogos,
        variacoes={linha.participante.strip(): None for linha in classificacao},
        mudancas_posicao={linha.participante.strip(): None for linha in classificacao},
        titulo=titulo,
        rodape=rodape,
        mostrar_rod=False,
        rotulo_soma="Soma",
    )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    imagem.save(path, format="PNG")


def _largura_nome(classificacao: list[ClassificacaoLinha], fonte) -> int:
    nomes = [linha.participante.strip() for linha in classificacao]
    return _largura_nome_participantes(nomes, fonte)


def _largura_nome_participantes(nomes: list[str], fonte) -> int:
    from PIL import Image, ImageDraw

    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    largura = 180
    for nome in nomes:
        bbox = draw.textbbox((0, 0), nome, font=fonte)
        largura = max(largura, bbox[2] - bbox[0] + PADDING_NOME * 2)
    return min(largura + _extra_coluna_participante(), 340 + _extra_coluna_participante())


def _cor_fundo_zona_posicao(posicao: int) -> tuple[int, int, int]:
    if posicao == 1:
        return PAL_ZONA_LIDER
    if posicao <= ZONA_AZUL_ATE:
        return PAL_ZONA_AZUL
    if posicao <= ZONA_VERDE_ATE:
        return PAL_ZONA_VERDE
    if posicao <= ZONA_NEUTRA_ATE:
        return PAL_ZONA_NEUTRA
    return PAL_ZONA_VERMELHA


def _desenhar_coluna_posicao(
    draw,
    x_col: int,
    y_linha: int,
    altura_linha: int,
    posicao: int,
    delta_pos: int | None,
    *,
    fontes: dict,
) -> None:
    fundo = _cor_fundo_zona_posicao(posicao)
    draw.rectangle(
        (x_col, y_linha, x_col + LARGURA_COL_POS, y_linha + altura_linha),
        fill=fundo,
    )
    draw.line(
        (x_col + LARGURA_COL_POS, y_linha, x_col + LARGURA_COL_POS, y_linha + altura_linha),
        fill=PAL_BORDA,
        width=1,
    )

    centro_x = x_col + LARGURA_COL_POS // 2
    centro_y = y_linha + altura_linha // 2
    cor_numero = (28, 20, 0) if posicao == 1 else PAL_TEXTO
    texto_mudanca = formatar_mudanca_posicao(delta_pos)
    if not texto_mudanca:
        draw.text(
            (centro_x, centro_y),
            str(posicao),
            font=fontes["linha"],
            fill=cor_numero,
            anchor="mm",
        )
        return

    texto_pos = str(posicao)
    espaco = 4
    largura_pos = draw.textlength(texto_pos, font=fontes["linha"])
    largura_mudanca = draw.textlength(texto_mudanca, font=fontes["var"])
    largura_total = largura_pos + espaco + largura_mudanca
    x_inicio = centro_x - largura_total / 2

    draw.text(
        (x_inicio, centro_y),
        texto_pos,
        font=fontes["linha"],
        fill=cor_numero,
        anchor="lm",
    )
    if delta_pos is not None and delta_pos > 0:
        cor_mudanca = PAL_SETA_SUBIU
    elif delta_pos is not None and delta_pos < 0:
        cor_mudanca = PAL_SETA_DESCEU
    else:
        cor_mudanca = PAL_SECUNDARIO
    draw.text(
        (x_inicio + largura_pos + espaco, centro_y),
        texto_mudanca,
        font=fontes["var"],
        fill=cor_mudanca,
        anchor="lm",
    )


def exportar_classificacao_png(
    classificacao: list[ClassificacaoLinha],
    path: str | Path,
    *,
    jogos_realizados: int,
    total_jogos: int,
    variacoes: dict[str, int | None],
    mudancas_posicao: dict[str, int | None],
    jogos_novos: list[str] | None = None,
) -> None:
    imagem = renderizar_classificacao_png(
        classificacao,
        jogos_realizados=jogos_realizados,
        total_jogos=total_jogos,
        variacoes=variacoes,
        mudancas_posicao=mudancas_posicao,
        jogos_novos=jogos_novos,
    )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    imagem.save(path, format="PNG")


def renderizar_classificacao_png(
    classificacao: list[ClassificacaoLinha],
    *,
    jogos_realizados: int,
    total_jogos: int,
    variacoes: dict[str, int | None],
    mudancas_posicao: dict[str, int | None],
    jogos_novos: list[str] | None = None,
    titulo: str = "B) RESULTADOS DOS JOGOS",
    rodape: str | None = None,
    omitir_rodape: bool = False,
    mostrar_rod: bool = True,
    rotulo_soma: str = "Pts",
    margem_superior: int = MARGEM,
    fonte_titulo: str = "sub",
    altura_titulo: int = 28,
):
    from PIL import Image, ImageDraw

    fontes = _carregar_fontes()
    extra_nome = _extra_coluna_participante()
    altura_linha = _altura_linha_tabela()
    largura_nome = _largura_nome(classificacao, fontes["linha"])
    layout = _layout_classificacao(largura_nome, mostrar_rod=mostrar_rod, fonte_cab=fontes["cab"])
    largura = layout["largura_total"]
    larguras_pontos = layout["larguras_pontos"]

    linhas_jogos = 0
    if jogos_novos:
        linhas_jogos = min(len(jogos_novos), 3)

    altura = (
        margem_superior
        + altura_titulo
        + linhas_jogos * 22
        + (4 if linhas_jogos else 0)
        + ALTURA_TITULO_TABELA
        + altura_linha * len(classificacao)
        + (0 if omitir_rodape else ALTURA_RODAPE)
        + MARGEM
    )

    imagem = Image.new("RGB", (largura, altura), PAL_FUNDO)
    draw = ImageDraw.Draw(imagem)

    y = margem_superior
    draw.text(
        (MARGEM, y),
        titulo,
        font=fontes[fonte_titulo],
        fill=PAL_TITULO_LARANJA,
    )
    y += altura_titulo
    if jogos_novos:
        for texto in jogos_novos[:3]:
            draw.text((MARGEM, y), texto, font=fontes["sub"], fill=PAL_TEXTO_SUAVE)
            y += 22
        y += 4

    x_pos = layout["pos"]
    x_nome = layout["nome"]
    x_soma = layout["soma"]
    x_rod = layout.get("rod")
    centro_cab = y + ALTURA_TITULO_TABELA // 2

    draw.rectangle((MARGEM, y, largura - MARGEM, y + ALTURA_TITULO_TABELA), fill=PAL_CABECALHO)
    draw.text(
        (x_pos + LARGURA_COL_POS // 2, centro_cab),
        "Pos",
        font=fontes["cab"],
        fill=PAL_TEXTO_CAB,
        anchor="mm",
    )
    draw.text(
        (x_nome + PADDING_NOME + extra_nome, centro_cab),
        "Participante",
        font=fontes["cab"],
        fill=PAL_TEXTO_CAB,
        anchor="lm",
    )
    for (rotulo, _), x_col, largura_col in zip(
        _COLUNAS_PONTOS, layout["pontos"], larguras_pontos, strict=True
    ):
        draw.text(
            (x_col + largura_col // 2, centro_cab),
            rotulo,
            font=fontes["cab"],
            fill=PAL_TEXTO_CAB,
            anchor="mm",
        )
    draw.text(
        (x_soma + LARGURA_COL_SOMA // 2, centro_cab),
        rotulo_soma,
        font=fontes["cab"],
        fill=PAL_TEXTO_CAB,
        anchor="mm",
    )
    if mostrar_rod and x_rod is not None:
        draw.text(
            (x_rod + LARGURA_COL_VAR // 2, centro_cab),
            "Rod",
            font=fontes["cab"],
            fill=PAL_TEXTO_CAB,
            anchor="mm",
        )
    y += ALTURA_TITULO_TABELA

    for indice, linha in enumerate(classificacao):
        eh_lider = linha.posicao == 1
        if eh_lider:
            cor = PAL_LINHA_LIDER
        else:
            cor = PAL_LINHA_PAR if indice % 2 == 0 else PAL_LINHA_IMPAR
        draw.rectangle((MARGEM, y, largura - MARGEM, y + altura_linha), fill=cor)
        draw.line((MARGEM, y + altura_linha, largura - MARGEM, y + altura_linha), fill=PAL_BORDA, width=1)

        chave = linha.participante.strip()
        variacao = variacoes.get(chave)
        texto_var = formatar_variacao(variacao)
        delta_pos = mudancas_posicao.get(chave)
        cor_texto = PAL_TEXTO_LIDER if eh_lider else PAL_TEXTO

        centro_y = y + altura_linha // 2
        _desenhar_coluna_posicao(
            draw,
            x_pos,
            y,
            altura_linha,
            linha.posicao,
            delta_pos,
            fontes=fontes,
        )
        _desenhar_participante_com_avatar(
            imagem,
            draw,
            x_nome,
            y,
            altura_linha,
            chave,
            cor_texto=cor_texto,
            fonte=fontes["linha"],
        )
        for (_, campo), x_col, largura_col in zip(
            _COLUNAS_PONTOS, layout["pontos"], larguras_pontos, strict=True
        ):
            valor = getattr(linha, campo)
            draw.text(
                (x_col + largura_col // 2, centro_y),
                str(valor),
                font=fontes["linha"],
                fill=cor_texto,
                anchor="mm",
            )
        draw.text(
            (x_soma + LARGURA_COL_SOMA // 2, centro_y),
            str(linha.soma),
            font=fontes["linha"],
            fill=cor_texto,
            anchor="mm",
        )

        if mostrar_rod and x_rod is not None:
            if variacao is None:
                cor_var = PAL_SECUNDARIO
            elif variacao > 0:
                cor_var = PAL_POSITIVO
            elif variacao < 0:
                cor_var = PAL_NEGATIVO
            else:
                cor_var = PAL_SECUNDARIO

            draw.text(
                (x_rod + LARGURA_COL_VAR // 2, centro_y),
                texto_var,
                font=fontes["var"],
                fill=cor_var,
                anchor="mm",
            )
        y += altura_linha

    if not omitir_rodape:
        texto_rodape = (
            rodape
            if rodape is not None
            else "Premio B: metade do premio | Rod = jogos novos | Mata-mata conforme fase"
        )
        draw.rectangle((MARGEM, y, largura - MARGEM, y + ALTURA_RODAPE), fill=PAL_FUNDO)
        draw.text(
            (MARGEM + 8, y + ALTURA_RODAPE // 2),
            texto_rodape,
            font=fontes["sub"],
            fill=PAL_TEXTO_SUAVE,
            anchor="lm",
        )

    return imagem


def renderizar_classificacao_resumida_png(
    classificacao: list[ClassificacaoLinha],
    *,
    titulo: str,
):
    from PIL import Image, ImageDraw

    fontes = _carregar_fontes()
    extra_nome = _extra_coluna_participante()
    altura_linha = _altura_linha_tabela()
    largura_nome = _largura_nome(classificacao, fontes["linha"])
    largura_col_pts = 52
    largura = MARGEM + LARGURA_COL_POS + largura_nome + largura_col_pts + MARGEM
    altura = (
        MARGEM + 28 + ALTURA_TITULO_TABELA + altura_linha * len(classificacao) + MARGEM
    )
    imagem = Image.new("RGB", (largura, altura), PAL_FUNDO)
    draw = ImageDraw.Draw(imagem)
    y = MARGEM
    draw.text((MARGEM, y), titulo, font=fontes["sub"], fill=PAL_TITULO_LARANJA)
    y += 28
    x_pos = MARGEM
    x_nome = x_pos + LARGURA_COL_POS
    x_pts = x_nome + largura_nome
    centro_cab = y + ALTURA_TITULO_TABELA // 2
    draw.rectangle((MARGEM, y, largura - MARGEM, y + ALTURA_TITULO_TABELA), fill=PAL_CABECALHO)
    for rotulo, x_col, anchor in (
        ("Pos", x_pos + LARGURA_COL_POS // 2, "mm"),
        ("Participante", x_nome + PADDING_NOME + extra_nome, "lm"),
        ("Pts", x_pts + largura_col_pts // 2, "mm"),
    ):
        draw.text((x_col, centro_cab), rotulo, font=fontes["cab"], fill=PAL_TEXTO_CAB, anchor=anchor)
    y += ALTURA_TITULO_TABELA
    for indice, linha in enumerate(classificacao):
        cor = PAL_LINHA_LIDER if linha.posicao == 1 else (
            PAL_LINHA_PAR if indice % 2 == 0 else PAL_LINHA_IMPAR
        )
        draw.rectangle((MARGEM, y, largura - MARGEM, y + altura_linha), fill=cor)
        centro_y = y + altura_linha // 2
        nome = linha.participante.strip()
        draw.text((x_pos + LARGURA_COL_POS // 2, centro_y), str(linha.posicao), font=fontes["linha"], fill=PAL_TEXTO, anchor="mm")
        _desenhar_participante_com_avatar(
            imagem,
            draw,
            x_nome,
            y,
            altura_linha,
            nome,
            cor_texto=PAL_TEXTO,
            fonte=fontes["linha"],
        )
        draw.text((x_pts + largura_col_pts // 2, centro_y), str(linha.soma), font=fontes["linha"], fill=PAL_TEXTO, anchor="mm")
        y += altura_linha
    return imagem


def renderizar_premio_a_png(
    classificacao: list[ClassificacaoPremioLinha],
    *,
    cravadura_ativa: bool = False,
):
    from PIL import Image, ImageDraw

    fontes = _carregar_fontes()
    extra_nome = _extra_coluna_participante()
    altura_linha = _altura_linha_tabela()
    nomes = [linha.participante.strip() for linha in classificacao]
    largura_nome = _largura_nome_participantes(nomes, fontes["linha"])
    largura_col = 52
    largura = MARGEM + LARGURA_COL_POS + largura_nome + largura_col * 3 + MARGEM
    altura = (
        MARGEM
        + 28
        + ALTURA_TITULO_TABELA
        + altura_linha * len(classificacao)
        + ALTURA_RODAPE
        + MARGEM
    )

    imagem = Image.new("RGB", (largura, altura), PAL_FUNDO)
    draw = ImageDraw.Draw(imagem)
    y = MARGEM
    draw.text(
        (MARGEM, y),
        "A) CRAVADURA E GRUPOS",
        font=fontes["sub"],
        fill=PAL_TITULO_LARANJA,
    )
    y += 28

    x_pos = MARGEM
    x_nome = x_pos + LARGURA_COL_POS
    x_grp = x_nome + largura_nome
    x_crav = x_grp + largura_col
    x_pts = x_crav + largura_col
    centro_cab = y + ALTURA_TITULO_TABELA // 2

    draw.rectangle((MARGEM, y, largura - MARGEM, y + ALTURA_TITULO_TABELA), fill=PAL_CABECALHO)
    for rotulo, x_col in (
        ("Pos", x_pos + LARGURA_COL_POS // 2),
        ("Participante", x_nome + PADDING_NOME + extra_nome),
        ("Grp", x_grp + largura_col // 2),
        ("Crav", x_crav + largura_col // 2),
        ("Pts", x_pts + largura_col // 2),
    ):
        anchor = "mm" if rotulo != "Participante" else "lm"
        draw.text((x_col, centro_cab), rotulo, font=fontes["cab"], fill=PAL_TEXTO_CAB, anchor=anchor)
    y += ALTURA_TITULO_TABELA

    for indice, linha in enumerate(classificacao):
        cor = PAL_LINHA_LIDER if linha.posicao == 1 else (
            PAL_LINHA_PAR if indice % 2 == 0 else PAL_LINHA_IMPAR
        )
        draw.rectangle((MARGEM, y, largura - MARGEM, y + altura_linha), fill=cor)
        centro_y = y + altura_linha // 2
        nome = linha.participante.strip()
        draw.text((x_pos + LARGURA_COL_POS // 2, centro_y), str(linha.posicao), font=fontes["linha"], fill=PAL_TEXTO, anchor="mm")
        _desenhar_participante_com_avatar(
            imagem,
            draw,
            x_nome,
            y,
            altura_linha,
            nome,
            cor_texto=PAL_TEXTO,
            fonte=fontes["linha"],
        )
        draw.text((x_grp + largura_col // 2, centro_y), str(linha.grupos), font=fontes["linha"], fill=PAL_TEXTO, anchor="mm")
        draw.text((x_crav + largura_col // 2, centro_y), str(linha.cravadura), font=fontes["linha"], fill=PAL_TEXTO, anchor="mm")
        draw.text((x_pts + largura_col // 2, centro_y), str(linha.soma), font=fontes["linha"], fill=PAL_TEXTO, anchor="mm")
        y += altura_linha

    draw.rectangle((MARGEM, y, largura - MARGEM, y + ALTURA_RODAPE), fill=PAL_FUNDO)
    draw.text(
        (MARGEM + 8, y + ALTURA_RODAPE // 2),
        "Premio A | Grp 10/time | Crav "
        + ("ativa" if cravadura_ativa else "aguardando REAL OFICIAL"),
        font=fontes["sub"],
        fill=PAL_TEXTO_SUAVE,
        anchor="lm",
    )
    return imagem


def exportar_premio_a_png(
    classificacao: list[ClassificacaoPremioLinha],
    path: str | Path,
    *,
    cravadura_ativa: bool = False,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    renderizar_premio_a_png(classificacao, cravadura_ativa=cravadura_ativa).save(path, format="PNG")


def combinar_imagens_vertical(imagens: list, *, espaco: int = ESPACO_ENTRE_SECOES):
    from PIL import Image

    if not imagens:
        raise ValueError("Nenhuma imagem para combinar.")

    largura = max(imagem.width for imagem in imagens)
    altura = sum(imagem.height for imagem in imagens) + espaco * max(0, len(imagens) - 1)
    canvas = Image.new("RGB", (largura, altura), PAL_FUNDO)
    y = 0
    for indice, imagem in enumerate(imagens):
        x = (largura - imagem.width) // 2
        canvas.paste(imagem, (x, y))
        y += imagem.height
        if indice < len(imagens) - 1:
            y += espaco
    return canvas


ALTURA_BLOCO_JOGO = 24
ESPACO_ENTRE_COLUNAS = 16
LARGURA_NOME_COL = 200
LARGURA_COL_PALPITE = 80
LARGURA_COL_PEN_PALPITE = 88
LARGURA_COL_PTS_PALPITE = 40
LARGURA_MIN_JOGO = 108


def _jogo_mata_mata_palpites(jogo) -> bool:
    from src.scoring import FASE_GRUPOS_MAX

    return jogo.id > FASE_GRUPOS_MAX


def _mapa_palpites_por_nome(bloco) -> dict[str, object]:
    return {linha.participante.strip(): linha for linha in bloco.linhas}


def _participantes_alinhados(blocos) -> list[str]:
    nomes = {linha.participante.strip() for bloco in blocos for linha in bloco.linhas}
    return sorted(nomes, key=str.lower)


def _largura_nome_participantes(participantes: list[str], fonte) -> int:
    from PIL import Image, ImageDraw

    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    largura = LARGURA_NOME_COL
    for nome in participantes:
        largura = max(largura, int(draw.textlength(nome, font=fonte)) + PADDING_NOME * 2)
    return min(largura, 280)


def _largura_coluna_jogo(bloco, fontes: dict | None = None) -> int:
    from src.bandeiras_img import largura_confronto

    largura = LARGURA_COL_PALPITE
    if _jogo_mata_mata_palpites(bloco.jogo):
        largura += LARGURA_COL_PEN_PALPITE
    if bloco.jogo.realizado:
        largura += LARGURA_COL_PTS_PALPITE

    if fontes is not None:
        from PIL import Image, ImageDraw

        draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        largura_bandeiras = largura_confronto(fontes["confronto"])
        largura_rotulo = int(draw.textlength("Palpite", font=fontes["cab"])) + 16
        if _jogo_mata_mata_palpites(bloco.jogo):
            largura_rotulo += LARGURA_COL_PEN_PALPITE
        largura = max(largura, largura_bandeiras, largura_rotulo, LARGURA_MIN_JOGO)

    return largura


def _encurtar_texto(draw, texto: str, fonte, largura_max: int) -> str:
    resultado = texto
    while len(resultado) > 1 and draw.textlength(resultado, font=fonte) > largura_max:
        resultado = resultado[:-2] + "."
    return resultado


def _centros_coluna_jogo(
    x_atual: int,
    largura_col: int,
    jogo,
) -> tuple[int, int | None, int | None]:
    tem_pen = _jogo_mata_mata_palpites(jogo)
    realizado = jogo.realizado
    largura_bloco = LARGURA_COL_PALPITE
    if tem_pen:
        largura_bloco += LARGURA_COL_PEN_PALPITE
    if realizado:
        largura_bloco += LARGURA_COL_PTS_PALPITE
    x_bloco = x_atual + (largura_col - largura_bloco) // 2
    x_pal = x_bloco + LARGURA_COL_PALPITE // 2
    x_pen = None
    if tem_pen:
        x_pen = x_bloco + LARGURA_COL_PALPITE + LARGURA_COL_PEN_PALPITE // 2
    x_pts = None
    if realizado:
        offset_pts = LARGURA_COL_PALPITE + (LARGURA_COL_PEN_PALPITE if tem_pen else 0)
        x_pts = x_bloco + offset_pts + LARGURA_COL_PTS_PALPITE // 2
    return x_pal, x_pen, x_pts


def exportar_palpites_png(blocos, path: str | Path) -> None:
    from PIL import Image, ImageDraw

    from src.bandeiras import titulo_jogo_bandeiras
    from src.bandeiras_img import ALTURA_BANDEIRA, colar_confronto
    from src.palpites_view import _resultado_jogo

    if not blocos:
        raise ValueError("Nenhum jogo informado para exportar palpites.")

    fontes = _carregar_fontes()
    participantes = _participantes_alinhados(blocos)
    largura_nome = _largura_nome_participantes(participantes, fontes["linha"])
    larguras_jogos = [_largura_coluna_jogo(bloco, fontes) for bloco in blocos]
    largura_jogos = sum(larguras_jogos) + max(0, len(blocos) - 1) * ESPACO_ENTRE_COLUNAS
    largura = MARGEM * 2 + largura_nome + ESPACO_ENTRE_COLUNAS + largura_jogos

    tem_resultado = any(bloco.jogo.realizado for bloco in blocos)
    altura_bandeiras = ALTURA_BANDEIRA + 10
    altura_titulos_jogos = 22 + altura_bandeiras + (20 if tem_resultado else 0)
    altura = (
        MARGEM
        + altura_titulos_jogos
        + ALTURA_TITULO_TABELA
        + ALTURA_LINHA * len(participantes)
        + MARGEM
    )

    imagem = Image.new("RGB", (largura, altura), PAL_FUNDO)
    draw = ImageDraw.Draw(imagem)
    y = MARGEM
    x_nome = MARGEM
    x_jogos = x_nome + largura_nome + ESPACO_ENTRE_COLUNAS
    x_atual = x_jogos

    for bloco, largura_col in zip(blocos, larguras_jogos):
        titulo, _ = titulo_jogo_bandeiras(
            bloco.jogo.id, bloco.jogo.casa, bloco.jogo.fora
        )
        centro = x_atual + largura_col // 2
        draw.text((centro, y), titulo, font=fontes["sub"], fill=PAL_TEXTO_SUAVE, anchor="mm")
        colar_confronto(
            imagem,
            centro,
            y + 22 + ALTURA_BANDEIRA // 2,
            bloco.jogo.casa,
            bloco.jogo.fora,
            fonte_x=fontes["confronto"],
            cor_x=PAL_TEXTO,
        )
        resultado = _resultado_jogo(bloco.jogo)
        if resultado:
            draw.text(
                (centro, y + 22 + altura_bandeiras),
                resultado,
                font=fontes["sub"],
                fill=PAL_TEXTO_SUAVE,
                anchor="mm",
            )
        x_atual += largura_col + ESPACO_ENTRE_COLUNAS

    y += altura_titulos_jogos

    draw.rectangle((MARGEM, y, largura - MARGEM, y + ALTURA_TITULO_TABELA), fill=PAL_CABECALHO)
    draw.text(
        (x_nome + PADDING_NOME, y + ALTURA_TITULO_TABELA // 2),
        "Participante",
        font=fontes["cab"],
        fill=PAL_TEXTO_CAB,
        anchor="lm",
    )

    x_atual = x_jogos
    for bloco, largura_col in zip(blocos, larguras_jogos):
        x_pal, x_pen, x_pts = _centros_coluna_jogo(x_atual, largura_col, bloco.jogo)
        draw.text(
            (x_pal, y + ALTURA_TITULO_TABELA // 2),
            "Palpite",
            font=fontes["cab"],
            fill=PAL_TEXTO_CAB,
            anchor="mm",
        )
        if x_pen is not None:
            draw.text(
                (x_pen, y + ALTURA_TITULO_TABELA // 2),
                "Pen.",
                font=fontes["cab"],
                fill=PAL_TEXTO_CAB,
                anchor="mm",
            )
        if x_pts is not None:
            draw.text(
                (x_pts, y + ALTURA_TITULO_TABELA // 2),
                "Pts",
                font=fontes["cab"],
                fill=PAL_TEXTO_CAB,
                anchor="mm",
            )
        x_atual += largura_col + ESPACO_ENTRE_COLUNAS

    y += ALTURA_TITULO_TABELA
    mapas = [_mapa_palpites_por_nome(bloco) for bloco in blocos]

    for indice, nome in enumerate(participantes):
        cor = PAL_LINHA_PAR if indice % 2 == 0 else PAL_LINHA_IMPAR
        draw.rectangle((MARGEM, y, largura - MARGEM, y + ALTURA_LINHA), fill=cor)

        nome_exibicao = _encurtar_texto(
            draw, nome, fontes["linha"], largura_nome - PADDING_NOME * 2
        )
        draw.text(
            (x_nome + PADDING_NOME, y + ALTURA_LINHA // 2),
            nome_exibicao,
            font=fontes["linha"],
            fill=PAL_TEXTO,
            anchor="lm",
        )

        x_atual = x_jogos
        for bloco, mapa, largura_col in zip(blocos, mapas, larguras_jogos):
            linha = mapa[nome]
            jogo = bloco.jogo
            x_pal, x_pen, x_pts = _centros_coluna_jogo(x_atual, largura_col, jogo)

            placar_exato = (
                jogo.realizado
                and linha.palpite_casa == jogo.gols_casa
                and linha.palpite_fora == jogo.gols_fora
            )
            cor_palpite = PAL_DESTAQUE if placar_exato else PAL_TEXTO
            draw.text(
                (x_pal, y + ALTURA_LINHA // 2),
                linha.placar_texto,
                font=fontes["linha"],
                fill=cor_palpite,
                anchor="mm",
            )

            if x_pen is not None:
                mostrar_pen = linha.palpite_casa == linha.palpite_fora
                pen_texto = (
                    _encurtar_texto(
                        draw,
                        linha.penaltis_texto,
                        fontes["linha"],
                        LARGURA_COL_PEN_PALPITE - 8,
                    )
                    if mostrar_pen
                    else "-"
                )
                draw.text(
                    (x_pen, y + ALTURA_LINHA // 2),
                    pen_texto,
                    font=fontes["linha"],
                    fill=PAL_TEXTO_SUAVE
                    if mostrar_pen and linha.vencedor_penaltis
                    else PAL_SECUNDARIO,
                    anchor="mm",
                )

            if x_pts is not None:
                pontos = "-" if linha.pontos is None else str(linha.pontos)
                if linha.pontos == 5:
                    cor_pts = PAL_DESTAQUE
                elif linha.pontos and linha.pontos > 0:
                    cor_pts = PAL_TEXTO
                else:
                    cor_pts = PAL_SECUNDARIO
                draw.text(
                    (x_pts, y + ALTURA_LINHA // 2),
                    pontos,
                    font=fontes["var"],
                    fill=cor_pts,
                    anchor="mm",
                )
            x_atual += largura_col + ESPACO_ENTRE_COLUNAS

        y += ALTURA_LINHA

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    imagem.save(path, format="PNG")


LARGURA_COL_GOL = 40
LARGURA_COL_X = 28
LARGURA_COL_QUESITO = 100
LARGURA_COL_VENC = 88
ESPACO_BLOCO_JOGO = 28

COR_QUESITO_PLACAR = (160, 120, 20)
COR_QUESITO_PARCIAL = (45, 95, 170)
COR_QUESITO_NADA = (140, 45, 45)
COR_VENC_ACERTOU = (40, 130, 70)
COR_VENC_ERROU = (140, 45, 45)
COR_LINHA_PLACAR = (45, 45, 45)


def _cor_categoria(categoria: str | None) -> tuple[int, int, int]:
    if categoria == "Placar":
        return COR_QUESITO_PLACAR
    if categoria in {"Gols Casa", "Gols fora"}:
        return COR_QUESITO_PARCIAL
    return COR_QUESITO_NADA


def _cor_vencedor(acertou: bool | None) -> tuple[int, int, int]:
    if acertou:
        return COR_VENC_ACERTOU
    return COR_VENC_ERROU


@dataclass(frozen=True)
class ColunaJogoProvisorio:
    x: int
    largura: int
    largura_gol: int
    largura_venc: int

    @property
    def largura_gols(self) -> int:
        return self.largura_gol * 2 + LARGURA_COL_X

    @property
    def largura_conteudo(self) -> int:
        return self.largura_gols + LARGURA_COL_QUESITO + self.largura_venc

    @property
    def x_gol_casa(self) -> int:
        return self.x

    @property
    def x_sep(self) -> int:
        return self.x + self.largura_gol

    @property
    def x_gol_fora(self) -> int:
        return self.x_sep + LARGURA_COL_X

    @property
    def x_quesito(self) -> int:
        return self.x_gol_fora + self.largura_gol

    @property
    def x_venc(self) -> int:
        return self.x_quesito + LARGURA_COL_QUESITO


def _layouts_jogos_provisorio(blocos, fontes, x_jogos: int) -> list[ColunaJogoProvisorio]:
    from PIL import Image, ImageDraw

    from src.bandeiras_img import largura_confronto
    from src.palpites_view import rotulo_vencedor_jogo

    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    layouts: list[ColunaJogoProvisorio] = []
    x = x_jogos

    for bloco in blocos:
        jogo = bloco.jogo
        largura_gol = max(
            LARGURA_COL_GOL,
            int(draw.textlength("99", font=fontes["linha"])) + 12,
        )
        rotulo = rotulo_vencedor_jogo(jogo)
        largura_venc = max(
            LARGURA_COL_VENC,
            int(draw.textlength(rotulo, font=fontes["linha"])) + 16,
        )
        largura_gols = largura_gol * 2 + LARGURA_COL_X
        largura_conteudo = largura_gols + LARGURA_COL_QUESITO + largura_venc
        largura = max(largura_conteudo, largura_confronto(fontes["confronto"]) + 8)
        layouts.append(
            ColunaJogoProvisorio(
                x=x,
                largura=largura,
                largura_gol=largura_gol,
                largura_venc=largura_venc,
            )
        )
        x += largura + ESPACO_ENTRE_COLUNAS

    return layouts


def _desenhar_celula(
    draw,
    x: int,
    y: int,
    largura: int,
    altura: int,
    texto: str,
    *,
    fundo: tuple[int, int, int] | None,
    fonte,
    cor_texto=(255, 255, 255),
) -> None:
    if fundo is not None:
        draw.rectangle((x, y, x + largura, y + altura), fill=fundo)
    draw.text(
        (x + largura // 2, y + altura // 2),
        texto,
        font=fonte,
        fill=cor_texto,
        anchor="mm",
    )


def _desenhar_cabecalho_jogo_provisorio(
    draw,
    _bloco,
    layout: ColunaJogoProvisorio,
    y: int,
    *,
    fontes,
) -> None:
    centro_palpite = layout.x_gol_casa + layout.largura_gols // 2
    draw.text(
        (centro_palpite, y + ALTURA_TITULO_TABELA // 2),
        "Palpite",
        font=fontes["cab"],
        fill=PAL_TEXTO_CAB,
        anchor="mm",
    )
    for texto, x, largura_cel in [
        ("Quesito", layout.x_quesito, LARGURA_COL_QUESITO),
        ("Vencedor", layout.x_venc, layout.largura_venc),
    ]:
        draw.text(
            (x + largura_cel // 2, y + ALTURA_TITULO_TABELA // 2),
            texto,
            font=fontes["cab"],
            fill=PAL_TEXTO_CAB,
            anchor="mm",
        )


def _desenhar_linha_placar_provisorio(
    draw,
    bloco,
    layout: ColunaJogoProvisorio,
    y: int,
    *,
    fontes,
) -> None:
    from src.palpites_view import rotulo_vencedor_jogo

    jogo = bloco.jogo
    _desenhar_celula(
        draw, layout.x_gol_casa, y, layout.largura_gol, ALTURA_LINHA, str(jogo.gols_casa),
        fundo=None, fonte=fontes["var"],
    )
    _desenhar_celula(draw, layout.x_sep, y, LARGURA_COL_X, ALTURA_LINHA, "x", fundo=None, fonte=fontes["linha"])
    _desenhar_celula(
        draw, layout.x_gol_fora, y, layout.largura_gol, ALTURA_LINHA, str(jogo.gols_fora),
        fundo=None, fonte=fontes["var"],
    )
    _desenhar_celula(
        draw, layout.x_quesito, y, LARGURA_COL_QUESITO, ALTURA_LINHA, "--",
        fundo=COR_LINHA_PLACAR, fonte=fontes["linha"],
    )
    rotulo = _encurtar_texto(
        draw, rotulo_vencedor_jogo(jogo), fontes["linha"], layout.largura_venc - 8
    )
    _desenhar_celula(
        draw, layout.x_venc, y, layout.largura_venc, ALTURA_LINHA, rotulo,
        fundo=COR_LINHA_PLACAR, fonte=fontes["linha"],
    )


def _desenhar_linha_participante_provisorio(
    draw,
    linha,
    layout: ColunaJogoProvisorio,
    y: int,
    *,
    fontes,
) -> None:
    _desenhar_celula(
        draw, layout.x_gol_casa, y, layout.largura_gol, ALTURA_LINHA, str(linha.palpite_casa),
        fundo=None, fonte=fontes["linha"],
    )
    _desenhar_celula(draw, layout.x_sep, y, LARGURA_COL_X, ALTURA_LINHA, "x", fundo=None, fonte=fontes["linha"])
    _desenhar_celula(
        draw, layout.x_gol_fora, y, layout.largura_gol, ALTURA_LINHA, str(linha.palpite_fora),
        fundo=None, fonte=fontes["linha"],
    )
    _desenhar_celula(
        draw, layout.x_quesito, y, LARGURA_COL_QUESITO, ALTURA_LINHA, linha.categoria or "-",
        fundo=_cor_categoria(linha.categoria), fonte=fontes["linha"],
    )
    _desenhar_celula(
        draw, layout.x_venc, y, layout.largura_venc, ALTURA_LINHA, linha.texto_vencedor or "-",
        fundo=_cor_vencedor(linha.acertou_vencedor), fonte=fontes["linha"],
    )


def exportar_palpites_provisorios_png(blocos, path: str | Path) -> None:
    imagem = renderizar_palpites_provisorios_png(blocos)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    imagem.save(path, format="PNG")


def renderizar_palpites_provisorios_png(
    blocos,
    *,
    mesclar_titulo_jogo: bool = False,
    margem_superior: int = MARGEM,
):
    from PIL import Image, ImageDraw

    from src.bandeiras import titulo_jogo_bandeiras
    from src.bandeiras_img import ALTURA_BANDEIRA, colar_confronto
    from src.palpites_view import participantes_ordenados_provisorio

    realizados = [bloco for bloco in blocos if bloco.jogo.realizado]
    if not realizados:
        raise ValueError("Nenhum jogo com placar provisorio para exportar.")

    fontes = _carregar_fontes()
    participantes = participantes_ordenados_provisorio(blocos)
    largura_nome = _largura_nome_participantes(participantes, fontes["linha"])
    largura_pts = LARGURA_COL_PTS_PALPITE
    x_nome = MARGEM
    x_jogos = x_nome + largura_nome + ESPACO_ENTRE_COLUNAS
    layouts = _layouts_jogos_provisorio(realizados, fontes, x_jogos)
    largura_jogos = sum(layout.largura for layout in layouts) + max(
        0, len(layouts) - 1
    ) * ESPACO_ENTRE_COLUNAS
    x_pts = x_jogos + largura_jogos + ESPACO_ENTRE_COLUNAS
    largura = (
        MARGEM * 2
        + largura_nome
        + ESPACO_ENTRE_COLUNAS
        + largura_jogos
        + ESPACO_ENTRE_COLUNAS
        + largura_pts
    )

    altura_bandeiras = ALTURA_BANDEIRA + 6
    altura_cabecalho_jogo = 22
    altura_titulos_jogos = altura_cabecalho_jogo + altura_bandeiras
    altura = (
        margem_superior
        + altura_titulos_jogos
        + ALTURA_TITULO_TABELA
        + ALTURA_LINHA
        + ALTURA_LINHA * len(participantes)
        + MARGEM
    )

    imagem = Image.new("RGB", (largura, altura), PAL_FUNDO)
    draw = ImageDraw.Draw(imagem)
    y = margem_superior

    for bloco, layout in zip(realizados, layouts):
        centro = layout.x + layout.largura // 2
        if mesclar_titulo_jogo:
            titulo = f"Palpites provisórios — Jogo {bloco.jogo.id}"
            cor_titulo = PAL_TITULO_LARANJA
            fonte_titulo = fontes["secao_menor"]
        else:
            titulo, _ = titulo_jogo_bandeiras(bloco.jogo.id, bloco.jogo.casa, bloco.jogo.fora)
            cor_titulo = PAL_TEXTO_SUAVE
            fonte_titulo = fontes["sub"]
        draw.text((centro, y), titulo, font=fonte_titulo, fill=cor_titulo, anchor="mm")
        colar_confronto(
            imagem,
            centro,
            y + altura_cabecalho_jogo + ALTURA_BANDEIRA // 2,
            bloco.jogo.casa,
            bloco.jogo.fora,
            fonte_x=fontes["confronto"],
            cor_x=PAL_TEXTO,
        )

    y += altura_titulos_jogos

    draw.rectangle((MARGEM, y, largura - MARGEM, y + ALTURA_TITULO_TABELA), fill=PAL_CABECALHO)
    draw.text(
        (x_nome + PADDING_NOME, y + ALTURA_TITULO_TABELA // 2),
        "Participante",
        font=fontes["cab"],
        fill=PAL_TEXTO_CAB,
        anchor="lm",
    )
    for bloco, layout in zip(realizados, layouts):
        _desenhar_cabecalho_jogo_provisorio(draw, bloco, layout, y, fontes=fontes)
    draw.text(
        (x_pts + largura_pts // 2, y + ALTURA_TITULO_TABELA // 2),
        "Pts",
        font=fontes["cab"],
        fill=PAL_TEXTO_CAB,
        anchor="mm",
    )

    y += ALTURA_TITULO_TABELA

    draw.rectangle((MARGEM, y, largura - MARGEM, y + ALTURA_LINHA), fill=COR_LINHA_PLACAR)
    draw.text(
        (x_nome + PADDING_NOME, y + ALTURA_LINHA // 2),
        "PLACAR",
        font=fontes["var"],
        fill=PAL_TEXTO,
        anchor="lm",
    )
    for bloco, layout in zip(realizados, layouts):
        _desenhar_linha_placar_provisorio(draw, bloco, layout, y, fontes=fontes)
    y += ALTURA_LINHA

    mapas = [_mapa_palpites_por_nome(bloco) for bloco in realizados]

    def _cor_total_pontos(total: int) -> tuple[int, int, int]:
        if total >= 8:
            return PAL_DESTAQUE
        if total > 0:
            return PAL_TEXTO
        return PAL_SECUNDARIO

    for indice, nome in enumerate(participantes):
        cor = PAL_LINHA_PAR if indice % 2 == 0 else PAL_LINHA_IMPAR
        draw.rectangle((MARGEM, y, largura - MARGEM, y + ALTURA_LINHA), fill=cor)
        nome_exibicao = _encurtar_texto(draw, nome, fontes["linha"], largura_nome - PADDING_NOME * 2)
        draw.text(
            (x_nome + PADDING_NOME, y + ALTURA_LINHA // 2),
            nome_exibicao,
            font=fontes["linha"],
            fill=PAL_TEXTO,
            anchor="lm",
        )
        total_pts = sum(mapa[nome].pontos or 0 for mapa in mapas)
        for layout, mapa in zip(layouts, mapas):
            _desenhar_linha_participante_provisorio(draw, mapa[nome], layout, y, fontes=fontes)
        draw.text(
            (x_pts + largura_pts // 2, y + ALTURA_LINHA // 2),
            str(total_pts),
            font=fontes["var"],
            fill=_cor_total_pontos(total_pts),
            anchor="mm",
        )
        y += ALTURA_LINHA

    return imagem



def combinar_imagens_horizontal(
    imagens: list,
    *,
    espaco: int = ESPACO_ENTRE_SECOES,
    alinhar_topo: bool = False,
):
    from PIL import Image

    if not imagens:
        raise ValueError("Nenhuma imagem para combinar.")

    largura = sum(imagem.width for imagem in imagens) + espaco * max(0, len(imagens) - 1)
    altura = max(imagem.height for imagem in imagens)
    canvas = Image.new("RGB", (largura, altura), PAL_FUNDO)
    x = 0
    for indice, imagem in enumerate(imagens):
        y = 0 if alinhar_topo else (altura - imagem.height) // 2
        canvas.paste(imagem, (x, y))
        x += imagem.width
        if indice < len(imagens) - 1:
            x += espaco
    return canvas


def _adicionar_breadcrumb(imagem, texto: str):
    from PIL import Image, ImageDraw

    faixa = 14
    fontes = _carregar_fontes()
    nova = Image.new("RGB", (imagem.width, imagem.height + faixa), PAL_FUNDO)
    nova.paste(imagem, (0, faixa))
    draw = ImageDraw.Draw(nova)
    draw.text(
        (MARGEM, faixa - 1),
        texto,
        font=fontes["crumb"],
        fill=PAL_TEXTO_SUAVE,
        anchor="lb",
    )
    return nova


_MARGEM_RODADA = 4
_ALTURA_TITULO_RODADA = 34


def exportar_rodada_completa_png(
    classificacao: list[ClassificacaoLinha],
    blocos,
    path: str | Path,
    *,
    jogos_realizados: int,
    total_jogos: int,
    variacoes: dict[str, int | None],
    mudancas_posicao: dict[str, int | None],
    jogos_novos: list[str] | None = None,
    breadcrumb: str | None = None,
) -> None:
    """Classificação geral + palpites provisórios lado a lado."""
    from src.share_options import BREADCRUMB_RODADA_PNG

    imagem_classificacao = renderizar_classificacao_png(
        classificacao,
        jogos_realizados=jogos_realizados,
        total_jogos=total_jogos,
        variacoes=variacoes,
        mudancas_posicao=mudancas_posicao,
        jogos_novos=jogos_novos,
        titulo="CLASSIFICAÇÃO GERAL",
        omitir_rodape=True,
        margem_superior=_MARGEM_RODADA,
        fonte_titulo="secao_grande",
        altura_titulo=_ALTURA_TITULO_RODADA,
    )
    imagem_provisorio = renderizar_palpites_provisorios_png(
        blocos,
        mesclar_titulo_jogo=True,
        margem_superior=_MARGEM_RODADA,
    )
    combinada = combinar_imagens_horizontal(
        [imagem_classificacao, imagem_provisorio],
        espaco=20,
        alinhar_topo=True,
    )
    combinada = _adicionar_breadcrumb(combinada, breadcrumb or BREADCRUMB_RODADA_PNG)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    combinada.save(path, format="PNG")
