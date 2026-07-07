"""Importa jogos e palpites das oitavas (J89-J96) para bolao.csv."""

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
    PALPITES_PENALTIS_CSV,
    PLANILHA_OITAVAS_CSV,
    RESPOSTAS_OITAVAS_CSV,
    RESULTADOS_CSV,
    ensure_data_layout,
)
from src.penaltis import (
    carregar_palpites_penaltis,
    carregar_palpites_penaltis_respostas,
    exportar_palpites_penaltis,
)

DATA_DIR = BASE_DIR / "data"

JOGOS_OITAVAS: dict[int, tuple[str, str]] = {
    89: ("Paraguai", "França"),
    90: ("Canadá", "Marrocos"),
    91: ("Brasil", "Noruega"),
    92: ("México", "Inglaterra"),
    93: ("Portugal", "Espanha"),
    94: ("Estados Unidos", "Bélgica"),
    95: ("Argentina", "Egito"),
    96: ("Suíça", "Colômbia"),
}

PALPITE_PADRAO = (1, 2)
DATA_BLOCO = "04 DE JULHO"
TITULO_BLOCO = "JOGOS 89 a 96"

NOME_ALIASES = {
    "cornorato": "matheus honorato",
}

JOGO_COL_RE = re.compile(r"^JOGO (\d+) \[(.+)\]$")


def _chave_participante(nome: str) -> str:
    from src.bandeiras import _normalizar

    chave = _normalizar(nome).strip().lower()
    return NOME_ALIASES.get(chave, chave)


def _chave_nome(nome: str) -> str:
    return _chave_participante(nome)


def _parse_int(valor: str) -> int | None:
    valor = (valor or "").strip()
    if not valor.isdigit():
        return None
    return int(valor)


def _carregar_participantes_bolao(path: Path) -> list[str]:
    from src.thdfm_parser import parse_thdfm_csv

    return parse_thdfm_csv(path).participantes


def _palpite_resposta_linha(
    row: dict[str, str],
    jogo_id: int,
    colunas: list[str],
) -> tuple[int, int] | None:
    from src.grupos_ranking import times_iguais

    casa, fora = JOGOS_OITAVAS[jogo_id]
    gols_casa: int | None = None
    gols_fora: int | None = None

    for coluna in colunas:
        match = JOGO_COL_RE.match(coluna.strip())
        if not match or int(match.group(1)) != jogo_id:
            continue
        time_col = match.group(2).strip()
        valor = _parse_int(row.get(coluna, ""))
        if valor is None:
            continue
        if times_iguais(time_col, casa):
            gols_casa = valor
        elif times_iguais(time_col, fora):
            gols_fora = valor

    if gols_casa is None or gols_fora is None:
        return None
    return gols_casa, gols_fora


def validar_colunas_respostas(path: Path) -> list[str]:
    from src.grupos_ranking import times_iguais

    erros: list[str] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        times_por_jogo: dict[int, set[str]] = {}
        for coluna in reader.fieldnames or []:
            match = JOGO_COL_RE.match(coluna.strip())
            if not match:
                continue
            jogo_id = int(match.group(1))
            if jogo_id not in JOGOS_OITAVAS:
                continue
            times_por_jogo.setdefault(jogo_id, set()).add(match.group(2).strip())

    for jogo_id, (casa, fora) in sorted(JOGOS_OITAVAS.items()):
        times_col = times_por_jogo.get(jogo_id, set())
        tem_casa = any(times_iguais(time_col, casa) for time_col in times_col)
        tem_fora = any(times_iguais(time_col, fora) for time_col in times_col)
        if not tem_casa or not tem_fora:
            erros.append(
                f"Jogo {jogo_id}: colunas do formulario {sorted(times_col)!r} "
                f"nao correspondem a {casa!r} x {fora!r}"
            )
    return erros


def _assert_colunas_respostas(path: Path) -> None:
    erros = validar_colunas_respostas(path)
    if erros:
        raise ValueError(
            "Planilha de respostas inconsistente com mandante/visitante:\n" + "\n".join(erros)
        )


