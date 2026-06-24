from __future__ import annotations

import json
from pathlib import Path

from src.models import ClassificacaoLinha


def _chave(participante: str) -> str:
    return participante.strip()


def carregar_snapshot(path: str | Path) -> dict | None:
    path = Path(path)
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def salvar_snapshot(
    path: str | Path,
    classificacao: list[ClassificacaoLinha],
    *,
    jogos_realizados: int,
    jogos_ids: list[int],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    dados = {
        "jogos_realizados": jogos_realizados,
        "jogos_ids": jogos_ids,
        "participantes": {
            _chave(linha.participante): {
                "posicao": linha.posicao,
                "soma": linha.soma,
                "placar": linha.placar,
                "vencedor": linha.vencedor,
                "gols_casa": linha.gols_casa,
                "gols_fora": linha.gols_fora,
            }
            for linha in classificacao
        },
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(dados, handle, ensure_ascii=False, indent=2)


def snapshot_de_classificacao(
    classificacao: list[ClassificacaoLinha],
) -> dict[str, dict]:
    return {_chave(linha.participante): {"soma": linha.soma, "posicao": linha.posicao} for linha in classificacao}


def calcular_variacoes(
    classificacao: list[ClassificacaoLinha],
    anterior: dict[str, dict] | None,
) -> dict[str, int | None]:
    if anterior is None:
        return {_chave(linha.participante): None for linha in classificacao}

    variacoes: dict[str, int | None] = {}
    for linha in classificacao:
        chave = _chave(linha.participante)
        ref = anterior.get(chave)
        if ref is None:
            variacoes[chave] = None
        else:
            variacoes[chave] = linha.soma - int(ref["soma"])
    return variacoes


def formatar_variacao(valor: int | None) -> str:
    if valor is None:
        return "-"
    if valor > 0:
        return f"+{valor}"
    return str(valor)


def calcular_mudancas_posicao(
    classificacao: list[ClassificacaoLinha],
    anterior: dict[str, dict] | None,
) -> dict[str, int | None]:
    if anterior is None:
        return {_chave(linha.participante): None for linha in classificacao}

    mudancas: dict[str, int | None] = {}
    for linha in classificacao:
        chave = _chave(linha.participante)
        ref = anterior.get(chave)
        if ref is None:
            mudancas[chave] = None
        else:
            mudancas[chave] = int(ref["posicao"]) - linha.posicao
    return mudancas


def formatar_mudanca_posicao(delta: int | None) -> str:
    if delta is None or delta == 0:
        return ""
    if delta > 0:
        return f"↑{delta}"
    return f"↓{abs(delta)}"


def formatar_posicao_com_mudanca(posicao: int, delta: int | None) -> str:
    mudanca = formatar_mudanca_posicao(delta)
    if mudanca:
        return f"{posicao} {mudanca}"
    return str(posicao)
