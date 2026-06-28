from __future__ import annotations

import csv
from pathlib import Path

from src.models import BolaoData, Jogo


def limpar_todos_resultados(bolao: BolaoData) -> None:
    for jogo in bolao.jogos:
        jogo.gols_casa = None
        jogo.gols_fora = None
        jogo.vencedor_penaltis = None


def aplicar_resultados_externos(bolao: BolaoData, path: str | Path) -> None:
    path = Path(path)
    if not path.exists():
        return

    limpar_todos_resultados(bolao)

    overrides: dict[int, tuple[int, int, str | None]] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            jogo_id = int(row["jogo_id"])
            gols_casa = row.get("gols_casa", "").strip()
            gols_fora = row.get("gols_fora", "").strip()
            if gols_casa == "" or gols_fora == "":
                continue
            penaltis = (row.get("vencedor_penaltis") or "").strip() or None
            overrides[jogo_id] = (int(gols_casa), int(gols_fora), penaltis)

    for jogo in bolao.jogos:
        if jogo.id in overrides:
            gols_casa, gols_fora, penaltis = overrides[jogo.id]
            jogo.gols_casa = gols_casa
            jogo.gols_fora = gols_fora
            jogo.vencedor_penaltis = penaltis


def salvar_resultados(bolao: BolaoData, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["jogo_id", "gols_casa", "gols_fora", "vencedor_penaltis"])
        for jogo in sorted(bolao.jogos, key=lambda j: j.id):
            casa = "" if jogo.gols_casa is None else jogo.gols_casa
            fora = "" if jogo.gols_fora is None else jogo.gols_fora
            penaltis = "" if not jogo.vencedor_penaltis else jogo.vencedor_penaltis
            writer.writerow([jogo.id, casa, fora, penaltis])


def atualizar_resultado(
    bolao: BolaoData,
    jogo_id: int,
    gols_casa: int,
    gols_fora: int,
    *,
    vencedor_penaltis: str | None = None,
) -> Jogo:
    jogo = next((j for j in bolao.jogos if j.id == jogo_id), None)
    if jogo is None:
        raise ValueError(f"Jogo {jogo_id} não encontrado.")

    jogo.gols_casa = gols_casa
    jogo.gols_fora = gols_fora
    jogo.vencedor_penaltis = vencedor_penaltis
    return jogo


def remover_resultados(bolao: BolaoData, jogo_ids: list[int]) -> list[Jogo]:
    removidos: list[Jogo] = []
    jogos_por_id = {jogo.id: jogo for jogo in bolao.jogos}
    for jogo_id in jogo_ids:
        jogo = jogos_por_id.get(jogo_id)
        if jogo is None:
            raise ValueError(f"Jogo {jogo_id} não encontrado.")
        jogo.gols_casa = None
        jogo.gols_fora = None
        jogo.vencedor_penaltis = None
        removidos.append(jogo)
    return removidos


def importar_resultados_da_planilha(
    path: str | Path,
    destino: str | Path,
) -> tuple[int, int]:
    from src.thdfm_parser import parse_thdfm_csv

    bolao = parse_thdfm_csv(path)
    salvar_resultados(bolao, destino)
    realizados = sum(1 for jogo in bolao.jogos if jogo.realizado)
    return realizados, len(bolao.jogos)


def validar_bolao(bolao: BolaoData) -> list[str]:
    erros: list[str] = []

    if not bolao.jogos:
        erros.append("Nenhum jogo encontrado no CSV.")
    if not bolao.participantes:
        erros.append("Nenhum participante encontrado no CSV.")

    jogos_ids = {jogo.id for jogo in bolao.jogos}
    palpites_por_par = {(p.participante, p.jogo_id) for p in bolao.palpites}

    for participante in bolao.participantes:
        for jogo_id in jogos_ids:
            if (participante, jogo_id) not in palpites_por_par:
                erros.append(f"Palpite ausente: {participante} no jogo {jogo_id}.")

    for palpite in bolao.palpites:
        if palpite.jogo_id not in jogos_ids:
            erros.append(f"Palpite referencia jogo inexistente: {palpite.jogo_id}.")

    return erros
