"""Caminhos padronizados em data/: base/, fontes/ e ultimo/."""

from __future__ import annotations

import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BASE_DATA_DIR = DATA_DIR / "base"
FONTES_DATA_DIR = DATA_DIR / "fontes"
PARTICIPANTES_DIR = DATA_DIR / "participantes"
PALPITES_PARTICIPANTES_DIR = DATA_DIR / "palpites participantes"
PARTICIPANTES_MANIFEST = PARTICIPANTES_DIR / "manifest.json"

ARQUIVOS_BASE = (
    "bolao.csv",
    "resultados.csv",
    "classificacao_snapshot.json",
)

ARQUIVOS_FONTES = (
    "classificacao_referencia.csv",
    "BOLÃO THDFM WC26 - CLASSIFICAÇÃO PROVISÓRIA.csv",
    "BOLÃO THDFM WC26 - CLASSIFICAÇÃO PROVISÓRIA (1).csv",
    "BOLÃO THDFM WC26 - CRAVADURA.csv",
    "BOLÃO THDFM WC26 - RESPOSTAS PRIMEIRA FASE E CRAVADURA.csv",
    "BOLÃO THDFM WC26 - RESPOSTAS 32 AVOS.csv",
    "BOLÃO THDFM WC26 - RESPOSTAS OITAVAS.csv",
    "BOLÃO THDFM WC26 - Oitavas.csv",
    "BOLÃO THDFM WC26 - Quartas.csv",
    "Planilha Classificações Reais.csv",
    "Planilha Classificações Reais.xlsx",
    "palpites_penaltis.csv",
    "Export CSV palpites bolao.csv",
)

NOMES_IGNORADOS_BOLAO = {
    "resultados.csv",
    "classificacao.csv",
    "classificacao_referencia.csv",
    "classificacao_snapshot.json",
    "palpites_penaltis.csv",
    *ARQUIVOS_FONTES,
}


def _mover_se_existir(origem: Path, destino: Path) -> str | None:
    if not origem.is_file():
        return None
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists():
        origem.unlink()
        return f"{origem.name} (legado removido; ja em {destino.parent.name}/)"
    shutil.move(str(origem), str(destino))
    return f"{origem.name} -> {destino.parent.name}/"


def migrar_estrutura_data(data_dir: Path | None = None) -> list[str]:
    """Move arquivos soltos na raiz de data/ para base/ ou fontes/."""
    raiz = data_dir or DATA_DIR
    base_dir = raiz / "base"
    fontes_dir = raiz / "fontes"
    base_dir.mkdir(parents=True, exist_ok=True)
    fontes_dir.mkdir(parents=True, exist_ok=True)

    movidos: list[str] = []
    for nome in ARQUIVOS_BASE:
        msg = _mover_se_existir(raiz / nome, base_dir / nome)
        if msg:
            movidos.append(msg)
    for nome in ARQUIVOS_FONTES:
        msg = _mover_se_existir(raiz / nome, fontes_dir / nome)
        if msg:
            movidos.append(msg)
    return movidos


def ensure_data_layout(data_dir: Path | None = None) -> list[str]:
    """Garante pastas e migra legados da raiz de data/."""
    raiz = data_dir or DATA_DIR
    raiz.mkdir(parents=True, exist_ok=True)
    (raiz / "base").mkdir(parents=True, exist_ok=True)
    (raiz / "fontes").mkdir(parents=True, exist_ok=True)
    (raiz / "participantes").mkdir(parents=True, exist_ok=True)
    (raiz / "palpites participantes").mkdir(parents=True, exist_ok=True)
    return migrar_estrutura_data(raiz)


def caminho_base(nome: str, *, data_dir: Path | None = None) -> Path:
    """Caminho canonico em data/base/ (sempre usado para gravar)."""
    raiz = data_dir or DATA_DIR
    return raiz / "base" / nome


def caminho_fonte(nome: str, *, data_dir: Path | None = None) -> Path:
    """Caminho canonico em data/fontes/ (sempre usado para gravar)."""
    raiz = data_dir or DATA_DIR
    return raiz / "fontes" / nome


def resolver_arquivo_base(nome: str, *, data_dir: Path | None = None) -> Path:
    canonico = caminho_base(nome, data_dir=data_dir)
    if canonico.exists():
        return canonico
    legado = (data_dir or DATA_DIR) / nome
    if legado.exists():
        return legado
    return canonico


