"""Testa se alterar o resultado de um jogo explica o drift vs Excel."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from scripts.import_oitavas import _chave_participante
from src.cli import carregar_bolao
from src.data_paths import DATA_DIR, resolver_arquivo_fonte
from src.ranking import _parse_linhas_classificacao, calcular_pontos_faixa
from src.scoring import pontos_detalhados


def _grupos_drift() -> tuple[set[str], set[str]]:
    ref_path = resolver_arquivo_fonte(
        "BOLÃO THDFM WC26 - CLASSIFICAÇÃO PROVISÓRIA.csv",
        data_dir=DATA_DIR,
    )
    with ref_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    idx32 = next(
        i
        for i, row in enumerate(rows)
        if "GRUPOS + 32 AVOS (ORDENADA)" in "".join(row) and "OITAVAS" not in "".join(row)
    )
    ref32 = {
        _chave_participante(linha.participante): linha
        for linha in _parse_linhas_classificacao(rows, idx32 + 1)
    }
    ref_g = {
        _chave_participante(linha.participante): linha
        for linha in _parse_linhas_classificacao(rows, 1)
    }

    bolao = carregar_bolao()
    calc73 = calcular_pontos_faixa(bolao, set(range(73, 89)))

    plus5: set[str] = set()
    minus5: set[str] = set()
    for chave, r32 in ref32.items():
        rg = ref_g.get(chave)
        if rg is None:
            continue
        ref_73_88 = r32.soma - rg.soma
        calc_pts = next(
            valor for nome, valor in calc73.items() if _chave_participante(nome) == chave
        )
        delta = ref_73_88 - calc_pts.soma
        if delta == 5:
            plus5.add(chave)
        elif delta == -5:
            minus5.add(chave)
    return plus5, minus5


def testar_jogo(jogo_id: int, casa: int, fora: int) -> None:
    bolao = carregar_bolao()
    jogo = next(j for j in bolao.jogos if j.id == jogo_id)
    plus5, minus5 = _grupos_drift()

    print(
        f"J{jogo_id} {jogo.casa} x {jogo.fora}: "
        f"{jogo.gols_casa}-{jogo.gols_fora} -> {casa}-{fora}"
    )

    fix_plus = fix_minus = 0
    for chave in plus5:
        palpite = next(
            p
            for p in bolao.palpites
            if p.jogo_id == jogo_id and _chave_participante(p.participante) == chave
        )
        antes = pontos_detalhados(
            palpite.palpite_casa,
            palpite.palpite_fora,
            jogo.gols_casa,
            jogo.gols_fora,
            jogo_id=jogo_id,
            time_casa=jogo.casa,
            time_fora=jogo.fora,
            palpite_penaltis=palpite.vencedor_penaltis,
            real_penaltis=jogo.vencedor_penaltis,
        )
        depois = pontos_detalhados(
            palpite.palpite_casa,
            palpite.palpite_fora,
            casa,
            fora,
            jogo_id=jogo_id,
            time_casa=jogo.casa,
            time_fora=jogo.fora,
            palpite_penaltis=palpite.vencedor_penaltis,
            real_penaltis=jogo.vencedor_penaltis,
        )
        if depois.total - antes.total == 5:
            fix_plus += 1

    for chave in minus5:
        palpite = next(
            p
            for p in bolao.palpites
            if p.jogo_id == jogo_id and _chave_participante(p.participante) == chave
        )
        antes = pontos_detalhados(
            palpite.palpite_casa,
            palpite.palpite_fora,
            jogo.gols_casa,
            jogo.gols_fora,
            jogo_id=jogo_id,
            time_casa=jogo.casa,
            time_fora=jogo.fora,
            palpite_penaltis=palpite.vencedor_penaltis,
            real_penaltis=jogo.vencedor_penaltis,
        )
        depois = pontos_detalhados(
            palpite.palpite_casa,
            palpite.palpite_fora,
            casa,
            fora,
            jogo_id=jogo_id,
            time_casa=jogo.casa,
            time_fora=jogo.fora,
            palpite_penaltis=palpite.vencedor_penaltis,
            real_penaltis=jogo.vencedor_penaltis,
        )
        if antes.total - depois.total == 5:
            fix_minus += 1

    print(f"  Corrige +5: {fix_plus}/{len(plus5)} | Corrige -5: {fix_minus}/{len(minus5)}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: py scripts/testar_resultado_jogo.py JOGO_ID GOLS_CASA GOLS_FORA")
        sys.exit(1)
    testar_jogo(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
