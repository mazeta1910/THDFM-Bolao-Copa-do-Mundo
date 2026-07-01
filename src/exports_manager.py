"""Organiza exports gerados em data/ultimo/{png,txt,csv}/ e remove arquivos legados."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

ULTIMO_DIR_NAME = "ultimo"

SUBDIR_POR_EXTENSAO = {
    "png": "png",
    "txt": "txt",
    "csv": "csv",
}

EXPORTS_ESTAVEIS: dict[str, str] = {
    "classificacao_png": "png/classificacao.png",
    "classificacao_txt": "txt/classificacao.txt",
    "classificacao_csv": "csv/classificacao.csv",
    "premio_a_png": "png/premio_a.png",
    "premio_a_csv": "csv/premio_a.csv",
    "fase_32avos_png": "png/fase_32avos.png",
    "fase_grupos_32avos_png": "png/fase_grupos_mais_32avos.png",
    "rodada_png": "png/rodada.png",
    "ranking_grupos_txt": "txt/ranking_grupos.txt",
}

LEGACY_GLOBS = (
    "rodada_j*.png",
    "palpites_j*.png",
    "palpites_provisorios_j*.png",
    "palpites_j*.txt",
    "palpites_provisorios_j*.txt",
    "classificacao_grupo.png",
    "classificacao_grupo.txt",
    "classificacao_premio_a.png",
    "classificacao_32avos.png",
    "classificacao_grupos_32avos.png",
    "classificacao_fase_*.png",
    "classificacao_fase_*.txt",
    "classificacao.csv",
    "premio_a.csv",
    "ranking_grupos.txt",
    "palpites.txt",
    "palpites_provisorios.txt",
)


def _subdir(extensao: str) -> str:
    chave = extensao.lstrip(".").lower()
    if chave not in SUBDIR_POR_EXTENSAO:
        raise ValueError(f"Extensao de export nao suportada: {extensao}")
    return SUBDIR_POR_EXTENSAO[chave]


def ultimo_dir(data_dir: Path) -> Path:
    destino = data_dir / ULTIMO_DIR_NAME
    destino.mkdir(parents=True, exist_ok=True)
    for sub in SUBDIR_POR_EXTENSAO.values():
        (destino / sub).mkdir(parents=True, exist_ok=True)
    return destino


def caminho_ultimo(data_dir: Path, chave: str) -> Path:
    if chave not in EXPORTS_ESTAVEIS:
        raise KeyError(f"Export desconhecido: {chave}")
    return ultimo_dir(data_dir) / EXPORTS_ESTAVEIS[chave]


def caminho_fase(data_dir: Path, fase_id: str, extensao: str) -> Path:
    return ultimo_dir(data_dir) / _subdir(extensao) / f"fase_{fase_id}.{extensao}"


def caminho_palpites(data_dir: Path, provisorio: bool, extensao: str) -> Path:
    prefixo = "palpites_provisorios" if provisorio else "palpites"
    return ultimo_dir(data_dir) / _subdir(extensao) / f"{prefixo}.{extensao}"


def migrar_estrutura_ultimo(data_dir: Path) -> list[str]:
    """Move exports antigos (flat em ultimo/) para png/, txt/ e csv/."""
    destino = data_dir / ULTIMO_DIR_NAME
    if not destino.exists():
        return []

    movidos: list[str] = []
    for sub in SUBDIR_POR_EXTENSAO.values():
        (destino / sub).mkdir(parents=True, exist_ok=True)

    for path in destino.iterdir():
        if not path.is_file() or path.name == "manifest.txt":
            continue
        ext = path.suffix.lstrip(".").lower()
        if ext not in SUBDIR_POR_EXTENSAO:
            continue
        novo = destino / SUBDIR_POR_EXTENSAO[ext] / path.name
        if novo.exists():
            path.unlink()
            movidos.append(f"{path.name} (duplicado removido)")
        else:
            path.rename(novo)
            movidos.append(f"{path.name} -> {SUBDIR_POR_EXTENSAO[ext]}/")
    return movidos


def limpar_exports_legados(data_dir: Path) -> list[str]:
    """Remove exports antigos espalhados em data/ (fora de ultimo/)."""
    removidos: list[str] = []
    for pattern in LEGACY_GLOBS:
        for path in data_dir.glob(pattern):
            if path.is_file():
                path.unlink()
                removidos.append(path.name)
    return sorted(removidos)


def atualizar_manifest(data_dir: Path, descricoes: dict[str, str]) -> Path:
    """Registra o que ha em data/ultimo/ para facilitar achar o ultimo arquivo."""
    destino = ultimo_dir(data_dir)
    migrar_estrutura_ultimo(data_dir)
    manifest: dict[str, str] = {}

    for chave, rel_path in EXPORTS_ESTAVEIS.items():
        path = destino / rel_path
        if path.exists() and chave in descricoes:
            manifest[rel_path] = descricoes[chave]

    for sub in SUBDIR_POR_EXTENSAO.values():
        for path in sorted((destino / sub).glob("fase_*.*")):
            rel = f"{sub}/{path.name}"
            if rel in manifest:
                continue
            if path.suffix in {".png", ".txt"}:
                fase_id = path.stem.removeprefix("fase_")
                manifest[rel] = descricoes.get(
                    f"fase_{fase_id}_png",
                    descricoes.get(
                        f"fase_{fase_id}",
                        f"Pontuacao parcial da fase {fase_id}",
                    ),
                )

    for prefixo in ("palpites", "palpites_provisorios"):
        for ext in ("png", "txt"):
            rel = f"{ext}/{prefixo}.{ext}"
            path = destino / rel
            if path.exists():
                manifest[rel] = descricoes.get(prefixo, "Palpites exportados")

    linhas = [
        f"# Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "# Consulte data/ultimo/png, txt/ e csv/ para os arquivos mais recentes.",
        "",
    ]
    for rel in sorted(manifest):
        linhas.append(f"{rel:<40} {manifest[rel]}")

    manifest_path = destino / "manifest.txt"
    manifest_path.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return manifest_path


def formatar_resumo_ultimo(data_dir: Path) -> str:
    manifest = ultimo_dir(data_dir) / "manifest.txt"
    base = ultimo_dir(data_dir)
    if not manifest.exists():
        return f"Pasta de exports: {base} (png/, txt/, csv/)"
    return f"Arquivos atuais em {base} (veja manifest.txt; subpastas png/, txt/, csv/)"