def _carregar_palpites_respostas(path: Path) -> dict[str, dict[int, tuple[int, int]]]:
    palpites: dict[str, dict[int, tuple[int, int]]] = {}

    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        colunas_por_jogo: dict[int, list[str]] = {}
        for coluna in reader.fieldnames or []:
            match = JOGO_COL_RE.match(coluna.strip())
            if match:
                colunas_por_jogo.setdefault(int(match.group(1)), []).append(coluna)

        for row in reader:
            nome = _chave_nome(row.get("QUAL SEU NOME NA THDFM") or "")
            if not nome:
                continue
            por_jogo: dict[int, tuple[int, int]] = {}
            for jogo_id, colunas in colunas_por_jogo.items():
                if jogo_id not in JOGOS_OITAVAS:
                    continue
                palpite = _palpite_resposta_linha(row, jogo_id, colunas)
                if palpite is not None:
                    por_jogo[jogo_id] = palpite
            if por_jogo:
                palpites[nome] = por_jogo

    return palpites


def carregar_palpites_planilha_oitavas(
    path: Path,
) -> tuple[dict[tuple[str, int], tuple[int, int]], dict[tuple[str, int], str]]:
    """Extrai palpites e penaltis J89-J96 da planilha THDFM (formato bolao.csv)."""
    from src.thdfm_parser import JOGO_RE, _cell, _is_palpite_row, _parse_int

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
                jogo_atual = jogo_id if jogo_id in JOGOS_OITAVAS else None
                continue
            if jogo_atual is None or label.upper() == "PLACAR":
                continue
            if not _is_palpite_row(row):
                continue

            nome = _chave_participante(_cell(row, 1))
            casa = _parse_int(_cell(row, 2))
            fora = _parse_int(_cell(row, 4))
            if casa is None or fora is None:
                continue
            palpites[(nome, jogo_atual)] = (casa, fora)

            time_pen = _cell(row, 5)
            if casa == fora and time_pen and time_pen not in {"-", "--"}:
                penaltis[(nome, jogo_atual)] = time_pen

    return palpites, penaltis


def _mapa_nomes_bolao(bolao_path: Path) -> dict[str, str]:
    participantes = _carregar_participantes_bolao(bolao_path)
    return {_chave_participante(nome): nome.strip() for nome in participantes}


def _mesclar_penaltis_oitavas(
    penaltis: dict[tuple[str, int], str],
    nomes_bolao: dict[str, str],
) -> None:
    existentes = carregar_palpites_penaltis(PALPITES_PENALTIS_CSV)
    for (chave, jogo_id), time_passa in penaltis.items():
        participante = nomes_bolao.get(chave, chave)
        existentes[(participante, jogo_id)] = time_passa
    exportar_palpites_penaltis(existentes, PALPITES_PENALTIS_CSV)


def _aplicar_palpites_oitavas(
    palpites: dict[tuple[str, int], tuple[int, int]],
    *,
    bolao_path: Path,
    apenas_participantes: list[str] | None = None,
) -> int:
    linhas = bolao_path.read_text(encoding="utf-8-sig").splitlines(keepends=True)
    if not _bolao_ja_tem_jogo(linhas, 89):
        raise RuntimeError("Jogos 89+ ainda nao existem em bolao.csv; rode importar_oitavas()")

    filtro: set[str] | None = None
    if apenas_participantes:
        filtro = {_chave_participante(nome) for nome in apenas_participantes}

    jogo_atual: int | None = None
    alteracoes = 0

    for indice, linha in enumerate(linhas):
        jogo_id = _extrair_jogo_id(linha)
        if jogo_id is not None:
            jogo_atual = jogo_id
            continue
        if jogo_atual not in JOGOS_OITAVAS:
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
        if filtro is not None and chave not in filtro:
            continue
        palpite = palpites.get((chave, jogo_atual))
        if palpite is None:
            continue

        casa, fora = palpite
        atual_casa = _parse_int(partes[2])
        atual_fora = _parse_int(partes[4])
        if atual_casa != casa or atual_fora != fora:
            linhas[indice] = _atualizar_linha_palpite(linha, casa, fora)
            alteracoes += 1

    if alteracoes:
        bolao_path.write_text("".join(linhas), encoding="utf-8-sig")
    return alteracoes


