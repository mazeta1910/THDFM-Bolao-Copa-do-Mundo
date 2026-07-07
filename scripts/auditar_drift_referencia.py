"""Compara pontos jogos 1-79: Excel (referencia) vs recalculo do bolao.csv."""

from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from scripts.import_oitavas import _chave_participante
from src.cli import carregar_bolao
from src.data_paths import DATA_DIR
from src.ranking import (
    JOGOS_BASELINE_REFERENCIA_GERAL,
    calcular_pontos_faixa,
    carregar_classificacao_referencia,
    resolver_referencia_geral_csv,
)
from src.scoring import FASE_GRUPOS_MAX, pontos_detalhados


def _auditar_penaltis_ausentes(bolao, drifts: list[tuple]) -> None:
    """Sugere jogos com empate sem vencedor_penaltis que explicam o drift."""
    if not drifts:
        return

    alvos = {_chave_participante(nome): nome for nome, *_ in drifts}
    print("=== Hipotese: vencedor_penaltis ausente em resultados.csv ===")
    print()

    for jogo in bolao.jogos:
        if jogo.id not in JOGOS_BASELINE_REFERENCIA_GERAL:
            continue
        if not jogo.realizado or jogo.gols_casa != jogo.gols_fora:
            continue
        if jogo.id <= FASE_GRUPOS_MAX:
            continue
        if jogo.vencedor_penaltis:
            continue

        for pen in (jogo.casa, jogo.fora):
            afetados: list[str] = []
            for palpite in bolao.palpites:
                chave = _chave_participante(palpite.participante)
                if chave not in alvos or palpite.jogo_id != jogo.id:
                    continue
                antes = pontos_detalhados(
                    palpite.palpite_casa,
                    palpite.palpite_fora,
                    jogo.gols_casa,
                    jogo.gols_fora,
                    jogo_id=jogo.id,
                    time_casa=jogo.casa,
                    time_fora=jogo.fora,
                    palpite_penaltis=palpite.vencedor_penaltis,
                    real_penaltis=None,
                )
                depois = pontos_detalhados(
                    palpite.palpite_casa,
                    palpite.palpite_fora,
                    jogo.gols_casa,
                    jogo.gols_fora,
                    jogo_id=jogo.id,
                    time_casa=jogo.casa,
                    time_fora=jogo.fora,
                    palpite_penaltis=palpite.vencedor_penaltis,
                    real_penaltis=pen,
                )
                if depois.vencedor - antes.vencedor == 7:
                    afetados.append(
                        f"{palpite.participante.strip():22} "
                        f"palpite {palpite.palpite_casa}-{palpite.palpite_fora} "
                        f"pen={palpite.vencedor_penaltis!r}: "
                        f"{antes.total} -> {depois.total} pts"
                    )

            if afetados:
                print(
                    f"J{jogo.id} {jogo.casa} x {jogo.fora} ({jogo.gols_casa}-{jogo.gols_fora}) "
                    f"— se penaltis = {pen!r}:"
                )
                for linha in afetados:
                    print(f"    {linha}")
                print()


def main() -> None:
    bolao = carregar_bolao()
    ref_path = resolver_referencia_geral_csv(DATA_DIR)
    if ref_path is None:
        print("Arquivo de referencia nao encontrado.")
        return

    ref = {
        linha.participante.strip(): linha
        for linha in carregar_classificacao_referencia(ref_path, secao="grupos_32avos")
    }
    ids_1_79 = set(JOGOS_BASELINE_REFERENCIA_GERAL)
    calc_1_79 = calcular_pontos_faixa(bolao, ids_1_79)

    print("=== Drift jogos 1-79: Excel vs bolao.csv ===")
    print(f"Referencia: {ref_path.name}")
    print()

    drifts: list[tuple] = []
    for nome, pts in calc_1_79.items():
        chave = nome.strip()
        linha_ref = ref.get(chave)
        if linha_ref is None:
            continue
        delta = linha_ref.soma - pts.soma
        if delta != 0:
            drifts.append(
                (
                    chave,
                    delta,
                    linha_ref.soma,
                    pts.soma,
                    linha_ref.placar - pts.placar,
                    linha_ref.vencedor - pts.vencedor,
                    linha_ref.gols_casa - pts.gols_casa,
                    linha_ref.gols_fora - pts.gols_fora,
                )
            )

    drifts.sort(key=lambda item: -abs(item[1]))
    print(f"Participantes com diferenca: {len(drifts)}")
    for row in drifts:
        print(
            f"  {row[0]:28} drift={row[1]:+4d}  excel={row[2]:3d}  bolao={row[3]:3d}  "
            f"(dPlacar={row[4]:+d} dVenc={row[5]:+d} dGC={row[6]:+d} dGF={row[7]:+d})"
        )

    _auditar_penaltis_ausentes(bolao, drifts)

    if not drifts:
        return

    participante = "Jose Carlos"
    if len(sys.argv) > 1:
        participante = " ".join(sys.argv[1:])

    chave_alvo = _chave_participante(participante)
    nome_bolao = next(
        (n.strip() for n in bolao.participantes if _chave_participante(n) == chave_alvo),
        participante,
    )
    linha_ref = ref.get(nome_bolao)
    if linha_ref is None:
        print(f"\nParticipante nao encontrado na referencia: {participante}")
        return

    jogos = {
        jogo.id: jogo
        for jogo in bolao.jogos
        if jogo.id in ids_1_79 and jogo.realizado
    }
    per_jogo: dict[int, tuple] = {}
    for palpite in bolao.palpites:
        if palpite.jogo_id not in jogos:
            continue
        if _chave_participante(palpite.participante) != chave_alvo:
            continue
        jogo = jogos[palpite.jogo_id]
        det = pontos_detalhados(
            palpite.palpite_casa,
            palpite.palpite_fora,
            jogo.gols_casa,
            jogo.gols_fora,
            jogo_id=jogo.id,
            time_casa=jogo.casa,
            time_fora=jogo.fora,
            palpite_penaltis=palpite.vencedor_penaltis,
            real_penaltis=jogo.vencedor_penaltis,
        )
        per_jogo[jogo.id] = (
            det,
            palpite.palpite_casa,
            palpite.palpite_fora,
            jogo.gols_casa,
            jogo.gols_fora,
            jogo.casa,
            jogo.fora,
            palpite.vencedor_penaltis,
            jogo.vencedor_penaltis,
        )

    total_bolao = sum(item[0].total for item in per_jogo.values())
    print()
    print(f"=== {nome_bolao}: detalhe jogos 1-79 ===")
    print(f"Excel referencia: {linha_ref.soma} pts")
    print(f"Bolao recalculado: {total_bolao} pts")
    print(f"Drift: {linha_ref.soma - total_bolao:+d} pts")
    print()
    print("Jogos com pontos no bolao:")
    for jogo_id in sorted(per_jogo):
        det, pc, pf, rc, rf, casa, fora, pen_p, pen_r = per_jogo[jogo_id]
        if det.total == 0:
            continue
        print(
            f"  J{jogo_id:2d} {casa} x {fora}: "
            f"palpite {pc}-{pf} (pen {pen_p!r}) | real {rc}-{rf} (pen {pen_r!r}) "
            f"=> {det.total} (P{det.placar} V{det.vencedor} GC{det.gols_casa} GF{det.gols_fora})"
        )


if __name__ == "__main__":
    main()
