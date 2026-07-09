"""Importa jogos e palpites das quartas (J97-J100) e encerra baseline das oitavas (J96)."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.data_paths import (
    BOLAO_CSV,
    CLASSIFICACAO_18AVOS_CSV,
    PALPITES_PENALTIS_CSV,
    PLANILHA_QUARTAS_CSV,
    RESULTADOS_CSV,
    SNAPSHOT_JSON,
    ensure_data_layout,
)
from src.penaltis import carregar_palpites_penaltis, exportar_palpites_penaltis

DATA_DIR = BASE_DIR / "data"

JOGOS_QUARTAS: dict[int, tuple[str, str]] = {
    97: ("França", "Marrocos"),
    98: ("Espanha", "Bélgica"),
    99: ("Noruega", "Inglaterra"),
    100: ("Argentina", "Suíça"),
}

PALPITE_PADRAO = (1, 2)
TITULO_BLOCO = "JOGOS 97 a 100"
OITAVAS_MAX_JOGO = 96

NOME_ALIASES = {
    "cornorato": "matheus honorato",
}

JOGO_COL_RE = re.compile(r"^JOGO (\d+) \[(.+)\]$")


def _chave_participante(nome: str) -> str:
    from src.bandeiras import _normalizar

    chave = _normalizar(nome).strip().lower()
    return NOME_ALIASES.get(chave, chave)


def _parse_gols_palpite(valor: str) -> int | None:
    valor = (valor or "").strip().rstrip("+")
    if not valor.isdigit():
        return None
    return int(valor)


def _carregar_participantes_bolao(path: Path) -> list[str]:
    from src.thdfm_parser import parse_thdfm_csv

    return parse_thdfm_csv(path).participantes


def _is_palpite_row_quartas(row: list[str]) -> bool:
    from src.thdfm_parser import DATA_RE, JOGO_RE, _cell

    nome = _cell(row, 1)
    casa = _cell(row, 2)
    sep = _cell(row, 3).lower()
    fora = _cell(row, 4)

    if not nome or nome.upper() == "PLACAR":
        return False
    if JOGO_RE.match(nome):
        return False
    if DATA_RE.match(nome):
        return False
    if sep != "x":
        return False
    if _parse_gols_palpite(casa) is None or _parse_gols_palpite(fora) is None:
        return False
    return True


def carregar_palpites_planilha_quartas(
    path: Path,
) -> tuple[dict[tuple[str, int], tuple[int, int]], dict[tuple[str, int], str]]:
    """Extrai palpites J97-J100 da planilha THDFM (ignora Acertou/Vencedor/Quesito)."""
    from src.thdfm_parser import JOGO_RE, _cell

    palpites: dict[tuple[str, int], tuple[int, int]] = {}
    penaltis: dict[tuple[str, int], str] = {}
    jogo_atual: int | None = None

    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        for row in reader:
            label = _cell(row, 1)
            jogo_match = JOGO_RE.match(label)
            if jogo_match:
                jogo_id = int(jogo_match.group(1))
                jogo_atual = jogo_id if jogo_id in JOGOS_QUARTAS else None
                continue
            if jogo_atual is None or label.upper() == "PLACAR":
                continue
            if not _is_palpite_row_quartas(row):
                continue

            nome = _chave_participante(_cell(row, 1))
            casa = _parse_gols_palpite(_cell(row, 2))
            fora = _parse_gols_palpite(_cell(row, 4))
            if casa is None or fora is None:
                continue
            palpites[(nome, jogo_atual)] = (casa, fora)

            time_pen = _cell(row, 5)
            if casa == fora and time_pen and time_pen not in {"-", "--"}:
                penaltis[(nome, jogo_atual)] = time_pen

    return palpites, penaltis


def _linha_separador() -> str:
    return ",,,x,,,,,x,,,,,,,,,\n"


def _linha_jogo(jogo_id: int, casa: str, fora: str) -> str:
    return f",Jogo {jogo_id},{casa},x,{fora},,,,,x,,,,,,,,,\n"


def _linha_placar_vazio() -> str:
    return ",PLACAR,,x,,--,,,x,,,,,,,,,\n"


def _linha_palpite(nome: str, casa: int, fora: int) -> str:
    return f",{nome},{casa},x,{fora},,,,,x,,,,,,,,,\n"


def _remover_linhas_vazias_finais(linhas: list[str]) -> list[str]:
    while linhas and not linhas[-1].strip():
        linhas.pop()
    while linhas:
        ultima = linhas[-1].strip()
        if ultima and all(parte.strip() == "" or parte.strip().lower() == "x" for parte in ultima.split(",")):
            linhas.pop()
        else:
            break
    return linhas


def _bolao_ja_tem_jogo(linhas: list[str], jogo_id: int) -> bool:
    rotulo = f",Jogo {jogo_id},"
    return any(rotulo in linha for linha in linhas)


def _extrair_jogo_id(linha: str) -> int | None:
    if ",Jogo " not in linha:
        return None
    partes = linha.split(",")
    if len(partes) < 2:
        return None
    match = re.match(r"Jogo (\d+)", partes[1].strip())
    if not match:
        return None
    return int(match.group(1))


def _parse_int_linha(valor: str) -> int | None:
    valor = (valor or "").strip()
    if not valor.isdigit():
        return None
    return int(valor)


def _atualizar_linha_palpite(linha: str, casa: int, fora: int) -> str:
    partes = linha.rstrip("\r\n").split(",")
    while len(partes) < 5:
        partes.append("")
    partes[2] = str(casa)
    partes[4] = str(fora)
    newline = "\n" if linha.endswith("\n") else ""
    return ",".join(partes) + newline


def _mapa_nomes_bolao(bolao_path: Path) -> dict[str, str]:
    participantes = _carregar_participantes_bolao(bolao_path)
    return {_chave_participante(nome): nome.strip() for nome in participantes}


def _mesclar_penaltis_quartas(
    penaltis: dict[tuple[str, int], str],
    nomes_bolao: dict[str, str],
) -> None:
    existentes = carregar_palpites_penaltis(PALPITES_PENALTIS_CSV)
    for (chave, jogo_id), time_passa in penaltis.items():
        participante = nomes_bolao.get(chave, chave)
        existentes[(participante, jogo_id)] = time_passa
    exportar_palpites_penaltis(existentes, PALPITES_PENALTIS_CSV)


def _aplicar_palpites_quartas(
    palpites: dict[tuple[str, int], tuple[int, int]],
    *,
    bolao_path: Path,
) -> int:
    linhas = bolao_path.read_text(encoding="utf-8-sig").splitlines(keepends=True)
    if not _bolao_ja_tem_jogo(linhas, 97):
        raise RuntimeError("Jogos 97+ ainda nao existem em bolao.csv; rode importar_quartas()")

    jogo_atual: int | None = None
    alteracoes = 0

    for indice, linha in enumerate(linhas):
        jogo_id = _extrair_jogo_id(linha)
        if jogo_id is not None:
            jogo_atual = jogo_id
            continue
        if jogo_atual not in JOGOS_QUARTAS:
            continue
        if not linha.startswith(","):
            continue

        partes = linha.split(",")
        if len(partes) < 5:
            continue
        nome = partes[1].strip()
        if not nome or nome.upper() == "PLACAR":
            continue

        chave = _chave_participante(nome)
        palpite = palpites.get((chave, jogo_atual))
        if palpite is None:
            continue

        casa, fora = palpite
        atual_casa = _parse_int_linha(partes[2])
        atual_fora = _parse_int_linha(partes[4])
        if atual_casa != casa or atual_fora != fora:
            linhas[indice] = _atualizar_linha_palpite(linha, casa, fora)
            alteracoes += 1

    if alteracoes:
        bolao_path.write_text("".join(linhas), encoding="utf-8-sig")
    return alteracoes


def _atualizar_resultados(path: Path) -> None:
    existentes: dict[int, tuple[str, str, str]] = {}
    if path.exists():
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                existentes[int(row["jogo_id"])] = (
                    row.get("gols_casa", "").strip(),
                    row.get("gols_fora", "").strip(),
                    row.get("vencedor_penaltis", "").strip(),
                )

    max_id = max(max(existentes) if existentes else 0, max(JOGOS_QUARTAS))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["jogo_id", "gols_casa", "gols_fora", "vencedor_penaltis"])
        for jogo_id in range(1, max_id + 1):
            casa, fora, pen = existentes.get(jogo_id, ("", "", ""))
            writer.writerow([jogo_id, casa, fora, pen])


def _exportar_classificacao_18avos(path: Path) -> None:
    from src.ranking import (
        JOGOS_32_AVOS,
        JOGOS_FASE_GRUPOS,
        JOGOS_OITAVAS,
        gerar_classificacao_jogos_faixa,
    )
    from src.cli import carregar_bolao

    bolao = carregar_bolao()
    ids = JOGOS_FASE_GRUPOS | JOGOS_32_AVOS | JOGOS_OITAVAS
    classificacao = gerar_classificacao_jogos_faixa(bolao, ids)

    linhas = [
        "CLASSIFICAÇÃO ATUAL - FASE DE GRUPOS + 32 AVOS + OITAVAS (ORDENADA);;;;;;;\n",
        ";Nomes;Placar;Vencedor;Gols casa;Gols fora;Soma dos pontos;\n",
    ]
    for linha in classificacao:
        nome = linha.participante.strip()
        linhas.append(
            f"{linha.posicao};{nome};{linha.placar};{linha.vencedor};"
            f"{linha.gols_casa};{linha.gols_fora};{linha.soma};\n"
        )
    linhas.append(";;;;;;;\n")
    path.write_text("".join(linhas), encoding="utf-8-sig")


def encerrar_oitavas(*, snapshot_path: Path = SNAPSHOT_JSON) -> None:
    """Congela classificacao ate J96 (pos Suica x Colombia)."""
    from src.cli import carregar_bolao, _classificacao_jogos
    from src.snapshot import salvar_snapshot

    bolao = carregar_bolao()
    realizados = [jogo for jogo in bolao.jogos if jogo.realizado and jogo.id <= OITAVAS_MAX_JOGO]
    if len(realizados) < OITAVAS_MAX_JOGO:
        faltando = sorted(
            jogo_id
            for jogo_id in range(89, OITAVAS_MAX_JOGO + 1)
            if jogo_id not in {j.id for j in realizados}
        )
        raise RuntimeError(f"Oitavas incompletas; faltam resultados: {faltando}")

    _exportar_classificacao_18avos(CLASSIFICACAO_18AVOS_CSV)
    classificacao = _classificacao_jogos(bolao)
    salvar_snapshot(
        snapshot_path,
        classificacao,
        jogos_realizados=len(realizados),
        jogos_ids=[jogo.id for jogo in sorted(realizados, key=lambda j: j.id)],
    )
    print(
        f"Oitavas encerradas: referencia em {CLASSIFICACAO_18AVOS_CSV.name}, "
        f"snapshot com {len(realizados)} jogos realizados."
    )


def importar_quartas(
    *,
    bolao_path: Path = BOLAO_CSV,
    planilha_path: Path = PLANILHA_QUARTAS_CSV,
    resultados_path: Path = RESULTADOS_CSV,
    palpite_padrao: tuple[int, int] = PALPITE_PADRAO,
    encerrar: bool = True,
) -> None:
    if not planilha_path.exists():
        raise FileNotFoundError(f"Planilha das quartas nao encontrada: {planilha_path}")

    if encerrar:
        encerrar_oitavas()

    palpites_planilha, penaltis = carregar_palpites_planilha_quartas(planilha_path)
    if not palpites_planilha:
        raise ValueError(f"Nenhum palpite J97-J100 encontrado em {planilha_path.name}")

    participantes = _carregar_participantes_bolao(bolao_path)
    nomes_bolao = _mapa_nomes_bolao(bolao_path)

    palpites_por_chave: dict[str, dict[int, tuple[int, int]]] = {}
    for (chave, jogo_id), palpite in palpites_planilha.items():
        palpites_por_chave.setdefault(chave, {})[jogo_id] = palpite

    linhas = bolao_path.read_text(encoding="utf-8-sig").splitlines(keepends=True)
    linhas = _remover_linhas_vazias_finais(linhas)

    if _bolao_ja_tem_jogo(linhas, 97):
        alteracoes = _aplicar_palpites_quartas(palpites_planilha, bolao_path=bolao_path)
        _mesclar_penaltis_quartas(penaltis, nomes_bolao)
        print(f"Jogos 97+ ja existiam; sincronizados {alteracoes} palpites.")
        return

    if not _bolao_ja_tem_jogo(linhas, OITAVAS_MAX_JOGO):
        raise RuntimeError(
            f"Jogo {OITAVAS_MAX_JOGO} ainda nao existe em bolao.csv; importe as oitavas antes."
        )

    bloco: list[str] = []
    bloco.append(_linha_separador())
    bloco.append(f",09 DE JULHO,{TITULO_BLOCO},,,,,,,,,,,,,,\n")

    for jogo_id in sorted(JOGOS_QUARTAS):
        casa, fora = JOGOS_QUARTAS[jogo_id]
        bloco.append(_linha_separador())
        bloco.append(_linha_jogo(jogo_id, casa, fora))
        bloco.append(_linha_placar_vazio())
        for nome in participantes:
            chave = _chave_participante(nome)
            palpite = palpites_por_chave.get(chave, {}).get(jogo_id, palpite_padrao)
            bloco.append(_linha_palpite(nome, palpite[0], palpite[1]))
        bloco.append(_linha_separador())

    with bolao_path.open("w", encoding="utf-8-sig", newline="") as handle:
        handle.writelines(linhas)
        handle.writelines(bloco)

    _atualizar_resultados(resultados_path)
    _mesclar_penaltis_quartas(penaltis, nomes_bolao)

    carregados = sum(1 for chave in nomes_bolao if chave in palpites_por_chave)
    print(
        f"Importados jogos {min(JOGOS_QUARTAS)}-{max(JOGOS_QUARTAS)} em {bolao_path.name}"
    )
    print(f"Palpites carregados de {carregados} participantes (planilha THDFM)")


def atualizar_palpites_quartas(
    *,
    bolao_path: Path = BOLAO_CSV,
    planilha_path: Path = PLANILHA_QUARTAS_CSV,
) -> int:
    if not planilha_path.exists():
        raise FileNotFoundError(f"Planilha das quartas nao encontrada: {planilha_path}")

    palpites, penaltis = carregar_palpites_planilha_quartas(planilha_path)
    if not palpites:
        raise ValueError(f"Nenhum palpite J97-J100 encontrado em {planilha_path.name}")

    alteracoes = _aplicar_palpites_quartas(palpites, bolao_path=bolao_path)
    _mesclar_penaltis_quartas(penaltis, _mapa_nomes_bolao(bolao_path))
    print(f"Sincronizados {alteracoes} palpites (J97-J100) a partir de {planilha_path.name}")
    return alteracoes


if __name__ == "__main__":
    import argparse

    ensure_data_layout(DATA_DIR)

    parser = argparse.ArgumentParser(description="Importa quartas de final e encerra oitavas.")
    parser.add_argument(
        "--atualizar",
        action="store_true",
        help="Atualiza palpites existentes a partir da planilha THDFM",
    )
    parser.add_argument(
        "--sem-encerrar",
        action="store_true",
        help="Nao atualiza referencia/snapshot das oitavas",
    )
    args = parser.parse_args()

    linhas = BOLAO_CSV.read_text(encoding="utf-8-sig").splitlines()
    if args.atualizar or _bolao_ja_tem_jogo(linhas, 97):
        if not args.sem_encerrar:
            encerrar_oitavas()
        atualizar_palpites_quartas()
    else:
        importar_quartas(encerrar=not args.sem_encerrar)
