"""Importa jogos e palpites dos 32 avos (J73-J88) para bolao.csv."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
from src.penaltis import (
    carregar_palpites_penaltis_respostas,
    exportar_palpites_penaltis,
)

DATA_DIR = BASE_DIR / "data"
BOLAO_CSV = DATA_DIR / "bolao.csv"
RESULTADOS_CSV = DATA_DIR / "resultados.csv"
RESPOSTAS_32_AVOS = DATA_DIR / "BOLÃO THDFM WC26 - RESPOSTAS 32 AVOS.csv"
PALPITES_PENALTIS_CSV = DATA_DIR / "palpites_penaltis.csv"

JOGOS_32_AVOS: dict[int, tuple[str, str]] = {
    73: ("Canadá", "África do Sul"),
    74: ("Alemanha", "Paraguai"),
    75: ("Holanda", "Marrocos"),
    76: ("Brasil", "Japão"),
    77: ("França", "Suécia"),
    78: ("Costa do Marfim", "Noruega"),
    79: ("México", "Equador"),
    80: ("Inglaterra", "Congo"),
    81: ("Estados Unidos", "Bósnia e Herzegovina"),
    82: ("Bélgica", "Senegal"),
    83: ("Portugal", "Croácia"),
    84: ("Espanha", "Áustria"),
    85: ("Suíça", "Argélia"),
    86: ("Argentina", "Cabo Verde"),
    87: ("Colômbia", "Gana"),
    88: ("Austrália", "Egito"),
}

PALPITE_PADRAO = (1, 2)
DATA_BLOCO = "28 DE JUNHO"
TITULO_BLOCO = "JOGOS 73 a 88"

NOME_ALIASES = {
    "cornorato": "Matheus Honorato",
}

JOGO_COL_RE = re.compile(r"^JOGO (\d+) \[")


def _chave_nome(nome: str) -> str:
    return NOME_ALIASES.get(nome.strip().lower(), nome.strip())


def _parse_int(valor: str) -> int | None:
    valor = (valor or "").strip()
    if not valor.isdigit():
        return None
    return int(valor)


def _carregar_participantes_bolao(path: Path) -> list[str]:
    from src.thdfm_parser import parse_thdfm_csv

    return parse_thdfm_csv(path).participantes


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
                if jogo_id not in JOGOS_32_AVOS:
                    continue
                valores = [_parse_int(row.get(coluna, "")) for coluna in sorted(colunas)]
                nums = [valor for valor in valores if valor is not None]
                if len(nums) >= 2:
                    por_jogo[jogo_id] = (nums[0], nums[1])
            if por_jogo:
                palpites[nome] = por_jogo

    return palpites


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


def atualizar_palpites_32_avos(
    *,
    bolao_path: Path = BOLAO_CSV,
    respostas_path: Path = RESPOSTAS_32_AVOS,
    apenas_participantes: list[str] | None = None,
) -> int:
    """Atualiza palpites J73-J88 no bolao.csv a partir da planilha de respostas."""
    if not respostas_path.exists():
        raise FileNotFoundError(f"Respostas dos 32 avos nao encontradas: {respostas_path}")

    palpites_csv = _carregar_palpites_respostas(respostas_path)
    linhas = bolao_path.read_text(encoding="utf-8-sig").splitlines(keepends=True)

    if not _bolao_ja_tem_jogo(linhas, 73):
        raise RuntimeError("Jogos 73+ ainda nao existem em bolao.csv; rode importar_32_avos()")

    filtro: set[str] | None = None
    if apenas_participantes:
        filtro = {_chave_nome(nome) for nome in apenas_participantes}

    jogo_atual: int | None = None
    alteracoes = 0

    for indice, linha in enumerate(linhas):
        jogo_id = _extrair_jogo_id(linha)
        if jogo_id is not None:
            jogo_atual = jogo_id
            continue
        if jogo_atual not in JOGOS_32_AVOS:
            continue
        if not linha.startswith(","):
            continue

        partes = linha.split(",")
        if len(partes) < 5:
            continue
        nome = partes[1].strip()
        if not nome or nome.upper() == "PLACAR":
            continue

        chave = _chave_nome(nome)
        if filtro is not None and chave not in filtro:
            continue
        palpite = palpites_csv.get(chave, {}).get(jogo_atual)
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

    _exportar_penaltis_respostas(respostas_path)

    print(f"Atualizados {alteracoes} palpites (J73-J88) em {bolao_path.name}")
    return alteracoes


def _exportar_penaltis_respostas(respostas_path: Path) -> None:
    palpites_penaltis = carregar_palpites_penaltis_respostas(respostas_path)
    exportar_palpites_penaltis(palpites_penaltis, PALPITES_PENALTIS_CSV)
    print(f"Palpites de penaltis salvos em {PALPITES_PENALTIS_CSV.name}")


def importar_32_avos(
    *,
    bolao_path: Path = BOLAO_CSV,
    respostas_path: Path = RESPOSTAS_32_AVOS,
    resultados_path: Path = RESULTADOS_CSV,
    palpite_padrao: tuple[int, int] = PALPITE_PADRAO,
) -> None:
    if not respostas_path.exists():
        raise FileNotFoundError(f"Respostas dos 32 avos nao encontradas: {respostas_path}")

    participantes = _carregar_participantes_bolao(bolao_path)
    palpites_csv = _carregar_palpites_respostas(respostas_path)

    linhas = bolao_path.read_text(encoding="utf-8-sig").splitlines(keepends=True)
    linhas = _remover_linhas_vazias_finais(linhas)

    if _bolao_ja_tem_jogo(linhas, 73):
        print("Jogos 73+ ja existem em bolao.csv; importacao ignorada.")
        return

    bloco: list[str] = []
    bloco.append(_linha_separador())
    bloco.append(f",{DATA_BLOCO},{TITULO_BLOCO},,,,,,,,,,,,,,\n")

    for jogo_id in sorted(JOGOS_32_AVOS):
        casa, fora = JOGOS_32_AVOS[jogo_id]
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

    max_id = max(max(existentes) if existentes else 0, max(JOGOS_32_AVOS))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["jogo_id", "gols_casa", "gols_fora", "vencedor_penaltis"])
        for jogo_id in range(1, max_id + 1):
            casa, fora = existentes.get(jogo_id, ("", ""))
            writer.writerow([jogo_id, casa, fora, ""])


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
    print(f"Importados jogos {min(JOGOS_32_AVOS)}-{max(JOGOS_32_AVOS)} em {BOLAO_CSV.name}")
    print(f"Palpites carregados de {len(palpites_csv)} participantes")
    if sem_resposta:
        nomes = ", ".join(sem_resposta)
        print(
            f"Palpite padrao {palpite_padrao[0]}-{palpite_padrao[1]} "
            f"para: {nomes}"
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Importa ou atualiza palpites dos 32 avos.")
    parser.add_argument(
        "--atualizar",
        action="store_true",
        help="Atualiza palpites existentes a partir da planilha de respostas",
    )
    args = parser.parse_args()

    linhas = BOLAO_CSV.read_text(encoding="utf-8-sig").splitlines()
    if args.atualizar or _bolao_ja_tem_jogo(linhas, 73):
        atualizar_palpites_32_avos()
    else:
        importar_32_avos()
