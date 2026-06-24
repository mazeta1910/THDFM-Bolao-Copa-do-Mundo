from __future__ import annotations

from dataclasses import dataclass

from src.models import BolaoData, Jogo
from src.scoring import classificar_palpite, pontos_jogo, vencedor


@dataclass
class PalpiteLinha:
    participante: str
    palpite_casa: int
    palpite_fora: int
    pontos: int | None = None
    categoria: str | None = None
    acertou_vencedor: bool | None = None

    @property
    def placar_texto(self) -> str:
        return f"{self.palpite_casa}x{self.palpite_fora}"

    @property
    def texto_vencedor(self) -> str | None:
        if self.acertou_vencedor is None:
            return None
        return "Acertou" if self.acertou_vencedor else "Errou"


@dataclass
class PalpitesPorJogo:
    jogo: Jogo
    linhas: list[PalpiteLinha]


def _preencher_linha_palpite(jogo: Jogo, palpite) -> PalpiteLinha:
    pontos = None
    categoria = None
    acertou_vencedor = None
    if jogo.realizado:
        categoria, acertou_vencedor = classificar_palpite(
            palpite.palpite_casa,
            palpite.palpite_fora,
            jogo.gols_casa,
            jogo.gols_fora,
        )
        pontos = pontos_jogo(
            palpite.palpite_casa,
            palpite.palpite_fora,
            jogo.gols_casa,
            jogo.gols_fora,
        )
    return PalpiteLinha(
        participante=palpite.participante,
        palpite_casa=palpite.palpite_casa,
        palpite_fora=palpite.palpite_fora,
        pontos=pontos,
        categoria=categoria,
        acertou_vencedor=acertou_vencedor,
    )


def rotulo_vencedor_jogo(jogo: Jogo) -> str:
    if not jogo.realizado:
        return "-"
    resultado = vencedor(jogo.gols_casa, jogo.gols_fora)
    if resultado == "empate":
        return "Empate"
    if resultado == "casa":
        return jogo.casa.strip()
    return jogo.fora.strip()


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
        palpites_por_jogo[palpite.jogo_id].append(_preencher_linha_palpite(jogo, palpite))

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


def nome_arquivo_palpites(jogo_ids: list[int], extensao: str, *, provisorio: bool = False) -> str:
    ids = "_".join(str(jogo_id) for jogo_id in jogo_ids)
    prefixo = "palpites_provisorios" if provisorio else "palpites"
    return f"{prefixo}_j{ids}.{extensao}"


def formatar_palpites_provisorio_texto(blocos: list[PalpitesPorJogo]) -> str:
    realizados = [bloco for bloco in blocos if bloco.jogo.realizado]
    if not realizados:
        return "PALPITES PROVISORIOS - CLASSIFICADURA BOLAO\n\nNenhum jogo com placar provisorio."

    participantes = sorted(
        {linha.participante.strip() for bloco in realizados for linha in bloco.linhas},
        key=str.lower,
    )
    mapas = [{linha.participante.strip(): linha for linha in bloco.linhas} for bloco in realizados]

    linhas = ["PALPITES PROVISORIOS - CLASSIFICADURA BOLAO", ""]
    for bloco in realizados:
        jogo = bloco.jogo
        linhas.append(
            f"Jogo {jogo.id}: {jogo.casa.strip()} x {jogo.fora.strip()}  "
            f"-> {jogo.gols_casa}x{jogo.gols_fora}  "
            f"({rotulo_vencedor_jogo(jogo)})"
        )

    cabecalho_jogos = "".join(f"  {'Pal':>5} {'Quesito':<10} {'Venc':<7}" for _ in realizados)
    linhas.extend(["", f"{'Participante':<28}{cabecalho_jogos}  {'Pts':>3}", "-" * 72])

    for nome in participantes:
        texto = f"{nome:<28}"
        total = 0
        for mapa in mapas:
            linha = mapa[nome]
            total += linha.pontos or 0
            texto += (
                f"  {linha.placar_texto:>5} "
                f"{(linha.categoria or '-'):<10} {(linha.texto_vencedor or '-'):<7}"
            )
        texto += f"  {total:>3}"
        linhas.append(texto)

    return "\n".join(linhas)
