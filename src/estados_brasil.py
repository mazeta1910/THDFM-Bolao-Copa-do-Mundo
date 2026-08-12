"""Times dos estados brasileiros para a proxima atualizacao do grid.

Nomes canonicos:
- estado de uma palavra → "Time do/da/de {Nome}"
- estado composto (ou UF usual no futebol) → "Time do/de {UF}"

Exemplos: "Time do Paraná", "Time do RS".
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EstadoBrasil:
    uf: str
    nome: str
    artigo: str  # "do" | "da" | "de"
    usar_uf_no_nome: bool

    @property
    def codigo(self) -> str:
        return f"BR-{self.uf}"

    @property
    def nome_time(self) -> str:
        rotulo = self.uf if self.usar_uf_no_nome else self.nome
        return f"Time {self.artigo} {rotulo}"


# Grid completo: 26 estados + DF (ordem por regiao).
ESTADOS_BRASIL: tuple[EstadoBrasil, ...] = (
    # Norte
    EstadoBrasil("AC", "Acre", "do", False),
    EstadoBrasil("AP", "Amapá", "do", False),
    EstadoBrasil("AM", "Amazonas", "do", False),
    EstadoBrasil("PA", "Pará", "do", False),
    EstadoBrasil("RO", "Rondônia", "de", False),
    EstadoBrasil("RR", "Roraima", "de", False),
    EstadoBrasil("TO", "Tocantins", "do", False),
    # Nordeste
    EstadoBrasil("AL", "Alagoas", "de", False),
    EstadoBrasil("BA", "Bahia", "da", False),
    EstadoBrasil("CE", "Ceará", "do", False),
    EstadoBrasil("MA", "Maranhão", "do", False),
    EstadoBrasil("PB", "Paraíba", "da", False),
    EstadoBrasil("PE", "Pernambuco", "de", False),
    EstadoBrasil("PI", "Piauí", "do", False),
    EstadoBrasil("RN", "Rio Grande do Norte", "do", True),
    EstadoBrasil("SE", "Sergipe", "de", False),
    # Centro-Oeste
    EstadoBrasil("DF", "Distrito Federal", "do", True),
    EstadoBrasil("GO", "Goiás", "de", False),
    EstadoBrasil("MT", "Mato Grosso", "do", True),
    EstadoBrasil("MS", "Mato Grosso do Sul", "do", True),
    # Sudeste
    EstadoBrasil("ES", "Espírito Santo", "do", True),
    EstadoBrasil("MG", "Minas Gerais", "de", True),
    EstadoBrasil("RJ", "Rio de Janeiro", "do", True),
    EstadoBrasil("SP", "São Paulo", "de", True),
    # Sul
    EstadoBrasil("PR", "Paraná", "do", False),
    EstadoBrasil("RS", "Rio Grande do Sul", "do", True),
    EstadoBrasil("SC", "Santa Catarina", "de", True),
)


def times_estados() -> list[str]:
    return [estado.nome_time for estado in ESTADOS_BRASIL]


def mapa_times_estados_iso() -> dict[str, str]:
    """Nome canonico (apos normalizar acentos) → codigo BR-UF."""
    from src.bandeiras import _normalizar

    mapa: dict[str, str] = {}
    for estado in ESTADOS_BRASIL:
        mapa[_normalizar(estado.nome_time)] = estado.codigo
    return mapa


def aliases_times_estados() -> dict[str, str]:
    """Variantes (apos normalizar) → nome canonico tambem normalizado."""
    from src.bandeiras import _normalizar

    aliases: dict[str, str] = {}
    for estado in ESTADOS_BRASIL:
        canonico_norm = _normalizar(estado.nome_time)
        variantes = {
            estado.nome,
            estado.uf,
            f"Time {estado.artigo} {estado.uf}",
            f"Time {estado.artigo} {estado.nome}",
            f"Selecao {estado.artigo} {estado.nome}",
            f"Selecao {estado.artigo} {estado.uf}",
        }
        for variante in variantes:
            chave = _normalizar(variante)
            if chave == canonico_norm:
                continue
            aliases[chave] = canonico_norm
    return aliases


def ufs_registradas() -> set[str]:
    return {estado.uf for estado in ESTADOS_BRASIL}


def eh_codigo_estado(codigo: str) -> bool:
    return codigo.upper().startswith("BR-") and len(codigo) == 5


def uf_do_codigo(codigo: str) -> str | None:
    if not eh_codigo_estado(codigo):
        return None
    return codigo.upper().split("-", 1)[1]
