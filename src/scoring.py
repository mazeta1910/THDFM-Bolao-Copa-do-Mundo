from __future__ import annotations

from dataclasses import dataclass

from src.models import PontosJogo


@dataclass(frozen=True)
class PesosJogo:
    placar: int
    vencedor: int
    gols: int


FASE_GRUPOS_MAX = 72
DECIMA_SEXTAS_MAX = 88
OITAVAS_MAX = 96
QUARTAS_MAX = 100
SEMIS_MAX = 102
FINAIS_MAX = 104


def pesos_para_jogo(jogo_id: int) -> PesosJogo:
    if jogo_id <= FASE_GRUPOS_MAX:
        return PesosJogo(placar=3, vencedor=2, gols=1)
    if jogo_id <= DECIMA_SEXTAS_MAX:
        return PesosJogo(placar=10, vencedor=7, gols=5)
    if jogo_id <= OITAVAS_MAX:
        return PesosJogo(placar=20, vencedor=15, gols=10)
    if jogo_id <= QUARTAS_MAX:
        return PesosJogo(placar=40, vencedor=25, gols=20)
    if jogo_id <= SEMIS_MAX:
        return PesosJogo(placar=50, vencedor=30, gols=25)
    if jogo_id <= FINAIS_MAX:
        return PesosJogo(placar=100, vencedor=75, gols=50)
    return PesosJogo(placar=3, vencedor=2, gols=1)


def fase_jogo(jogo_id: int) -> str:
    if jogo_id <= FASE_GRUPOS_MAX:
        return "grupos"
    if jogo_id <= DECIMA_SEXTAS_MAX:
        return "16avos"
    if jogo_id <= OITAVAS_MAX:
        return "oitavas"
    if jogo_id <= QUARTAS_MAX:
        return "quartas"
    if jogo_id <= SEMIS_MAX:
        return "semis"
    if jogo_id <= FINAIS_MAX:
        return "finais"
    return "grupos"


def vencedor(gols_casa: int, gols_fora: int) -> str:
    if gols_casa > gols_fora:
        return "casa"
    if gols_casa < gols_fora:
        return "fora"
    return "empate"


def lado_vencedor(
    gols_casa: int,
    gols_fora: int,
    *,
    time_casa: str,
    time_fora: str,
    vencedor_penaltis: str | None = None,
    jogo_id: int = 1,
) -> str | None:
    """Retorna 'casa', 'fora' ou 'empate' (None se empate no mata-mata sem penaltis)."""
    from src.grupos_ranking import times_iguais

    if gols_casa > gols_fora:
        return "casa"
    if gols_casa < gols_fora:
        return "fora"
    if jogo_id <= FASE_GRUPOS_MAX:
        return "empate"
    if vencedor_penaltis:
        if times_iguais(vencedor_penaltis, time_casa):
            return "casa"
        if times_iguais(vencedor_penaltis, time_fora):
            return "fora"
    return None


def classificar_palpite(
    palpite_casa: int,
    palpite_fora: int,
    real_casa: int,
    real_fora: int,
    *,
    jogo_id: int = 1,
    time_casa: str = "",
    time_fora: str = "",
    palpite_penaltis: str | None = None,
    real_penaltis: str | None = None,
) -> tuple[str, bool]:
    """Replica as colunas F (quesito) e G (acertou vencedor) da planilha."""
    if palpite_casa == real_casa and palpite_fora == real_fora:
        acertou_vencedor = True
        if jogo_id > FASE_GRUPOS_MAX and real_casa == real_fora:
            acertou_vencedor = _acertou_vencedor(
                palpite_casa,
                palpite_fora,
                real_casa,
                real_fora,
                jogo_id=jogo_id,
                time_casa=time_casa,
                time_fora=time_fora,
                palpite_penaltis=palpite_penaltis,
                real_penaltis=real_penaltis,
            )
        return "Placar", acertou_vencedor

    acertou_vencedor = _acertou_vencedor(
        palpite_casa,
        palpite_fora,
        real_casa,
        real_fora,
        jogo_id=jogo_id,
        time_casa=time_casa,
        time_fora=time_fora,
        palpite_penaltis=palpite_penaltis,
        real_penaltis=real_penaltis,
    )
    if palpite_casa == real_casa:
        return "Gols Casa", acertou_vencedor
    if palpite_fora == real_fora:
        return "Gols fora", acertou_vencedor
    return "Nada", acertou_vencedor


def _acertou_vencedor(
    palpite_casa: int,
    palpite_fora: int,
    real_casa: int,
    real_fora: int,
    *,
    jogo_id: int,
    time_casa: str,
    time_fora: str,
    palpite_penaltis: str | None,
    real_penaltis: str | None,
) -> bool:
    if jogo_id <= FASE_GRUPOS_MAX:
        return vencedor(palpite_casa, palpite_fora) == vencedor(real_casa, real_fora)

    lado_palpite = lado_vencedor(
        palpite_casa,
        palpite_fora,
        time_casa=time_casa,
        time_fora=time_fora,
        vencedor_penaltis=palpite_penaltis,
        jogo_id=jogo_id,
    )
    lado_real = lado_vencedor(
        real_casa,
        real_fora,
        time_casa=time_casa,
        time_fora=time_fora,
        vencedor_penaltis=real_penaltis,
        jogo_id=jogo_id,
    )
    return lado_palpite is not None and lado_palpite == lado_real


def pontos_jogo(
    palpite_casa: int,
    palpite_fora: int,
    real_casa: int,
    real_fora: int,
    *,
    jogo_id: int = 1,
    time_casa: str = "",
    time_fora: str = "",
    palpite_penaltis: str | None = None,
    real_penaltis: str | None = None,
) -> int:
    return pontos_detalhados(
        palpite_casa,
        palpite_fora,
        real_casa,
        real_fora,
        jogo_id=jogo_id,
        time_casa=time_casa,
        time_fora=time_fora,
        palpite_penaltis=palpite_penaltis,
        real_penaltis=real_penaltis,
    ).total


def pontos_detalhados(
    palpite_casa: int,
    palpite_fora: int,
    real_casa: int,
    real_fora: int,
    *,
    jogo_id: int = 1,
    time_casa: str = "",
    time_fora: str = "",
    palpite_penaltis: str | None = None,
    real_penaltis: str | None = None,
) -> PontosJogo:
    categoria, acertou_vencedor = classificar_palpite(
        palpite_casa,
        palpite_fora,
        real_casa,
        real_fora,
        jogo_id=jogo_id,
        time_casa=time_casa,
        time_fora=time_fora,
        palpite_penaltis=palpite_penaltis,
        real_penaltis=real_penaltis,
    )
    pesos = pesos_para_jogo(jogo_id)

    if categoria == "Placar":
        if acertou_vencedor:
            return PontosJogo(placar=pesos.placar, vencedor=pesos.vencedor)
        return PontosJogo(placar=pesos.placar)

    pts = PontosJogo()
    if acertou_vencedor:
        pts.vencedor = pesos.vencedor
    if categoria == "Gols Casa":
        pts.gols_casa = pesos.gols
    elif categoria == "Gols fora":
        pts.gols_fora = pesos.gols
    return pts
