from __future__ import annotations

import ssl
import urllib.error
import urllib.request
import warnings
from pathlib import Path

from src.bandeiras import TIMES_ISO

BASE_DIR = Path(__file__).resolve().parent.parent
FLAG_DIR = BASE_DIR / "data" / "flags"
FLAGCDN_BASE = "https://flagcdn.com/w80"
USER_AGENT = "THDFM-Bolao/1.0"

# Códigos que não batem 1:1 com o ISO no flagcdn.
ISO_PARA_FLAGCDN: dict[str, str] = {
    "SCO": "gb-sct",
    "GB": "gb-eng",
}

_aviso_ssl_emitido = False


def codigos_bandeira_necessarios() -> set[str]:
    codigos = set(TIMES_ISO.values())
    codigos.add("SCO")
    return codigos


def codigo_flagcdn(iso: str) -> str:
    codigo = iso.upper()
    return ISO_PARA_FLAGCDN.get(codigo, codigo).lower()


def caminho_bandeira(iso: str) -> Path:
    return FLAG_DIR / f"{iso.upper()}.png"


def _contextos_ssl() -> list[ssl.SSLContext]:
    contextos: list[ssl.SSLContext] = [ssl.create_default_context()]
    try:
        import certifi

        contextos.insert(0, ssl.create_default_context(cafile=certifi.where()))
    except ImportError:
        pass

    contexto_inseguro = ssl.create_default_context()
    contexto_inseguro.check_hostname = False
    contexto_inseguro.verify_mode = ssl.CERT_NONE
    contextos.append(contexto_inseguro)
    return contextos


def _baixar_url(url: str) -> bytes:
    global _aviso_ssl_emitido
    ultimo_erro: Exception | None = None
    requisicao = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    for indice, contexto in enumerate(_contextos_ssl()):
        try:
            with urllib.request.urlopen(requisicao, context=contexto, timeout=20) as resposta:
                return resposta.read()
        except (urllib.error.URLError, TimeoutError, OSError) as erro:
            ultimo_erro = erro
            if indice == len(_contextos_ssl()) - 1 and not _aviso_ssl_emitido:
                warnings.warn(
                    "Download de bandeiras usando verificacao SSL relaxada "
                    f"({erro}). As imagens serao salvas em cache local.",
                    stacklevel=2,
                )
                _aviso_ssl_emitido = True

    raise RuntimeError(f"Nao foi possivel baixar {url}") from ultimo_erro


def baixar_bandeira(iso: str, *, forcar: bool = False) -> Path:
    codigo = iso.upper()
    destino = caminho_bandeira(codigo)
    if destino.exists() and not forcar:
        return destino

    FLAG_DIR.mkdir(parents=True, exist_ok=True)
    slug = codigo_flagcdn(codigo)
    url = f"{FLAGCDN_BASE}/{slug}.png"
    destino.write_bytes(_baixar_url(url))
    return destino


def garantir_bandeira(iso: str) -> Path:
    destino = caminho_bandeira(iso)
    if destino.exists():
        return destino
    return baixar_bandeira(iso)


def baixar_todas_bandeiras(*, forcar: bool = False) -> tuple[int, int, list[str]]:
    sucesso = 0
    falhas: list[str] = []
    for codigo in sorted(codigos_bandeira_necessarios()):
        try:
            baixar_bandeira(codigo, forcar=forcar)
            sucesso += 1
        except Exception as erro:
            falhas.append(f"{codigo}: {erro}")
    return sucesso, len(falhas), falhas


def bandeira_existe(iso: str) -> bool:
    return caminho_bandeira(iso).exists()
