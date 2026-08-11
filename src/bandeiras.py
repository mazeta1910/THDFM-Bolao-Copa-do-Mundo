from __future__ import annotations

import unicodedata

from src.estados_brasil import aliases_times_estados, mapa_times_estados_iso, uf_do_codigo


def _normalizar(nome: str) -> str:
    texto = unicodedata.normalize("NFD", nome.strip())
    return "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")


TIMES_ISO: dict[str, str] = {
    "Alemanha": "DE",
    "Argentina": "AR",
    "Argelia": "DZ",
    "Arabia Saudita": "SA",
    "Australia": "AU",
    "Brasil": "BR",
    "Belgica": "BE",
    "Bosnia e Herzegovina": "BA",
    "Cabo Verde": "CV",
    "Canada": "CA",
    "Catar": "QA",
    "Colombia": "CO",
    "Congo": "CD",
    "Coreia do Sul": "KR",
    "Costa do Marfim": "CI",
    "Croacia": "HR",
    "Curacao": "CW",
    "Egito": "EG",
    "Equador": "EC",
    "Espanha": "ES",
    "Estados Unidos": "US",
    "Franca": "FR",
    "Gana": "GH",
    "Haiti": "HT",
    "Holanda": "NL",
    "Inglaterra": "GB",
    "Iraque": "IQ",
    "Ira": "IR",
    "Japao": "JP",
    "Jordania": "JO",
    "Marrocos": "MA",
    "Mexico": "MX",
    "Noruega": "NO",
    "Nova Zelandia": "NZ",
    "Panama": "PA",
    "Paraguai": "PY",
    "Portugal": "PT",
    "Senegal": "SN",
    "Suecia": "SE",
    "Suica": "CH",
    "Tchequia": "CZ",
    "Tunisia": "TN",
    "Turquia": "TR",
    "Uruguai": "UY",
    "Uzbequistao": "UZ",
    "Africa do Sul": "ZA",
    "Austria": "AT",
}

BANDEIRAS_ESPECIAIS: dict[str, str] = {
    "Escocia": chr(0x1F3F4)
    + "".join(chr(c) for c in (0xE0067, 0xE0062, 0xE0073, 0xE0063, 0xE0074, 0xE007F)),
}

# Variantes de grafia usadas na planilha (apos _normalizar).
ALIASES_TIMES: dict[str, str] = {
    "Curacau": "Curacao",
    "Paises Baixos": "Holanda",
    "RD Congo": "Congo",
}


def _aliases_completos() -> dict[str, str]:
    aliases = dict(ALIASES_TIMES)
    aliases.update(aliases_times_estados())
    return aliases


def _chave_time(nome: str) -> str:
    chave = _normalizar(nome)
    return _aliases_completos().get(chave, chave)


def bandeira_iso(codigo: str) -> str:
    uf = uf_do_codigo(codigo)
    if uf:
        # Estados usam a bandeira do Brasil no texto; PNG e gerado localmente.
        return bandeira_iso("BR")
    return "".join(chr(127397 + ord(letra)) for letra in codigo.upper())


def iso_time(nome: str) -> str | None:
    chave = _chave_time(nome)
    if chave in BANDEIRAS_ESPECIAIS:
        return "SCO"
    codigo_estado = mapa_times_estados_iso().get(chave)
    if codigo_estado:
        return codigo_estado
    return TIMES_ISO.get(chave)


def sigla_time(nome: str) -> str:
    codigo = iso_time(nome)
    if not codigo:
        return nome[:3].upper()
    uf = uf_do_codigo(codigo)
    if uf:
        return uf
    return codigo.upper()


def confronto_siglas_placar(
    casa: str,
    fora: str,
    gols_casa: int,
    gols_fora: int,
) -> str:
    return f"{sigla_time(casa)} {gols_casa} x {gols_fora} {sigla_time(fora)}"


def bandeira_time(nome: str) -> str:
    chave = _chave_time(nome)
    if chave in BANDEIRAS_ESPECIAIS:
        return BANDEIRAS_ESPECIAIS[chave]
    codigo = iso_time(nome)
    if codigo:
        return bandeira_iso(codigo)
    return "🏳️"


def confronto_bandeiras(casa: str, fora: str) -> str:
    return f"{bandeira_time(casa)} x {bandeira_time(fora)}"


def titulo_jogo_bandeiras(jogo_id: int, casa: str, fora: str) -> tuple[str, str]:
    return f"Jogo {jogo_id}", confronto_bandeiras(casa, fora)
