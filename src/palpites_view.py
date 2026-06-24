from __future__ import annotations

from dataclasses import dataclass

from src.models import BolaoData, Jogo
from src.scoring import pontos_jogo


@dataclass
class PalpiteLinha:
    participante: str
    palpite_casa: int
    palpite_fora: int
    pontos: int | None = None

    @property
    def placar_texto(self) -> str:
        return f"{self.palpite_casa}x{self.palpite_fora}"


@dataclass
class PalpitesPorJogo:
    jogo: Jogo
    linhas: list[PalpiteLinha]


def _ordenar_linhas(jogo: Jogo, linhas: list[PalpiteLinha]) -> list[PalpiteLinha]:
    if jogo.realizado:
        return sorted(
            linhas,
            key=lambda linha: (-(linha.pontos or 0), linha.participante.strip().lower()),
        )
    return sorted(linhas, key=lambda linha: linha.participante.strip().lower())


def listar_palpites_jogos(bolao: BolaoData, jogo_ids: list[int]) -> list[PalpitesPorJogo]:
    if not jogo_ids:
        raise ValueError("Informe pelo menos um jogo com --jogo.")

    jogos_por_id = {jogo.id: jogo for jogo in bolao.jogos}
    palpites_por_jogo: dict[int, list[PalpiteLinha]] = {jogo_id: [] for jogo_id in jogo_ids}

    for palpite in bolao.palpites:
        if palpite.jogo_id not in palpites_por_jogo:
            continue
        jogo = jogos_por_id[palpite.jogo_id]
        pontos = None
        if jogo.realizado:
            pontos = pontos_jogo(
                palpite.palpite_casa,
                palpite.palpite_fora,
                jogo.gols_casa,
                jogo.gols_fora,
            )
        palpites_por_jogo[palpite.jogo_id].append(
            PalpiteLinha(
                participante=palpite.participante,
                palpite_casa=palpite.palpite_casa,
                palpite_fora=palpite.palpite_fora,
                pontos=pontos,
            )
        )

    blocos: list[PalpitesPorJogo] = []
    for jogo_id in jogo_ids:
        jogo = jogos_por_id.get(jogo_id)
        if jogo is None:
            raise ValueError(f"Jogo {jogo_id} nao encontrado.")
        linhas = _ordenar_linhas(jogo, palpites_por_jogo[jogo_id])
        blocos.append(PalpitesPorJogo(jogo=jogo, linhas=linhas))
    return blocos


def _titulo_jogo(jogo: Jogo) -> str:
    return f"Jogo {jogo.id}: {jogo.casa.strip()} x {jogo.fora.strip()}"


def _resultado_jogo(jogo: Jogo) -> str | None:
    if not jogo.realizado:
        return None
    return f"Resultado: {jogo.gols_casa}x{jogo.gols_fora}"


def formatar_palpites_texto(blocos: list[PalpitesPorJogo]) -> str:
    linhas = ["PALPITES - CLASSIFICADURA BOLAO", ""]
    mostrar_pontos = any(bloco.jogo.realizado for bloco in blocos)

    for indice, bloco in enumerate(blocos):
        if indice > 0:
            linhas.append("")
        linhas.append(_titulo_jogo(bloco.jogo))
        resultado = _resultado_jogo(bloco.jogo)
        if resultado:
            linhas.append(resultado)
        linhas.append("")

        if mostrar_pontos:
            linhas.append(f"{'Participante':<28} {'Palpite':>7}  {'Pts':>3}")
            linhas.append("-" * 42)
            for linha in bloco.linhas:
                pts = "-" if linha.pontos is None else str(linha.pontos)
                linhas.append(
                    f"{linha.participante.strip():<28} {linha.placar_texto:>7}  {pts:>3}"
                )
        else:
            linhas.append(f"{'Participante':<28} {'Palpite':>7}")
            linhas.append("-" * 38)
            for linha in bloco.linhas:
                linhas.append(
                    f"{linha.participante.strip():<28} {linha.placar_texto:>7}"
                )

    return "\n".join(linhas)


def nome_arquivo_palpites(jogo_ids: list[int], extensao: str) -> str:
    ids = "_".join(str(jogo_id) for jogo_id in jogo_ids)
    return f"palpites_j{ids}.{extensao}"
