from __future__ import annotations

from pathlib import Path

from src.models import ClassificacaoLinha
from src.snapshot import formatar_mudanca_posicao, formatar_variacao

# Paleta preto e branco (classificação e palpites)
PAL_FUNDO = (0, 0, 0)
PAL_LINHA_PAR = (0, 0, 0)
PAL_LINHA_IMPAR = (22, 22, 22)
PAL_CABECALHO = (255, 255, 255)
PAL_TEXTO_CAB = (0, 0, 0)
PAL_TEXTO = (255, 255, 255)
PAL_TEXTO_SUAVE = (170, 170, 170)
PAL_DESTAQUE = (255, 255, 255)
PAL_SECUNDARIO = (120, 120, 120)
PAL_POSITIVO = (255, 255, 255)
PAL_NEGATIVO = (120, 120, 120)
PAL_SETA_SUBIU = (74, 222, 128)
PAL_SETA_DESCEU = (248, 113, 113)

MARGEM = 32
ALTURA_LINHA = 36
ALTURA_CABECALHO = 64
ALTURA_SUBTITULO = 36
ALTURA_TITULO_TABELA = 40
LARGURA_COL_POS = 76
LARGURA_COL_PTS = 56
LARGURA_COL_VAR = 64
PADDING_NOME = 16


def _carregar_fontes():
    from PIL import ImageFont

    tamanhos = {
        "titulo": 26,
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
        "sub": fonte(False, tamanhos["sub"]),
        "cab": fonte(True, tamanhos["cab"]),
        "linha": fonte(False, tamanhos["linha"]),
        "var": fonte(True, tamanhos["var"]),
        "confronto": fonte(False, 16),
    }


def _largura_nome(classificacao: list[ClassificacaoLinha], fonte) -> int:
    from PIL import Image, ImageDraw

    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    largura = 180
    for linha in classificacao:
        nome = linha.participante.strip()
        bbox = draw.textbbox((0, 0), nome, font=fonte)
        largura = max(largura, bbox[2] - bbox[0] + PADDING_NOME * 2)
    return min(largura, 340)


