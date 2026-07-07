"""Compara classificacao calculada vs secao GRUPOS+32AVOS+OITAVAS do Excel."""

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
from src.models import ClassificacaoLinha
from src.ranking import _parse_linhas_classificacao, gerar_classificacao_jogos
from src.scoring import classificar_palpite, pontos_detalhados

MARCADOR_OITAVAS = "GRUPOS + 32 AVOS + OITAVAS"
CAMPOS = ("placar", "vencedor", "gols_casa", "gols_fora", "soma")


def carregar_referencia_oitavas(path: Path) -> list[ClassificacaoLinha]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    cabecalho_idx = None
    for indice, row in enumerate(rows):
        if any(MARCADOR_OITAVAS in cell for cell in row):
            cabecalho_idx = indice + 1
            break
    if cabecalho_idx is None:
        raise ValueError(f"Secao {MARCADOR_OITAVAS!r} nao encontrada em {path.name}")

    return _parse_linhas_classificacao(rows, cabecalho_idx)


def _mapa_por_chave(linhas: list[ClassificacaoLinha]) -> dict[str, ClassificacaoLinha]:
    return {_chave_participante(linha.participante): linha for linha in linhas}


def comparar_totais(
    calculada: list[ClassificacaoLinha],
    referencia: list[ClassificacaoLinha],
) -> list[dict]:
    calc = _mapa_por_chave(calculada)
    ref = _mapa_por_chave(referencia)
    diffs: list[dict] = []

    for chave in sorted(set(calc) | set(ref)):
        c = calc.get(chave)
        r = ref.get(chave)
        if c is None:
            diffs.append({"chave": chave, "tipo": "ausente_calculada", "ref": r})
            continue
        if r is None:
            diffs.append({"chave": chave, "tipo": "ausente_referencia", "calc": c})
            continue

        delta = {campo: getattr(r, campo) - getattr(c, campo) for campo in CAMPOS}
        if any(delta[campo] != 0 for campo in CAMPOS):
            diffs.append(
                {
                    "chave": chave,
                    "nome": c.participante.strip(),
                    "calc": c,
                    "ref": r,
                    "delta": delta,
                }
            )
    return diffs


def pontos_por_jogo(bolao, chave: str) -> dict[int, dict]:
    por_jogo: dict[int, dict] = {}
    for palpite in bolao.palpites:
        if _chave_participante(palpite.participante) != chave:
            continue
        jogo = next(j for j in bolao.jogos if j.id == palpite.jogo_id)
        if not jogo.realizado:
            continue
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
        cat, ac_v = classificar_palpite(
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
        por_jogo[jogo.id] = {
            "jogo": jogo,
            "palpite": palpite,
            "det": det,
            "categoria": cat,
            "acertou_vencedor": ac_v,
        }
    return por_jogo


def main() -> None:
    ref_path = resolver_arquivo_fonte(
        "BOLÃO THDFM WC26 - CLASSIFICAÇÃO PROVISÓRIA.csv",
        data_dir=DATA_DIR,
    )
    if ref_path is None or not ref_path.exists():
        print("Arquivo de referencia nao encontrado.")
        return

    bolao = carregar_bolao()
    calculada = gerar_classificacao_jogos(bolao)
    referencia = carregar_referencia_oitavas(ref_path)
    diffs = comparar_totais(calculada, referencia)

    print(f"Referencia: {ref_path.name}")
    print(f"Secao: {MARCADOR_OITAVAS}")
    print(f"Participantes com diferenca: {len(diffs)}")
    print()

    if not diffs:
        print("Classificacao calculada confere com o Excel.")
        return

    diffs.sort(key=lambda item: -abs(item["delta"]["soma"]))
    print("=== Resumo por participante ===")
    for item in diffs:
        d = item["delta"]
        c, r = item["calc"], item["ref"]
        print(
            f"{item['nome']:28} "
            f"dSoma={d['soma']:+4d}  "
            f"(dP={d['placar']:+d} dV={d['vencedor']:+d} "
            f"dGC={d['gols_casa']:+d} dGF={d['gols_fora']:+d})  "
            f"calc={c.soma} excel={r.soma}"
        )

    print()
    print("=== Detalhe por jogo (participantes com diferenca) ===")
    for item in diffs:
        chave = item["chave"]
        por_jogo = pontos_por_jogo(bolao, chave)
        print(f"\n--- {item['nome']} (excel - calc = {item['delta']['soma']:+d}) ---")
        for jogo_id in sorted(por_jogo):
            info = por_jogo[jogo_id]
            jogo = info["jogo"]
            palpite = info["palpite"]
            det = info["det"]
            if det.total == 0:
                continue
            pen_p = palpite.vencedor_penaltis or "-"
            pen_r = jogo.vencedor_penaltis or "-"
            print(
                f"  J{jogo_id:2d} {jogo.casa} x {jogo.fora} | "
                f"palpite {palpite.palpite_casa}-{palpite.palpite_fora} pen={pen_p} | "
                f"real {jogo.gols_casa}-{jogo.gols_fora} pen={pen_r} | "
                f"{info['categoria']} V={'S' if info['acertou_vencedor'] else 'N'} | "
                f"{det.total}pts (P{det.placar} V{det.vencedor} GC{det.gols_casa} GF{det.gols_fora})"
            )

    # Totais por faixa de jogos
    print()
    print("=== Totais por faixa (todos com diferenca) ===")
    from src.ranking import calcular_pontos_faixa

    faixas = [
        ("grupos 1-72", set(range(1, 73))),
        ("32avos 73-88", set(range(73, 89))),
        ("oitavas 89-94", set(range(89, 95))),
    ]
    for nome_faixa, ids in faixas:
        totais = calcular_pontos_faixa(bolao, ids)
        print(f"\n{nome_faixa}:")
        for item in diffs[:10]:
            chave = item["chave"]
            pts = next(
                (v for k, v in totais.items() if _chave_participante(k) == chave),
                None,
            )
            if pts:
                print(f"  {item['nome']:28} {pts.soma} pts")


if __name__ == "__main__":
    main()
