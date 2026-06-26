from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

from src.bandeiras import _chave_time

PONTOS_POR_ACERTO = 10
MAX_PONTOS_POR_GRUPO = 40
TOTAL_GRUPOS = 12
COLUNA_NOME_FORMS = "QUAL SEU NOME NA THDFM"
COLUNA_GRUPO_RE = re.compile(r"^GRUPO ([A-L]) \[(\d)\]$", re.IGNORECASE)
GRUPO_RE = re.compile(r"^GRUPO ([A-L])\s*;*$", re.IGNORECASE)


@dataclass
class RankingGruposLinha:
    posicao: int
    participante: str
    pontos: int
    acertos: int
    por_grupo: dict[str, int] = field(default_factory=dict)


@dataclass
class ResumoRankingGrupos:
    grupos_definidos: list[str]
    pontos_maximos: int
    participantes: int


def times_iguais(nome_a: str, nome_b: str) -> bool:
    return _chave_time(nome_a) == _chave_time(nome_b)


def carregar_classificacoes_reais(path: str | Path) -> dict[str, dict[int, str]]:
    path = Path(path)
    grupos: dict[str, dict[int, str]] = {}
    grupo_atual: str | None = None

    with path.open(encoding="utf-8-sig", newline="") as handle:
        for linha in handle:
            texto = linha.strip()
            if not texto:
                continue

            match_grupo = GRUPO_RE.match(texto.split(";")[0].strip())
            if match_grupo:
                grupo_atual = match_grupo.group(1).upper()
                grupos.setdefault(grupo_atual, {})
                continue

            partes = [parte.strip() for parte in texto.split(";")]
            if (
                grupo_atual
                and len(partes) >= 2
                and partes[0].isdigit()
                and partes[1]
            ):
                grupos[grupo_atual][int(partes[0])] = partes[1]

    return {grupo: posicoes for grupo, posicoes in grupos.items() if posicoes}


def carregar_palpites_grupos(path: str | Path) -> dict[str, dict[str, dict[int, str]]]:
    path = Path(path)
    palpites: dict[str, dict[str, dict[int, str]]] = {}

    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        colunas_grupo: dict[str, tuple[str, int]] = {}
        for coluna in reader.fieldnames or []:
            match = COLUNA_GRUPO_RE.match(coluna.strip())
            if match:
                colunas_grupo[coluna] = (match.group(1).upper(), int(match.group(2)))

        for row in reader:
            nome = (row.get(COLUNA_NOME_FORMS) or "").strip()
            if not nome:
                continue
            por_grupo: dict[str, dict[int, str]] = {}
            for coluna, (grupo, posicao) in colunas_grupo.items():
                time = (row.get(coluna) or "").strip()
                if not time:
                    continue
                por_grupo.setdefault(grupo, {})[posicao] = time
            palpites[nome] = por_grupo

    return palpites


def pontos_por_grupo(
    palpite_grupo: dict[int, str],
    real_grupo: dict[int, str],
) -> tuple[int, int]:
    pontos = 0
    acertos = 0
    for posicao, time_real in real_grupo.items():
        time_palpite = palpite_grupo.get(posicao)
        if time_palpite and times_iguais(time_palpite, time_real):
            pontos += PONTOS_POR_ACERTO
            acertos += 1
    return pontos, acertos


def calcular_pontos_participante(
    palpite: dict[str, dict[int, str]],
    reais: dict[str, dict[int, str]],
) -> tuple[int, int, dict[str, int]]:
    pontos_total = 0
    acertos_total = 0
    por_grupo: dict[str, int] = {}

    for grupo, real_grupo in reais.items():
        pontos, _ = pontos_por_grupo(palpite.get(grupo, {}), real_grupo)
        por_grupo[grupo] = pontos
        pontos_total += pontos
        acertos_total += pontos // PONTOS_POR_ACERTO

    return pontos_total, acertos_total, por_grupo


def gerar_ranking_grupos(
    reais_path: str | Path,
    palpites_path: str | Path,
) -> tuple[list[RankingGruposLinha], ResumoRankingGrupos]:
    reais = carregar_classificacoes_reais(reais_path)
    palpites = carregar_palpites_grupos(palpites_path)
    grupos_definidos = sorted(reais)
    pontos_maximos = len(grupos_definidos) * MAX_PONTOS_POR_GRUPO

    linhas: list[RankingGruposLinha] = []
    for participante, palpite in palpites.items():
        pontos, acertos, por_grupo = calcular_pontos_participante(palpite, reais)
        linhas.append(
            RankingGruposLinha(
                posicao=0,
                participante=participante,
                pontos=pontos,
                acertos=acertos,
                por_grupo=por_grupo,
            )
        )

    linhas.sort(key=lambda item: (-item.pontos, -item.acertos, item.participante.lower()))
    for posicao, linha in enumerate(linhas, start=1):
        linha.posicao = posicao

    resumo = ResumoRankingGrupos(
        grupos_definidos=grupos_definidos,
        pontos_maximos=pontos_maximos,
        participantes=len(linhas),
    )
    return linhas, resumo


def formatar_ranking_grupos(
    ranking: list[RankingGruposLinha],
    resumo: ResumoRankingGrupos,
    *,
    detalhe: bool = False,
) -> str:
    grupos_txt = ", ".join(resumo.grupos_definidos)
    linhas = [
        "RANKING CLASSIFICACAO DOS GRUPOS (parcial)",
        f"Grupos definidos: {grupos_txt} ({len(resumo.grupos_definidos)} de {TOTAL_GRUPOS})",
        f"Pontuacao maxima ate agora: {resumo.pontos_maximos} (10 por selecao cravada)",
        "",
        f"{'Pos':>3}  {'Participante':<28} {'Pts':>4}  {'Acertos':>7}",
        "-" * 50,
    ]

    for item in ranking:
        linha = f"{item.posicao:>3}  {item.participante:<28} {item.pontos:>4}  {item.acertos:>7}"
        if detalhe and item.por_grupo:
            grupos_detalhe = "  ".join(
                f"{grupo}:{item.por_grupo.get(grupo, 0):>2}"
                for grupo in resumo.grupos_definidos
            )
            linha = f"{linha}  | {grupos_detalhe}"
        linhas.append(linha)

    linhas.extend(
        [
            "",
            "Regra: 10 pts por time na posicao correta (max. 40 por grupo, 480 no total).",
            "Ranking separado da classificacao dos 72 jogos.",
        ]
    )
    return "\n".join(linhas)
