"""Organiza exports gerados em data/ultimo/ e remove arquivos legados."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

ULTIMO_DIR_NAME = "ultimo"

EXPORTS_ESTAVEIS: dict[str, str] = {
    "classificacao_png": "classificacao.png",
    "classificacao_txt": "classificacao.txt",
    "classificacao_csv": "classificacao.csv",
    "premio_a_png": "premio_a.png",
    "premio_a_csv": "premio_a.csv",
    "fase_32avos_png": "fase_32avos.png",
    "fase_grupos_32avos_png": "fase_grupos_mais_32avos.png",
    "rodada_png": "rodada.png",
    "ranking_grupos_txt": "ranking_grupos.txt",
}

LEGACY_GLOBS = (
    "rodada_j*.png",
    "palpites_j*.png",
    "palpites_provisorios_j*.png",
    "classificacao_grupo.png",
    "classificacao_grupo.txt",
    "classificacao_premio_a.png",
    "classificacao_32avos.png",
    "classificacao_grupos_32avos.png",
    "classificacao_fase_*.png",
    "classificacao_fase_*.txt",
)


def ultimo_dir(data_dir: Path) -> Path:
    destino = data_dir / ULTIMO_DIR_NAME
    destino.mkdir(parents=True, exist_ok=True)
    return destino


def caminho_ultimo(data_dir: Path, chave: str) -> Path:
    if chave not in EXPORTS_ESTAVEIS:
        raise KeyError(f"Export desconhecido: {chave}")
    return ultimo_dir(data_dir) / EXPORTS_ESTAVEIS[chave]


def caminho_fase(data_dir: Path, fase_id: str, extensao: str) -> Path:
    return ultimo_dir(data_dir) / f"fase_{fase_id}.{extensao}"


def caminho_palpites(data_dir: Path, provisorio: bool, extensao: str) -> Path:
    prefixo = "palpites_provisorios" if provisorio else "palpites"
    return ultimo_dir(data_dir) / f"{prefixo}.{extensao}"


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
    manifest: dict[str, str] = {}
    for chave, nome in EXPORTS_ESTAVEIS.items():
        path = destino / nome
        if path.exists() and chave in descricoes:
            manifest[nome] = descricoes[chave]

    for path in sorted(destino.glob("fase_*.*")):
        if path.name in manifest:
            continue
        if path.name.startswith("fase_") and path.suffix in {".png", ".txt"}:
            fase_id = path.stem.removeprefix("fase_")
            manifest[path.name] = descricoes.get(
                f"fase_{fase_id}_png",
                descricoes.get(
                    f"fase_{fase_id}",
                    f"Pontuacao parcial da fase {fase_id}",
                ),
            )

    for prefixo in ("palpites", "palpites_provisorios"):
        for ext in ("png", "txt"):
            path = destino / f"{prefixo}.{ext}"
            if path.exists():
                manifest[path.name] = descricoes.get(
                    prefixo,
                    "Palpites exportados",
                )

    linhas = [
        f"# Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "# Consulte esta pasta para os arquivos mais recentes do bolao.",
        "",
    ]
    for nome in sorted(manifest):
        linhas.append(f"{nome:<36} {manifest[nome]}")

    manifest_path = destino / "manifest.txt"
    manifest_path.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return manifest_path


def formatar_resumo_ultimo(data_dir: Path) -> str:
    manifest = ultimo_dir(data_dir) / "manifest.txt"
    if not manifest.exists():
        return f"Pasta de exports: {ultimo_dir(data_dir)}"
    return f"Arquivos atuais em {ultimo_dir(data_dir)} (veja manifest.txt)"