def _desenhar_coluna_posicao(
    draw,
    x_col: int,
    centro_y: int,
    posicao: int,
    delta_pos: int | None,
    *,
    fontes: dict,
    cor_pos: tuple[int, int, int],
) -> None:
    centro_x = x_col + LARGURA_COL_POS // 2
    texto_mudanca = formatar_mudanca_posicao(delta_pos)
    if not texto_mudanca:
        draw.text(
            (centro_x, centro_y),
            str(posicao),
            font=fontes["linha"],
            fill=cor_pos,
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
        fill=cor_pos,
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
    from PIL import Image, ImageDraw

    fontes = _carregar_fontes()
    largura_nome = _largura_nome(classificacao, fontes["linha"])
    largura = (
        MARGEM * 2
        + LARGURA_COL_POS
        + largura_nome
        + LARGURA_COL_PTS
        + LARGURA_COL_VAR
    )

    linhas_jogos = 0
    if jogos_novos:
        linhas_jogos = min(len(jogos_novos), 3)

    altura = (
        MARGEM
        + ALTURA_CABECALHO
        + ALTURA_SUBTITULO
        + linhas_jogos * 22
        + ALTURA_TITULO_TABELA
        + ALTURA_LINHA * len(classificacao)
        + MARGEM
    )

    imagem = Image.new("RGB", (largura, altura), PAL_FUNDO)
    draw = ImageDraw.Draw(imagem)

    y = MARGEM
    draw.rectangle(
        (MARGEM, y, largura - MARGEM, y + ALTURA_CABECALHO),
        fill=PAL_CABECALHO,
    )
    draw.text(
        (largura // 2, y + ALTURA_CABECALHO // 2),
        "CLASSIFICADURA BOLÃO",
        font=fontes["titulo"],
        fill=PAL_TEXTO_CAB,
        anchor="mm",
    )
    y += ALTURA_CABECALHO + 8

    draw.text(
        (MARGEM, y),
        f"Atualizada apos {jogos_realizados} de {total_jogos} jogos",
        font=fontes["sub"],
        fill=PAL_TEXTO_SUAVE,
    )
    y += ALTURA_SUBTITULO

    if jogos_novos:
        for texto in jogos_novos[:3]:
            draw.text((MARGEM, y), texto, font=fontes["sub"], fill=PAL_TEXTO_SUAVE)
            y += 22
        y += 4

    x_pos = MARGEM
    x_nome = x_pos + LARGURA_COL_POS
    x_pts = x_nome + largura_nome
    x_var = x_pts + LARGURA_COL_PTS

    draw.rectangle((MARGEM, y, largura - MARGEM, y + ALTURA_TITULO_TABELA), fill=PAL_CABECALHO)
    for texto, x, ancora in [
        ("Pos", x_pos + LARGURA_COL_POS // 2, "mm"),
        ("Participante", x_nome + PADDING_NOME, "lm"),
        ("Pts", x_pts + LARGURA_COL_PTS // 2, "mm"),
        ("Rodada", x_var + LARGURA_COL_VAR // 2, "mm"),
    ]:
        draw.text((x, y + ALTURA_TITULO_TABELA // 2), texto, font=fontes["cab"], fill=PAL_TEXTO_CAB, anchor=ancora)
    y += ALTURA_TITULO_TABELA

    for indice, linha in enumerate(classificacao):
        cor = PAL_LINHA_PAR if indice % 2 == 0 else PAL_LINHA_IMPAR
        draw.rectangle((MARGEM, y, largura - MARGEM, y + ALTURA_LINHA), fill=cor)

        chave = linha.participante.strip()
        variacao = variacoes.get(chave)
        texto_var = formatar_variacao(variacao)
        delta_pos = mudancas_posicao.get(chave)

        cor_pos = PAL_DESTAQUE if linha.posicao <= 3 else PAL_TEXTO
        centro_y = y + ALTURA_LINHA // 2
        _desenhar_coluna_posicao(
            draw,
            x_pos,
            centro_y,
            linha.posicao,
            delta_pos,
            fontes=fontes,
            cor_pos=cor_pos,
        )
        draw.text(
            (x_nome + PADDING_NOME, y + ALTURA_LINHA // 2),
            chave,
            font=fontes["linha"],
            fill=PAL_TEXTO,
            anchor="lm",
        )
        draw.text(
            (x_pts + LARGURA_COL_PTS // 2, y + ALTURA_LINHA // 2),
            str(linha.soma),
            font=fontes["linha"],
            fill=PAL_TEXTO,
            anchor="mm",
        )

        if variacao is None:
            cor_var = PAL_SECUNDARIO
        elif variacao > 0:
            cor_var = PAL_POSITIVO
        elif variacao < 0:
            cor_var = PAL_NEGATIVO
        else:
            cor_var = PAL_SECUNDARIO

        draw.text(
            (x_var + LARGURA_COL_VAR // 2, y + ALTURA_LINHA // 2),
            texto_var,
            font=fontes["var"],
            fill=cor_var,
            anchor="mm",
        )
        y += ALTURA_LINHA

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    imagem.save(path, format="PNG")


ALTURA_BLOCO_JOGO = 24
ESPACO_ENTRE_COLUNAS = 16
LARGURA_NOME_COL = 200
LARGURA_COL_PALPITE = 80
LARGURA_COL_PTS_PALPITE = 40
LARGURA_MIN_JOGO = 108


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
    if bloco.jogo.realizado:
        largura += LARGURA_COL_PTS_PALPITE

    if fontes is not None:
        from PIL import Image, ImageDraw

        draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        largura_bandeiras = largura_confronto(fontes["confronto"])
        largura_rotulo = int(draw.textlength("Palpite", font=fontes["cab"])) + 16
        largura = max(largura, largura_bandeiras, largura_rotulo, LARGURA_MIN_JOGO)

    return largura


def _encurtar_texto(draw, texto: str, fonte, largura_max: int) -> str:
    resultado = texto
    while len(resultado) > 1 and draw.textlength(resultado, font=fonte) > largura_max:
        resultado = resultado[:-2] + "."
    return resultado


def _centros_coluna_jogo(x_atual: int, largura_col: int, realizado: bool) -> tuple[int, int | None]:
    centro = x_atual + largura_col // 2
    if not realizado:
        return centro, None
    largura_bloco = LARGURA_COL_PALPITE + LARGURA_COL_PTS_PALPITE
    x_bloco = x_atual + (largura_col - largura_bloco) // 2
    x_pal = x_bloco + LARGURA_COL_PALPITE // 2
    x_pts = x_bloco + LARGURA_COL_PALPITE + LARGURA_COL_PTS_PALPITE // 2
    return x_pal, x_pts


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
        + ALTURA_CABECALHO
        + MARGEM
        + altura_titulos_jogos
        + ALTURA_TITULO_TABELA
        + ALTURA_LINHA * len(participantes)
        + MARGEM
    )

    imagem = Image.new("RGB", (largura, altura), PAL_FUNDO)
    draw = ImageDraw.Draw(imagem)
    y_topo = MARGEM

    draw.rectangle((MARGEM, y_topo, largura - MARGEM, y_topo + ALTURA_CABECALHO), fill=PAL_CABECALHO)
    draw.text(
        (largura // 2, y_topo + ALTURA_CABECALHO // 2),
        "PALPITES",
        font=fontes["titulo"],
        fill=PAL_TEXTO_CAB,
        anchor="mm",
    )

    y = y_topo + ALTURA_CABECALHO + MARGEM
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
        x_pal, x_pts = _centros_coluna_jogo(x_atual, largura_col, bloco.jogo.realizado)
        draw.text(
            (x_pal, y + ALTURA_TITULO_TABELA // 2),
            "Palpite",
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
            x_pal, x_pts = _centros_coluna_jogo(x_atual, largura_col, jogo.realizado)

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