def resolver_arquivo_fonte(nome: str, *, data_dir: Path | None = None) -> Path:
    canonico = caminho_fonte(nome, data_dir=data_dir)
    if canonico.exists():
        return canonico
    legado = (data_dir or DATA_DIR) / nome
    if legado.exists():
        return legado
    return canonico


def resolver_bolao_csv(
    data_dir: Path | None = None,
    *,
    downloads: Path | None = None,
) -> Path:
    raiz = data_dir or DATA_DIR
    principal = resolver_arquivo_base("bolao.csv", data_dir=raiz)
    if principal.exists():
        return principal

    candidatos = [
        path
        for path in sorted(_iter_csvs_candidatos_bolao(raiz), key=lambda item: item.stat().st_mtime, reverse=True)
        if path.name.lower() not in NOMES_IGNORADOS_BOLAO
        and "fase de grupos" in path.name.lower()
    ]
    if candidatos:
        return candidatos[0]

    if downloads is not None:
        fallback = downloads / "BOLÃO THDFM WC26 - Fase de grupos.csv"
        if fallback.exists():
            return fallback
    return principal


def _iter_csvs_candidatos_bolao(data_dir: Path) -> list[Path]:
    pastas = (data_dir / "fontes", data_dir)
    vistos: set[Path] = set()
    candidatos: list[Path] = []
    for pasta in pastas:
        if not pasta.exists():
            continue
        for path in pasta.glob("*.csv"):
            if path not in vistos:
                vistos.add(path)
                candidatos.append(path)
    return candidatos


def candidatos_referencia_geral(
    data_dir: Path | None = None,
    *,
    downloads: Path | None = None,
) -> list[Path]:
    raiz = data_dir or DATA_DIR
    nomes = (
        "classificacao_18avos.csv",
        "BOLÃO THDFM WC26 - CLASSIFICAÇÃO PROVISÓRIA (1).csv",
        "classificacao_referencia.csv",
        "BOLÃO THDFM WC26 - CLASSIFICAÇÃO PROVISÓRIA.csv",
    )
    candidatos: list[Path] = []
    for nome in nomes:
        if nome == "classificacao_18avos.csv":
            candidatos.append(resolver_arquivo_base(nome, data_dir=raiz))
        else:
            candidatos.append(resolver_arquivo_fonte(nome, data_dir=raiz))
    if downloads is not None:
        candidatos.extend(
            [
                downloads / "BOLÃO THDFM WC26 - CLASSIFICAÇÃO PROVISÓRIA (1).csv",
                downloads / "BOLÃO THDFM WC26 - CLASSIFICAÇÃO PROVISÓRIA.csv",
            ]
        )
    return candidatos


# Caminhos canonicos usados pelo programa
BOLAO_CSV = caminho_base("bolao.csv")
RESULTADOS_CSV = caminho_base("resultados.csv")
SNAPSHOT_JSON = caminho_base("classificacao_snapshot.json")
CLASSIFICACAO_18AVOS_CSV = caminho_base("classificacao_18avos.csv")
REFERENCIA_CSV = caminho_fonte("classificacao_referencia.csv")
REFERENCIA_GERAL_CSV = caminho_fonte("BOLÃO THDFM WC26 - CLASSIFICAÇÃO PROVISÓRIA (1).csv")
CRAVADURA_CSV = caminho_fonte("BOLÃO THDFM WC26 - CRAVADURA.csv")
CLASSIFICACOES_REAIS_CSV = caminho_fonte("Planilha Classificações Reais.csv")
PALPITES_PRIMEIRA_FASE_CSV = caminho_fonte(
    "BOLÃO THDFM WC26 - RESPOSTAS PRIMEIRA FASE E CRAVADURA.csv"
)
RESPOSTAS_32_AVOS_CSV = caminho_fonte("BOLÃO THDFM WC26 - RESPOSTAS 32 AVOS.csv")
RESPOSTAS_OITAVAS_CSV = caminho_fonte("BOLÃO THDFM WC26 - RESPOSTAS OITAVAS.csv")
PLANILHA_OITAVAS_CSV = caminho_fonte("BOLÃO THDFM WC26 - Oitavas.csv")
PLANILHA_QUARTAS_CSV = caminho_fonte("BOLÃO THDFM WC26 - Quartas.csv")
PALPITES_PENALTIS_CSV = caminho_fonte("palpites_penaltis.csv")
