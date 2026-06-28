from __future__ import annotations

import csv
import re
from pathlib import Path

PENALTI_COL_RE = re.compile(r"^J(\d+) - Quem passa", re.IGNORECASE)
COLUNA_NOME = "QUAL SEU NOME NA THDFM"

NOME_ALIASES = {
    "cornorato": "Matheus Honorato",
}


def _chave_participante(nome: str) -> str:
    return NOME_ALIASES.get(nome.strip().lower(), nome.strip())


def nome_vencedor_jogo(jogo) -> str:
    from src.scoring import lado_vencedor

    if not jogo.realizado:
        return "-"
    lado = lado_vencedor(
        jogo.gols_casa,
        jogo.gols_fora,
        time_casa=jogo.casa,
        time_fora=jogo.fora,
        vencedor_penaltis=jogo.vencedor_penaltis,
        jogo_id=jogo.id,
    )
    if lado == "casa":
        return jogo.casa.strip()
    if lado == "fora":
        return jogo.fora.strip()
    if lado == "empate":
        return "Empate"
    return "Empate"


def carregar_palpites_penaltis_respostas(path: Path) -> dict[tuple[str, int], str]:
    return _carregar_penaltis_respostas(path)


def _carregar_penaltis_respostas(path: Path) -> dict[tuple[str, int], str]:
    palpites: dict[tuple[str, int], str] = {}

    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        colunas_penaltis: dict[int, str] = {}
        for coluna in reader.fieldnames or []:
            match = PENALTI_COL_RE.match(coluna.strip())
            if match:
                colunas_penaltis[int(match.group(1))] = coluna

        for row in reader:
            nome = _chave_participante(row.get(COLUNA_NOME) or "")
            if not nome:
                continue
            for jogo_id, coluna in colunas_penaltis.items():
                time_passa = (row.get(coluna) or "").strip()
                if time_passa:
                    palpites[(nome, jogo_id)] = time_passa

    return palpites


def exportar_palpites_penaltis(
    palpites: dict[tuple[str, int], str],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["participante", "jogo_id", "time_passa"])
        for (participante, jogo_id), time_passa in sorted(
            palpites.items(),
            key=lambda item: (item[0][1], item[0][0].lower()),
        ):
            writer.writerow([participante, jogo_id, time_passa])


def carregar_palpites_penaltis(path: Path) -> dict[tuple[str, int], str]:
    if not path.exists():
        return {}

    palpites: dict[tuple[str, int], str] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            participante = _chave_participante(row.get("participante") or "")
            jogo_id_raw = (row.get("jogo_id") or "").strip()
            time_passa = (row.get("time_passa") or "").strip()
            if not participante or not jogo_id_raw.isdigit() or not time_passa:
                continue
            palpites[(participante, int(jogo_id_raw))] = time_passa
    return palpites


def aplicar_palpites_penaltis(bolao, palpites: dict[tuple[str, int], str]) -> None:
    if not palpites:
        return
    for palpite in bolao.palpites:
        chave = (_chave_participante(palpite.participante), palpite.jogo_id)
        if chave in palpites:
            palpite.vencedor_penaltis = palpites[chave]
