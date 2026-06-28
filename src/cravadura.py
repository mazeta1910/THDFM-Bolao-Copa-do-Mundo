from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from src.bandeiras import _chave_time
from src.grupos_ranking import times_iguais

COLUNA_REAL = "REAL OFICIAL"
PONTOS_PADRAO = {
    "campeao": 250,
    "vice": 200,
    "terceiro": 150,
    "quarto": 120,
    "artilheiro": 300,
}
CAMPOS = ("campeao", "vice", "terceiro", "quarto", "artilheiro")
HEADER_PONTOS_RE = re.compile(r"\((\d+)\)", re.IGNORECASE)


@dataclass
class PalpiteCravadura:
    participante: str
    campeao: str = ""
    vice: str = ""
    terceiro: str = ""
    quarto: str = ""
    artilheiro: str = ""


@dataclass
class CravaduraPlanilha:
    palpites: dict[str, PalpiteCravadura]
    reais: dict[str, str]
    pontos: dict[str, int]
    ativa: bool


def _chave_nome(nome: str) -> str:
    return nome.strip()


def _chave_texto(texto: str) -> str:
    return _chave_time(texto)


def _valor_valido(valor: str) -> bool:
    valor = (valor or "").strip()
    return bool(valor) and valor not in {"-", "—", "–"}


def _extrair_pontos_cabecalho(cabecalho: list[str]) -> dict[str, int]:
    pontos = dict(PONTOS_PADRAO)
    for indice, campo in enumerate(CAMPOS):
        if indice + 1 >= len(cabecalho):
            break
        match = HEADER_PONTOS_RE.search(cabecalho[indice + 1])
        if match:
            pontos[campo] = int(match.group(1))
    return pontos


def carregar_cravadura_planilha(path: str | Path) -> CravaduraPlanilha:
    path = Path(path)
    palpites: dict[str, PalpiteCravadura] = {}
    reais: dict[str, str] = {campo: "" for campo in CAMPOS}
    pontos = dict(PONTOS_PADRAO)

    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        rows = list(reader)

    if not rows:
        return CravaduraPlanilha(palpites=palpites, reais=reais, pontos=pontos, ativa=False)

    pontos = _extrair_pontos_cabecalho(rows[0])

    for row in rows[1:]:
        if len(row) < 6:
            continue
        nome = _chave_nome(row[0])
        if not nome:
            continue
        valores = [(row[i + 1] if i + 1 < len(row) else "").strip() for i in range(5)]

        if nome.upper() == COLUNA_REAL.upper():
            reais = {
                campo: valores[indice] if _valor_valido(valores[indice]) else ""
                for indice, campo in enumerate(CAMPOS)
            }
            continue

        palpites[nome] = PalpiteCravadura(
            participante=nome,
            campeao=valores[0],
            vice=valores[1],
            terceiro=valores[2],
            quarto=valores[3],
            artilheiro=valores[4],
        )

    ativa = any(reais.values())
    return CravaduraPlanilha(palpites=palpites, reais=reais, pontos=pontos, ativa=ativa)


def pontos_cravadura_participante(
    palpite: PalpiteCravadura,
    reais: dict[str, str],
    pontos: dict[str, int],
) -> tuple[int, int]:
    if not any(reais.values()):
        return 0, 0

    total = 0
    acertos = 0
    for campo in CAMPOS:
        real = reais.get(campo, "")
        palpite_valor = getattr(palpite, campo, "")
        if not _valor_valido(real) or not palpite_valor:
            continue
        if campo == "artilheiro":
            acertou = _chave_texto(palpite_valor) == _chave_texto(real)
        else:
            acertou = times_iguais(palpite_valor, real)
        if acertou:
            total += pontos.get(campo, 0)
            acertos += 1

    return total, acertos


def pontos_cravadura_por_participante(path: str | Path) -> tuple[dict[str, int], bool]:
    planilha = carregar_cravadura_planilha(path)
    return {
        nome: pontos_cravadura_participante(palpite, planilha.reais, planilha.pontos)[0]
        for nome, palpite in planilha.palpites.items()
    }, planilha.ativa
