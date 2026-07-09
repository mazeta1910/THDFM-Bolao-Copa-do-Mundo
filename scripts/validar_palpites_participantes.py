"""Valida palpites exportados dos participantes e recalcula a classificacao ate J96."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.data_paths import (
    BOLAO_CSV,
    CLASSIFICACAO_18AVOS_CSV,
    DATA_DIR,
    PALPITES_PENALTIS_CSV,
    RESULTADOS_CSV,
)
from src.loader import aplicar_resultados_externos
from src.models import BolaoData, Palpite
from src.penaltis import aplicar_palpites_penaltis, carregar_palpites_penaltis
from src.ranking import (
    JOGOS_ATE_OITAVAS,
    carregar_classificacao_referencia,
    exportar_classificacao,
    gerar_classificacao_jogos_faixa,
)
from src.thdfm_parser import JOGO_RE, _cell, parse_thdfm_csv

PALPITES_PARTICIPANTES_DIR = DATA_DIR / "palpites participantes"
EXCEL_REF_CSV = DATA_DIR / "fontes" / "BOLÃO THDFM WC26 - CLASSIFICAÇÃO PROVISÓRIA.csv"
SAIDA_CSV = DATA_DIR / "ultimo" / "csv" / "classificacao_palpites_validados.csv"
RELATORIO_CSV = DATA_DIR / "ultimo" / "csv" / "validacao_palpites_diff.csv"

NOME_ALIASES = {
    "cornorato": "matheus honorato",
    "josé carlos": "jose carlos",
}


def _chave_participante(nome: str) -> str:
    from src.bandeiras import _normalizar

    chave = _normalizar(nome).strip().lower()
    return NOME_ALIASES.get(chave, chave)


def _parse_gols(valor: str) -> int | None:
    valor = (valor or "").strip().rstrip("+")
    if not valor.isdigit():
        return None
    return int(valor)


def _detectar_delimitador(linha: str) -> str:
    if linha.count(";") >= linha.count(","):
        return ";"
    return ","


def _ler_linhas_csv(path: Path) -> list[list[str]]:
    linhas: list[list[str]] = []
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        if not raw.strip():
            continue
        delim = _detectar_delimitador(raw)
        linhas.append(next(csv.reader([raw], delimiter=delim)))
    return linhas


def _label_linha(row: list[str]) -> str:
    return _cell(row, 0) or _cell(row, 1)


def _indices_palpite_row(row: list[str]) -> tuple[str, int, int] | None:
    """Retorna (nome, idx_casa, idx_fora) ou None."""
    nome_col0 = _cell(row, 0)
    if nome_col0 and _cell(row, 1).lower() != "x" and _parse_gols(_cell(row, 1)) is not None:
        if _cell(row, 2).lower() != "x":
            return None
        return nome_col0, 1, 3

    nome_col1 = _cell(row, 1)
    if nome_col1 and _cell(row, 3).lower() == "x":
        return nome_col1, 2, 4
    return None


def _extrair_thdfm(path: Path) -> tuple[dict[tuple[str, int], tuple[int, int]], dict[tuple[str, int], str]]:
    """Extrai palpites no layout bolao/THDFM (multiplos participantes por arquivo)."""
    palpites: dict[tuple[str, int], tuple[int, int]] = {}
    penaltis: dict[tuple[str, int], str] = {}
    jogo_atual: int | None = None

    for row in _ler_linhas_csv(path):
        label = _label_linha(row)
        jogo_match = JOGO_RE.match(label)
        if jogo_match:
            jogo_atual = int(jogo_match.group(1))
            continue
        if jogo_atual is None or label.upper() == "PLACAR":
            continue

        parsed = _indices_palpite_row(row)
        if parsed is None:
            continue
        nome, idx_casa, idx_fora = parsed
        if not nome or JOGO_RE.match(nome) or nome.upper() == "PLACAR":
            continue

        casa = _parse_gols(_cell(row, idx_casa))
        fora = _parse_gols(_cell(row, idx_fora))
        if casa is None or fora is None:
            continue

        chave = _chave_participante(nome)
        palpites[(chave, jogo_atual)] = (casa, fora)

        pen = _cell(row, idx_fora + 1)
        if casa == fora and pen and pen not in {"-", "--"} and not pen.startswith("Gols"):
            penaltis[(chave, jogo_atual)] = pen.strip()

    return palpites, penaltis


def _extrair_participante(path: Path) -> tuple[dict[tuple[str, int], tuple[int, int]], dict[tuple[str, int], str]]:
    """Extrai palpites de um CSV de um unico participante (nome no arquivo ou na 1a coluna)."""
    participante = path.stem.strip()
    chave_part = _chave_participante(participante)
    palpites: dict[tuple[str, int], tuple[int, int]] = {}
    penaltis: dict[tuple[str, int], str] = {}
    jogo_atual: int | None = None

    rows = _ler_linhas_csv(path)
    if not rows:
        return {}, {}

    header = [c.strip().lower() for c in rows[0]]
    if "jogo" in header or "jogo_id" in header:
        try:
            idx_jogo = header.index("jogo") if "jogo" in header else header.index("jogo_id")
            idx_casa = next(i for i, h in enumerate(header) if h in {"gols_casa", "casa", "gol_casa"})
            idx_fora = next(i for i, h in enumerate(header) if h in {"gols_fora", "fora", "gol_fora"})
        except StopIteration:
            idx_jogo = None
        if idx_jogo is not None:
            idx_pen = header.index("penaltis") if "penaltis" in header else None
            idx_nome = header.index("nome") if "nome" in header else None
            for row in rows[1:]:
                if len(row) <= max(idx_jogo, idx_casa, idx_fora):
                    continue
                jogo_raw = row[idx_jogo].strip()
                jogo_match = re.search(r"(\d+)", jogo_raw)
                if not jogo_match:
                    continue
                jogo_id = int(jogo_match.group(1))
                casa = _parse_gols(row[idx_casa])
                fora = _parse_gols(row[idx_fora])
                if casa is None or fora is None:
                    continue
                nome = row[idx_nome].strip() if idx_nome is not None and idx_nome < len(row) else participante
                chave = _chave_participante(nome)
                palpites[(chave, jogo_id)] = (casa, fora)
                if idx_pen is not None and idx_pen < len(row):
                    pen = row[idx_pen].strip()
                    if pen:
                        penaltis[(chave, jogo_id)] = pen
            return palpites, penaltis

    thdfm_p, thdfm_pen = _extrair_thdfm(path)
    if thdfm_p:
        return thdfm_p, thdfm_pen

    for row in rows:
        label = _cell(row, 0)
        jogo_match = JOGO_RE.match(label) or re.match(r"^Jogo\s*(\d+)$", label, re.I)
        if jogo_match:
            jogo_atual = int(jogo_match.group(1))
            continue
        if jogo_atual is None:
            continue
        casa = _parse_gols(_cell(row, 0))
        fora = _parse_gols(_cell(row, 2) if _cell(row, 1).lower() == "x" else _cell(row, 1))
        if casa is None or fora is None:
            continue
        palpites[(chave_part, jogo_atual)] = (casa, fora)

    return palpites, penaltis


def carregar_palpites_diretorio(diretorio: Path) -> tuple[dict[tuple[str, int], tuple[int, int]], dict[tuple[str, int], str], list[Path]]:
    arquivos = sorted(p for p in diretorio.glob("*.csv") if p.is_file())
    palpites: dict[tuple[str, int], tuple[int, int]] = {}
    penaltis: dict[tuple[str, int], str] = {}
    usados: list[Path] = []

    for path in arquivos:
        thdfm_p, thdfm_pen = _extrair_thdfm(path)
        if thdfm_p:
            palpites.update(thdfm_p)
            penaltis.update(thdfm_pen)
            usados.append(path)
            continue

        part_p, part_pen = _extrair_participante(path)
        if part_p:
            palpites.update(part_p)
            penaltis.update(part_pen)
            usados.append(path)

    return palpites, penaltis, usados


@dataclass(frozen=True)
class LinhaDiff:
    participante: str
    campo: str
    calculado: int
    referencia: int


def _mapa_nomes_bolao(bolao: BolaoData) -> dict[str, str]:
    return {_chave_participante(nome): nome.strip() for nome in bolao.participantes}


def aplicar_palpites_no_bolao(
    bolao: BolaoData,
    palpites: dict[tuple[str, int], tuple[int, int]],
    nomes_bolao: dict[str, str],
) -> int:
    alterados = 0
    novos: list[Palpite] = []
    for palpite in bolao.palpites:
        if palpite.jogo_id not in JOGOS_ATE_OITAVAS:
            novos.append(palpite)
            continue
        chave = _chave_participante(palpite.participante)
        novo = palpites.get((chave, palpite.jogo_id))
        if novo is None:
            novos.append(palpite)
            continue
        casa, fora = novo
        if palpite.palpite_casa != casa or palpite.palpite_fora != fora:
            alterados += 1
        novos.append(
            Palpite(
                participante=palpite.participante,
                jogo_id=palpite.jogo_id,
                palpite_casa=casa,
                palpite_fora=fora,
                vencedor_penaltis=palpite.vencedor_penaltis,
            )
        )
    bolao.palpites = novos
    return alterados


def carregar_referencia_ate_oitavas() -> dict[str, tuple[int, int, int, int, int]]:
    linhas = carregar_classificacao_referencia(
        CLASSIFICACAO_18AVOS_CSV,
        secao="grupos_32avos_oitavas",
    )
    return {
        linha.participante.strip(): (
            linha.placar,
            linha.vencedor,
            linha.gols_casa,
            linha.gols_fora,
            linha.soma,
        )
        for linha in linhas
    }


def carregar_excel_oitavas() -> dict[str, tuple[int, int, int, int, int]]:
    if not EXCEL_REF_CSV.exists():
        return {}
    resultado: dict[str, tuple[int, int, int, int, int]] = {}
    with EXCEL_REF_CSV.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        in_sec = False
        for row in reader:
            if row and "GRUPOS + 32 AVOS + OITAVAS" in row[0]:
                in_sec = True
                continue
            if not in_sec or not row or not row[0].strip().isdigit():
                continue
            nome = row[1].strip()
            vals = tuple(int(x) for x in row[2:7])
            resultado[nome] = vals
    return resultado


def _normalizar_nome_excel(nome: str, nomes_bolao: dict[str, str]) -> str:
    chave = _chave_participante(nome)
    return nomes_bolao.get(chave, nome.strip())


def comparar_classificacoes(
    calculada: dict[str, tuple[int, int, int, int, int]],
    referencia: dict[str, tuple[int, int, int, int, int]],
    *,
    rotulo_ref: str,
    nomes_bolao: dict[str, str],
) -> list[LinhaDiff]:
    diffs: list[LinhaDiff] = []
    campos = ("placar", "vencedor", "gols_casa", "gols_fora", "soma")

    ref_por_chave: dict[str, tuple[int, int, int, int, int]] = {}
    for nome, vals in referencia.items():
        ref_por_chave[_chave_participante(nome)] = vals

    for chave, calc_vals in sorted(calculada.items(), key=lambda item: -item[1][4]):
        nome = nomes_bolao.get(chave, chave)
        ref_vals = ref_por_chave.get(chave)
        if ref_vals is None:
            diffs.append(LinhaDiff(nome, f"ausente_em_{rotulo_ref}", calc_vals[4], -1))
            continue
        for indice, campo in enumerate(campos):
            if calc_vals[indice] != ref_vals[indice]:
                diffs.append(
                    LinhaDiff(nome, f"{campo}_vs_{rotulo_ref}", calc_vals[indice], ref_vals[indice])
                )
    return diffs


def exportar_relatorio_diff(diffs: list[LinhaDiff], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["participante", "campo", "calculado", "referencia", "delta"])
        for diff in diffs:
            delta = diff.calculado - diff.referencia if diff.referencia >= 0 else ""
            writer.writerow([diff.participante, diff.campo, diff.calculado, diff.referencia, delta])


def validar_palpites(
    *,
    diretorio: Path = PALPITES_PARTICIPANTES_DIR,
    bolao_path: Path = BOLAO_CSV,
    resultados_path: Path = RESULTADOS_CSV,
) -> int:
    arquivos = sorted(diretorio.glob("*.csv"))
    if not arquivos:
        print(f"Nenhum CSV encontrado em {diretorio}")
        print("Coloque os exports dos participantes (.csv) nessa pasta e rode novamente.")
        return 1

    palpites_csv, penaltis_csv, usados = carregar_palpites_diretorio(diretorio)
    if not palpites_csv:
        print(f"Nenhum palpite J1-J96 reconhecido nos arquivos de {diretorio}")
        return 1

    bolao = parse_thdfm_csv(bolao_path)
    aplicar_resultados_externos(bolao, resultados_path)
    nomes_bolao = _mapa_nomes_bolao(bolao)

    alterados = aplicar_palpites_no_bolao(bolao, palpites_csv, nomes_bolao)
    penaltis = carregar_palpites_penaltis(PALPITES_PENALTIS_CSV)
    penaltis.update({(nomes_bolao.get(k, k), j): v for (k, j), v in penaltis_csv.items()})
    aplicar_palpites_penaltis(bolao, penaltis)

    classificacao = gerar_classificacao_jogos_faixa(bolao, set(JOGOS_ATE_OITAVAS))
    exportar_classificacao(classificacao, SAIDA_CSV)

    calc_map = {
        _chave_participante(l.participante): (
            l.placar,
            l.vencedor,
            l.gols_casa,
            l.gols_fora,
            l.soma,
        )
        for l in classificacao
    }

    ref_oitavas = carregar_referencia_ate_oitavas()
    ref_excel = carregar_excel_oitavas()
    diffs_oitavas = comparar_classificacoes(
        calc_map, ref_oitavas, rotulo_ref="classificacao_18avos", nomes_bolao=nomes_bolao
    )
    diffs_excel = comparar_classificacoes(
        calc_map, ref_excel, rotulo_ref="excel", nomes_bolao=nomes_bolao
    )
    exportar_relatorio_diff(diffs_oitavas + diffs_excel, RELATORIO_CSV)

    print(f"Arquivos lidos ({len(usados)}):")
    for path in usados:
        print(f"  - {path.name}")
    print(f"Palpites importados: {len(palpites_csv)} entradas")
    print(f"Palpites alterados vs bolao.csv: {alterados}")
    print(f"\nClassificacao recalculada: {SAIDA_CSV}")
    print(f"Relatorio de diferencas: {RELATORIO_CSV}\n")

    print("TOP 10 recalculado (J1-J96):")
    for linha in classificacao[:10]:
        print(
            f"  {linha.posicao:>2}. {linha.participante:<28} "
            f"{linha.placar:>3} {linha.vencedor:>4} {linha.gols_casa:>4} {linha.gols_fora:>4} {linha.soma:>4}"
        )

    print(f"\n=== vs classificacao_18avos ({len(diffs_oitavas)} divergencias) ===")
    if not diffs_oitavas:
        print("  OK — bate com a referencia congelada ate as oitavas.")
    else:
        for diff in diffs_oitavas[:20]:
            print(f"  {diff.participante}: {diff.campo} calc={diff.calculado} ref={diff.referencia}")
        if len(diffs_oitavas) > 20:
            print(f"  ... +{len(diffs_oitavas) - 20} linhas no CSV")

    print(f"\n=== vs Excel ({len(diffs_excel)} divergencias) ===")
    if not diffs_excel:
        print("  OK — bate com a secao oitavas do Excel.")
    else:
        for diff in diffs_excel[:20]:
            print(f"  {diff.participante}: {diff.campo} calc={diff.calculado} ref={diff.referencia}")
        if len(diffs_excel) > 20:
            print(f"  ... +{len(diffs_excel) - 20} linhas no CSV")

    return 0 if not diffs_oitavas else 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Valida palpites dos participantes ate J96.")
    parser.add_argument(
        "--dir",
        type=Path,
        default=PALPITES_PARTICIPANTES_DIR,
        help="Pasta com CSVs dos participantes",
    )
    args = parser.parse_args()
    raise SystemExit(validar_palpites(diretorio=args.dir))
