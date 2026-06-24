from __future__ import annotations

from src.models import PontosJogo


def vencedor(gols_casa: int, gols_fora: int) -> str:
    if gols_casa > gols_fora:
        return "casa"
    if gols_casa < gols_fora:
        return "fora"
    return "empate"


def classificar_palpite(
    palpite_casa: int, palpite_fora: int, real_casa: int, real_fora: int
) -> tuple[str, bool]:
    """Replica as colunas F (quesito) e G (acertou vencedor) da planilha."""
    if palpite_casa == real_casa and palpite_fora == real_fora:
        return "Placar", True

    acertou_vencedor = vencedor(palpite_casa, palpite_fora) == vencedor(real_casa, real_fora)
    if palpite_casa == real_casa:
        return "Gols Casa", acertou_vencedor
    if palpite_fora == real_fora:
        return "Gols fora", acertou_vencedor
    return "Nada", acertou_vencedor


def pontos_jogo(palpite_casa: int, palpite_fora: int, real_casa: int, real_fora: int) -> int:
    return pontos_detalhados(palpite_casa, palpite_fora, real_casa, real_fora).total


def pontos_detalhados(
    palpite_casa: int, palpite_fora: int, real_casa: int, real_fora: int
) -> PontosJogo:
    categoria, acertou_vencedor = classificar_palpite(
        palpite_casa, palpite_fora, real_casa, real_fora
    )

    if categoria == "Placar":
        return PontosJogo(placar=3, vencedor=2)

    pts = PontosJogo()
    if acertou_vencedor:
        pts.vencedor = 2
    if categoria == "Gols Casa":
        pts.gols_casa = 1
    elif categoria == "Gols fora":
        pts.gols_fora = 1
    return pts