def atualizar_palpites_da_planilha_oitavas(
    *,
    bolao_path: Path = BOLAO_CSV,
    planilha_path: Path = PLANILHA_OITAVAS_CSV,
    apenas_participantes: list[str] | None = None,
) -> int:
    """Sincroniza palpites J89-J96 a partir da planilha oficial das oitavas."""
    if not planilha_path.exists():
        raise FileNotFoundError(f"Planilha das oitavas nao encontrada: {planilha_path}")

    palpites, penaltis = carregar_palpites_planilha_oitavas(planilha_path)
    if not palpites:
        raise ValueError(f"Nenhum palpite J89-J96 encontrado em {planilha_path.name}")

    alteracoes = _aplicar_palpites_oitavas(
        palpites,
        bolao_path=bolao_path,
        apenas_participantes=apenas_participantes,
    )
    _mesclar_penaltis_oitavas(penaltis, _mapa_nomes_bolao(bolao_path))
    print(
        f"Sincronizados {alteracoes} palpites (J89-J96) a partir de {planilha_path.name}"
    )
    return alteracoes


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


def _atualizar_linha_palpite(linha: str, casa: int, fora: int) -> str:
    partes = linha.rstrip("\r\n").split(",")
    while len(partes) < 5:
        partes.append("")
    partes[2] = str(casa)
    partes[4] = str(fora)
    newline = "\n" if linha.endswith("\n") else ""
    return ",".join(partes) + newline


def _exportar_penaltis_respostas(respostas_path: Path) -> None:
    novos = carregar_palpites_penaltis_respostas(respostas_path)
    existentes = carregar_palpites_penaltis(PALPITES_PENALTIS_CSV)
    existentes.update(novos)
    exportar_palpites_penaltis(existentes, PALPITES_PENALTIS_CSV)
    print(f"Palpites de penaltis salvos em {PALPITES_PENALTIS_CSV.name}")


def atualizar_palpites_oitavas(
    *,
    bolao_path: Path = BOLAO_CSV,
    respostas_path: Path = RESPOSTAS_OITAVAS_CSV,
    apenas_participantes: list[str] | None = None,
) -> int:
    """Atualiza palpites J89-J96 no bolao.csv a partir da planilha de respostas."""
    if not respostas_path.exists():
        raise FileNotFoundError(f"Respostas das oitavas nao encontradas: {respostas_path}")

    _assert_colunas_respostas(respostas_path)
    palpites_csv = _carregar_palpites_respostas(respostas_path)
    palpites_flat = {
        (_chave_participante(nome), jogo_id): palpite
        for nome, por_jogo in palpites_csv.items()
        for jogo_id, palpite in por_jogo.items()
    }
    alteracoes = _aplicar_palpites_oitavas(
        palpites_flat,
        bolao_path=bolao_path,
        apenas_participantes=apenas_participantes,
    )

    _exportar_penaltis_respostas(respostas_path)

    print(f"Atualizados {alteracoes} palpites (J89-J96) em {bolao_path.name}")
    return alteracoes


def _atualizar_resultados(path: Path) -> None:
    existentes: dict[int, tuple[str, str]] = {}
    if path.exists():
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                existentes[int(row["jogo_id"])] = (
                    row.get("gols_casa", "").strip(),
                    row.get("gols_fora", "").strip(),
                )

    max_id = max(max(existentes) if existentes else 0, max(JOGOS_OITAVAS))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["jogo_id", "gols_casa", "gols_fora", "vencedor_penaltis"])
        for jogo_id in range(1, max_id + 1):
            casa, fora = existentes.get(jogo_id, ("", ""))
            writer.writerow([jogo_id, casa, fora, ""])


