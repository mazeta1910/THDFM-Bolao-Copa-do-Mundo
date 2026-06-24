from __future__ import annotations

from dataclasses import dataclass
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
        + ALTURA_SUBTITULO
        + linhas_jogos * 22
        + ALTURA_TITULO_TABELA
        + ALTURA_LINHA * len(classificacao)
        + MARGEM
    )

    imagem = Image.new("RGB", (largura, altura), PAL_FUNDO)
    draw = ImageDraw.Draw(imagem)

    y = MARGEM
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

    altura_bandeiras = ALTURA_BANDEIRA + 10
    altura_titulos_jogos = 22 + altura_bandeiras
    altura = (
        MARGEM
        + altura_titulos_jogos
        + ALTURA_TITULO_TABELA
        + ALTURA_LINHA
        + ALTURA_LINHA * len(participantes)
        + MARGEM
    )

    imagem = Image.new("RGB", (largura, altura), PAL_FUNDO)
    draw = ImageDraw.Draw(imagem)
    y = MARGEM

    for bloco, layout in zip(realizados, layouts):
        titulo, _ = titulo_jogo_bandeiras(bloco.jogo.id, bloco.jogo.casa, bloco.jogo.fora)
        centro = layout.x + layout.largura // 2
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

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    imagem.save(path, format="PNG")
