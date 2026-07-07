"""Encontra, por participante, qual jogo em 73-88 explicaria o drift de 5 pts."""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from scripts.import_oitavas import _chave_participante
from src.cli import carregar_bolao
from src.data_paths import DATA_DIR, resolver_arquivo_fonte
from src.ranking import _parse_linhas_classificacao, calcular_pontos_faixa
from src.scoring import classificar_palpite, pontos_detalhados


def _drift_32avos() -> list[dict]:
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
    itens: list[dict] = []

    for chave, r32 in ref32.items():
        rg = ref_g.get(chave)
        if rg is None:
            continue
        ref_pts = r32.soma - rg.soma
        calc_pts = next(
            valor for nome, valor in calc73.items() if _chave_participante(nome) == chave
        )
        delta = ref_pts - calc_pts.soma
        if delta == 0:
            continue
        itens.append(
            {
                "chave": chave,
                "nome": r32.participante.strip(),
                "delta": delta,
                "ref": ref_pts,
                "calc": calc_pts.soma,
            }
        )
    return itens


def _candidatos_jogo(bolao, chave: str, delta: int) -> list[tuple[int, int, str]]:
    """Retorna jogos onde mudar o placar em +/-1 explicaria delta de 5 pts."""
    candidatos: list[tuple[int, int, str]] = []
    for jogo_id in range(73, 89):
        jogo = next(j for j in bolao.jogos if j.id == jogo_id)
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
        for dc in (-1, 0, 1):
            for df in (-1, 0, 1):
                if dc == 0 and df == 0:
                    continue
                nc, nf = jogo.gols_casa + dc, jogo.gols_fora + df
                if nc < 0 or nf < 0:
                    continue
                depois = pontos_detalhados(
                    palpite.palpite_casa,
                    palpite.palpite_fora,
                    nc,
                    nf,
                    jogo_id=jogo_id,
                    time_casa=jogo.casa,
                    time_fora=jogo.fora,
                    palpite_penaltis=palpite.vencedor_penaltis,
                    real_penaltis=jogo.vencedor_penaltis,
                )
                mudanca = depois.total - antes.total
                if mudanca == delta:
                    cat, _ = classificar_palpite(
                        palpite.palpite_casa,
                        palpite.palpite_fora,
                        nc,
                        nf,
                        jogo_id=jogo_id,
                        time_casa=jogo.casa,
                        time_fora=jogo.fora,
                        palpite_penaltis=palpite.vencedor_penaltis,
                        real_penaltis=jogo.vencedor_penaltis,
                    )
                    candidatos.append(
                        (
                            jogo_id,
                            mudanca,
                            (
                                f"palpite {palpite.palpite_casa}-{palpite.palpite_fora} "
                                f"pen={palpite.vencedor_penaltis or '-'} | "
                                f"atual {jogo.gols_casa}-{jogo.gols_fora} ({antes.total}pts) -> "
                                f"{nc}-{nf} ({depois.total}pts, {cat})"
                            ),
                        )
                    )
    return candidatos


def main() -> None:
    bolao = carregar_bolao()
    drifts = _drift_32avos()
    contagem = Counter()

    print("=== Drift 32 avos (J73-J88) vs Excel ===")
    print(f"Participantes afetados: {len(drifts)}")
    print()

    for item in sorted(drifts, key=lambda x: -abs(x["delta"])):
        candidatos = _candidatos_jogo(bolao, item["chave"], item["delta"])
        print(
            f"{item['nome']:28} excel={item['ref']:3d} calc={item['calc']:3d} "
            f"delta={item['delta']:+d}"
        )
        if not candidatos:
            print("  (nenhum ajuste de 1 gol explica)")
            continue
        for jogo_id, _, texto in candidatos[:3]:
            contagem[jogo_id] += 1
            print(f"  J{jogo_id}: {texto}")
        if len(candidatos) > 3:
            print(f"  ... +{len(candidatos) - 3} outro(s) cenario(s)")
        print()

    print("=== Jogos mais citados como possivel divergencia de resultado ===")
    for jogo_id, qtd in contagem.most_common():
        jogo = next(j for j in bolao.jogos if j.id == jogo_id)
        print(
            f"  J{jogo_id} {jogo.casa} x {jogo.fora} "
            f"(resultado atual {jogo.gols_casa}-{jogo.gols_fora}): {qtd} participante(s)"
        )


if __name__ == "__main__":
    main()