def importar_oitavas(
    *,
    bolao_path: Path = BOLAO_CSV,
    respostas_path: Path = RESPOSTAS_OITAVAS_CSV,
    resultados_path: Path = RESULTADOS_CSV,
    palpite_padrao: tuple[int, int] = PALPITE_PADRAO,
) -> None:
    if not respostas_path.exists():
        raise FileNotFoundError(f"Respostas das oitavas nao encontradas: {respostas_path}")

    _assert_colunas_respostas(respostas_path)
    participantes = _carregar_participantes_bolao(bolao_path)
    palpites_csv = _carregar_palpites_respostas(respostas_path)

    linhas = bolao_path.read_text(encoding="utf-8-sig").splitlines(keepends=True)
    linhas = _remover_linhas_vazias_finais(linhas)

    if _bolao_ja_tem_jogo(linhas, 89):
        print("Jogos 89+ ja existem em bolao.csv; importacao ignorada.")
        return

    if not _bolao_ja_tem_jogo(linhas, 88):
        raise RuntimeError("Jogos 88 ainda nao existem em bolao.csv; importe os 32 avos antes.")

    bloco: list[str] = []
    bloco.append(_linha_separador())
    bloco.append(f",{DATA_BLOCO},{TITULO_BLOCO},,,,,,,,,,,,,,\n")

    for jogo_id in sorted(JOGOS_OITAVAS):
        casa, fora = JOGOS_OITAVAS[jogo_id]
        bloco.append(_linha_separador())
        bloco.append(_linha_jogo(jogo_id, casa, fora))
        bloco.append(_linha_placar_vazio())
        for nome in participantes:
            chave = _chave_nome(nome)
            palpite = palpites_csv.get(chave, {}).get(jogo_id, palpite_padrao)
            bloco.append(_linha_palpite(nome, palpite[0], palpite[1]))
        bloco.append(_linha_separador())

    with bolao_path.open("w", encoding="utf-8-sig", newline="") as handle:
        handle.writelines(linhas)
        handle.writelines(bloco)

    _atualizar_resultados(resultados_path)
    _exportar_penaltis_respostas(respostas_path)
    _reportar(participantes, palpites_csv, palpite_padrao)


def _reportar(
    participantes: list[str],
    palpites_csv: dict[str, dict[int, tuple[int, int]]],
    palpite_padrao: tuple[int, int],
) -> None:
    sem_resposta = [
        nome
        for nome in participantes
        if _chave_nome(nome) not in palpites_csv
    ]
    print(f"Importados jogos {min(JOGOS_OITAVAS)}-{max(JOGOS_OITAVAS)} em {BOLAO_CSV.name}")
    print(f"Palpites carregados de {len(palpites_csv)} participantes")
    if sem_resposta:
        nomes = ", ".join(sem_resposta)
        print(
            f"Palpite padrao {palpite_padrao[0]}-{palpite_padrao[1]} "
            f"para: {nomes}"
        )


if __name__ == "__main__":
    import argparse

    ensure_data_layout(DATA_DIR)

    parser = argparse.ArgumentParser(description="Importa ou atualiza palpites das oitavas.")
    parser.add_argument(
        "--atualizar",
        action="store_true",
        help="Atualiza palpites existentes a partir da planilha de respostas",
    )
    parser.add_argument(
        "--planilha",
        action="store_true",
        help="Sincroniza palpites a partir de BOLÃO THDFM WC26 - Oitavas.csv",
    )
    args = parser.parse_args()

    linhas = BOLAO_CSV.read_text(encoding="utf-8-sig").splitlines()
    if args.planilha:
        atualizar_palpites_da_planilha_oitavas()
    elif args.atualizar or _bolao_ja_tem_jogo(linhas, 89):
        atualizar_palpites_oitavas()
    else:
        importar_oitavas()
