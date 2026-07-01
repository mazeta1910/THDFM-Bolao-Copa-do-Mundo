from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

SecaoClassificacaoReferencia = Literal["grupos", "grupos_32avos"]

JOGOS_BASELINE_REFERENCIA_GERAL = frozenset(range(1, 80))
_MARCADOR_SECAO_GRUPOS_32_AVOS = "GRUPOS + 32 AVOS"

from src.cravadura import pontos_cravadura_por_participante
from src.grupos_ranking import pontos_grupos_por_participante
from src.models import BolaoData, ClassificacaoLinha, ClassificacaoPremioLinha, Jogo, Palpite, PontosJogo, PontosParticipante
from src.scoring import FASE_GRUPOS_MAX, DECIMA_SEXTAS_MAX, pontos_detalhados
from src.share_options import SecoesTextoCompartilhar
from src.snapshot import formatar_posicao_com_mudanca, formatar_variacao


def _chave_participante(participante: str) -> str:
    return participante.strip()


def _carregar_pontos_grupos(
    classificacoes_reais_path: str | Path | None,
    palpites_grupos_path: str | Path | None,
) -> dict[str, int]:
    if classificacoes_reais_path is None or palpites_grupos_path is None:
        return {}
    reais = Path(classificacoes_reais_path)
    palpites = Path(palpites_grupos_path)
    if not reais.exists() or not palpites.exists():
        return {}
    return pontos_grupos_por_participante(reais, palpites)


JOGOS_FASE_GRUPOS = frozenset(range(1, FASE_GRUPOS_MAX + 1))
JOGOS_32_AVOS = frozenset(range(FASE_GRUPOS_MAX + 1, DECIMA_SEXTAS_MAX + 1))
JOGOS_OITAVAS = frozenset(range(DECIMA_SEXTAS_MAX + 1, 96 + 1))
JOGOS_QUARTAS = frozenset(range(97, 100 + 1))
JOGOS_SEMIS = frozenset(range(101, 102 + 1))
JOGOS_FINAIS = frozenset(range(103, 104 + 1))
JOGOS_GRUPOS_MAIS_32_AVOS = JOGOS_FASE_GRUPOS | JOGOS_32_AVOS


@dataclass(frozen=True)
class FaseBolao:
    id: str
    titulo: str
    jogos_ids: frozenset[int]
    jogo_pesos: int


FASES_BOLAO: dict[str, FaseBolao] = {
    "grupos": FaseBolao("grupos", "PONTUACAO PARCIAL - FASE DE GRUPOS", JOGOS_FASE_GRUPOS, 1),
    "32avos": FaseBolao("32avos", "PONTUACAO PARCIAL - 32 AVOS", JOGOS_32_AVOS, 73),
    "oitavas": FaseBolao("oitavas", "PONTUACAO PARCIAL - OITAVAS", JOGOS_OITAVAS, 89),
    "quartas": FaseBolao("quartas", "PONTUACAO PARCIAL - QUARTAS", JOGOS_QUARTAS, 97),
    "semis": FaseBolao("semis", "PONTUACAO PARCIAL - SEMIFINAIS", JOGOS_SEMIS, 101),
    "finais": FaseBolao("finais", "PONTUACAO PARCIAL - FINAIS", JOGOS_FINAIS, 103),
    "grupos_mais_32avos": FaseBolao(
        "grupos_mais_32avos",
        "PONTUACAO PARCIAL - FASE DE GRUPOS + 32 AVOS",
        JOGOS_GRUPOS_MAIS_32_AVOS,
        73,
    ),
}


def gerar_classificacao_fase(bolao: BolaoData, fase_id: str) -> list[ClassificacaoLinha]:
    fase = FASES_BOLAO.get(fase_id)
    if fase is None:
        opcoes = ", ".join(FASES_BOLAO)
        raise ValueError(f"Fase invalida: {fase_id!r}. Opcoes: {opcoes}")
    return gerar_classificacao_jogos_faixa(bolao, set(fase.jogos_ids))


def legenda_pesos_fase(fase_id: str) -> str:
    from src.scoring import pesos_para_jogo

    if fase_id == "grupos_mais_32avos":
        g = pesos_para_jogo(1)
        a = pesos_para_jogo(73)
        return (
            f"Grupos J1-J72: Placar {g.placar} | Vencedor {g.vencedor} | Gols {g.gols} | "
            f"32 avos J73-J88: Placar {a.placar} | Vencedor {a.vencedor} | Gols {a.gols}"
        )
    fase = FASES_BOLAO[fase_id]
    pesos = pesos_para_jogo(fase.jogo_pesos)
    return (
        f"Placar {pesos.placar} | Vencedor {pesos.vencedor} | "
        f"Gols Casa/Fora {pesos.gols}"
    )


def formatar_classificacao_fase_texto(
    classificacao: list[ClassificacaoLinha],
    *,
    fase_id: str,
    jogos_realizados: int,
    total_jogos: int,
) -> str:
    fase = FASES_BOLAO[fase_id]
    linhas = [
        fase.titulo,
        f"Jogos realizados na fase: {jogos_realizados}/{total_jogos}",
        "",
        f"{'Participante':<28} {'Placar':>6} {'Vencedor':>8} {'Gols casa':>9} {'Gols fora':>9} {'Soma':>5}",
        "-" * 78,
    ]
    for item in classificacao:
        linhas.append(
            f"{item.participante:<28} {item.placar:>6} {item.vencedor:>8} "
            f"{item.gols_casa:>9} {item.gols_fora:>9} {item.soma:>5}"
        )
    linhas.extend(["", legenda_pesos_fase(fase_id)])
    return "\n".join(linhas)


def _pontos_palpite_jogo(jogo: Jogo, palpite: Palpite) -> PontosJogo:
    return pontos_detalhados(
        palpite.palpite_casa,
        palpite.palpite_fora,
        jogo.gols_casa,
        jogo.gols_fora,
        jogo_id=jogo.id,
        time_casa=jogo.casa,
        time_fora=jogo.fora,
        palpite_penaltis=palpite.vencedor_penaltis,
        real_penaltis=jogo.vencedor_penaltis,
    )


def calcular_pontos_faixa(
    bolao: BolaoData,
    jogos_ids: set[int],
) -> dict[str, PontosParticipante]:
    totais = {nome: PontosParticipante(participante=nome) for nome in bolao.participantes}
    jogos_realizados = {
        jogo.id: jogo for jogo in bolao.jogos if jogo.realizado and jogo.id in jogos_ids
    }

    for palpite in bolao.palpites:
        if palpite.jogo_id not in jogos_realizados:
            continue
        jogo = jogos_realizados[palpite.jogo_id]
        totais[palpite.participante].adicionar(_pontos_palpite_jogo(jogo, palpite))
    return totais


def calcular_pontos(bolao: BolaoData) -> dict[str, PontosParticipante]:
    jogos_ids = {jogo.id for jogo in bolao.jogos}
    return calcular_pontos_faixa(bolao, jogos_ids)


def calcular_variacoes_da_rodada(
    bolao: BolaoData,
    jogos_ids_baseline: set[int],
) -> dict[str, int]:
    """Pontos ganhos apenas nos jogos realizados apos a ultima rodada confirmada."""
    jogos_da_rodada = {
        jogo.id for jogo in bolao.jogos if jogo.realizado and jogo.id not in jogos_ids_baseline
    }
    return calcular_variacoes_jogos(bolao, jogos_da_rodada)


def calcular_variacoes_jogos(bolao: BolaoData, jogos_ids: set[int]) -> dict[str, int]:
    """Pontos ganhos em um conjunto especifico de jogos realizados."""
    variacoes = {nome: 0 for nome in bolao.participantes}
    if not jogos_ids:
        return variacoes

    jogos_por_id = {jogo.id: jogo for jogo in bolao.jogos}
    for palpite in bolao.palpites:
        if palpite.jogo_id not in jogos_ids:
            continue
        jogo = jogos_por_id.get(palpite.jogo_id)
        if jogo is None or not jogo.realizado:
            continue
        variacoes[palpite.participante] += _pontos_palpite_jogo(jogo, palpite).total
    return variacoes


def _sort_key_jogos(item: PontosParticipante) -> tuple[int, int, int, int, int, str]:
    return (
        -item.soma,
        -item.placar,
        -item.vencedor,
        -item.gols_casa,
        -item.gols_fora,
        item.participante.lower(),
    )


def _sort_key_premio_a(grupos: int, cravadura: int, participante: str) -> tuple[int, int, int, str]:
    return (-(grupos + cravadura), -grupos, -cravadura, participante.lower())


def _classificacao_jogos_de_totais(totais: dict[str, PontosParticipante]) -> list[ClassificacaoLinha]:
    ordenados = sorted(totais.values(), key=_sort_key_jogos)
    return [
        ClassificacaoLinha(
            posicao=posicao,
            participante=item.participante,
            placar=item.placar,
            vencedor=item.vencedor,
            gols_casa=item.gols_casa,
            gols_fora=item.gols_fora,
            soma=item.soma,
            grupos=0,
        )
        for posicao, item in enumerate(ordenados, start=1)
    ]


def gerar_classificacao_jogos(bolao: BolaoData) -> list[ClassificacaoLinha]:
    """Classificacao B: pontos de todos os jogos realizados."""
    return gerar_classificacao_jogos_faixa(bolao, {jogo.id for jogo in bolao.jogos})


def gerar_classificacao_jogos_faixa(
    bolao: BolaoData,
    jogos_ids: set[int],
) -> list[ClassificacaoLinha]:
    totais = calcular_pontos_faixa(bolao, jogos_ids)
    return _classificacao_jogos_de_totais(totais)


def gerar_classificacao_32avos(bolao: BolaoData) -> list[ClassificacaoLinha]:
    return gerar_classificacao_jogos_faixa(bolao, set(JOGOS_32_AVOS))


def gerar_classificacao_grupos_mais_32avos(bolao: BolaoData) -> list[ClassificacaoLinha]:
    return gerar_classificacao_jogos_faixa(bolao, set(JOGOS_GRUPOS_MAIS_32_AVOS))


def gerar_classificacao(
    bolao: BolaoData,
    *,
    classificacoes_reais_path: str | Path | None = None,
    palpites_grupos_path: str | Path | None = None,
) -> list[ClassificacaoLinha]:
    """Alias historico: classificacao dos jogos (premiacao B)."""
    return gerar_classificacao_jogos(bolao)


def gerar_classificacao_premio_a(
    participantes: list[str],
    *,
    classificacoes_reais_path: str | Path | None = None,
    palpites_grupos_path: str | Path | None = None,
    cravadura_path: str | Path | None = None,
) -> tuple[list[ClassificacaoPremioLinha], bool]:
    """Classificacao A: palpitadura dos grupos + cravadura (quando REAL OFICIAL estiver preenchido)."""
    pontos_grupos = _carregar_pontos_grupos(classificacoes_reais_path, palpites_grupos_path)
    pontos_cravadura: dict[str, int] = {}
    cravadura_ativa = False
    if cravadura_path is not None and Path(cravadura_path).exists():
        pontos_cravadura, cravadura_ativa = pontos_cravadura_por_participante(cravadura_path)

    por_chave_grupos = {_chave_participante(nome): pts for nome, pts in pontos_grupos.items()}
    por_chave_crav = {_chave_participante(nome): pts for nome, pts in pontos_cravadura.items()}

    linhas: list[ClassificacaoPremioLinha] = []
    for nome in participantes:
        chave = _chave_participante(nome)
        grupos = por_chave_grupos.get(chave, 0)
        cravadura = por_chave_crav.get(chave, 0)
        linhas.append(
            ClassificacaoPremioLinha(
                posicao=0,
                participante=nome,
                grupos=grupos,
                cravadura=cravadura,
                soma=grupos + cravadura,
            )
        )

    linhas.sort(
        key=lambda item: _sort_key_premio_a(item.grupos, item.cravadura, item.participante)
    )
    for posicao, linha in enumerate(linhas, start=1):
        linha.posicao = posicao
    return linhas, cravadura_ativa


def obter_classificacao(
    bolao: BolaoData,
    *,
    importada_path: str | Path | None = None,
    secao: SecaoClassificacaoReferencia = "grupos",
) -> list[ClassificacaoLinha]:
    """Carrega a tabela importada do Excel, se existir; senao calcula dos palpites."""
    if importada_path is not None:
        path = Path(importada_path)
        if path.exists():
            return carregar_classificacao_referencia(path, secao=secao)
    return gerar_classificacao(bolao)


def _totais_da_base(base: list[ClassificacaoLinha]) -> dict[str, PontosParticipante]:
    totais: dict[str, PontosParticipante] = {}
    for linha in base:
        chave = linha.participante.strip()
        totais[chave] = PontosParticipante(
            participante=linha.participante,
            placar=linha.placar,
            vencedor=linha.vencedor,
            gols_casa=linha.gols_casa,
            gols_fora=linha.gols_fora,
            grupos=linha.grupos,
        )
    return totais


def _classificacao_de_totais(totais: dict[str, PontosParticipante]) -> list[ClassificacaoLinha]:
    return _classificacao_jogos_de_totais(totais)


def aplicar_jogos_novos(
    bolao: BolaoData,
    base: list[ClassificacaoLinha],
    jogos_ids_baseline: set[int],
) -> list[ClassificacaoLinha]:
    """Soma pontos dos jogos novos sobre a classificacao de baseline (ex.: Excel)."""
    jogos_novos = {jogo.id for jogo in bolao.jogos if jogo.realizado} - jogos_ids_baseline
    if not jogos_novos:
        return base

    totais = _totais_da_base(base)
    for nome in bolao.participantes:
        chave = nome.strip()
        if chave not in totais:
            totais[chave] = PontosParticipante(participante=nome)

    jogos_por_id = {jogo.id: jogo for jogo in bolao.jogos}
    for palpite in bolao.palpites:
        if palpite.jogo_id not in jogos_novos:
            continue
        jogo = jogos_por_id[palpite.jogo_id]
        if not jogo.realizado:
            continue
        chave = palpite.participante.strip()
        if chave not in totais:
            totais[chave] = PontosParticipante(participante=palpite.participante)
        totais[chave].adicionar(_pontos_palpite_jogo(jogo, palpite))

    return _classificacao_de_totais(totais)


def classificacao_ativa(
    bolao: BolaoData,
    *,
    importada_path: str | Path | None = None,
    jogos_ids_baseline: set[int] | None = None,
    secao: SecaoClassificacaoReferencia = "grupos",
) -> list[ClassificacaoLinha]:
    """Usa a importacao do Excel na baseline e soma apenas os jogos novos."""
    calculada = gerar_classificacao(bolao)
    jogos_atuais = {jogo.id for jogo in bolao.jogos if jogo.realizado}
    novos = jogos_atuais - jogos_ids_baseline if jogos_ids_baseline is not None else set()

    if novos and jogos_ids_baseline is not None:
        if importada_path is not None:
            path = Path(importada_path)
            if path.exists():
                base = carregar_classificacao_referencia(path, secao=secao)
                return aplicar_jogos_novos(bolao, base, jogos_ids_baseline)
        return calculada

    if importada_path is not None:
        path = Path(importada_path)
        if path.exists():
            return carregar_classificacao_referencia(path, secao=secao)

    return calculada


def referencia_tem_secao_grupos_32avos(path: str | Path) -> bool:
    path = Path(path)
    if not path.exists():
        return False
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.reader(handle):
            if any(_MARCADOR_SECAO_GRUPOS_32_AVOS in cell for cell in row):
                return True
    return False


def resolver_referencia_geral_csv(
    data_dir: str | Path,
    *,
    downloads: Path | None = None,
) -> Path | None:
    """Preferencia: CLASSIFICACAO PROVISORIA (1).csv com secao grupos+32 avos."""
    from src.data_paths import candidatos_referencia_geral

    candidatos = candidatos_referencia_geral(data_dir, downloads=downloads)

    for path in candidatos:
        if path.exists() and referencia_tem_secao_grupos_32avos(path):
            return path
    for path in candidatos:
        if path.exists():
            return path
    return None


def classificacao_geral_ativa(
    bolao: BolaoData,
    *,
    importada_path: str | Path | None = None,
    jogos_ids_baseline: set[int] | None = None,
    data_dir: str | Path | None = None,
) -> list[ClassificacaoLinha]:
    """Tabela geral (grupos + 32 avos): referencia do Excel + jogos novos calculados."""
    path = Path(importada_path) if importada_path else None
    if path is None or not path.exists():
        path = resolver_referencia_geral_csv(data_dir or Path("data"))
    if path is None or not path.exists():
        return gerar_classificacao_jogos(bolao)

    secao: SecaoClassificacaoReferencia = (
        "grupos_32avos" if referencia_tem_secao_grupos_32avos(path) else "grupos"
    )
    baseline = (
        set(jogos_ids_baseline)
        if jogos_ids_baseline is not None
        else set(JOGOS_BASELINE_REFERENCIA_GERAL)
    )
    return classificacao_ativa(
        bolao,
        importada_path=path,
        jogos_ids_baseline=baseline,
        secao=secao,
    )


def exportar_classificacao(classificacao: list[ClassificacaoLinha], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["CLASSIFICACAO B - RESULTADOS DOS JOGOS", "", "", "", "", "", ""]
        )
        writer.writerow(["", "", "Placar", "Vencedor", "Gols casa", "Gols fora", "Soma dos pontos"])
        for linha in classificacao:
            writer.writerow(
                [
                    linha.posicao,
                    linha.participante,
                    linha.placar,
                    linha.vencedor,
                    linha.gols_casa,
                    linha.gols_fora,
                    linha.soma,
                ]
            )
        writer.writerow(["", "", "", "", "", "", ""])
        writer.writerow(
            [
                "",
                "Premiacao B: metade do premio para o lider desta tabela",
                "",
                "",
                "",
                "",
                "",
            ]
        )
        writer.writerow(
            [
                "",
                "Grupos (1-72): Placar 3, Vencedor 2, Gols 1 | 16av: 10/7/5 | Oit: 20/15/10",
                "",
                "",
                "",
                "",
                "",
            ]
        )


def exportar_classificacao_premio_a(
    classificacao: list[ClassificacaoPremioLinha],
    path: str | Path,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["CLASSIFICACAO A - CRAVADURA E GRUPOS", "", "", "", ""])
        writer.writerow(["", "Participante", "Grupos", "Cravadura", "Soma"])
        for linha in classificacao:
            writer.writerow(
                [
                    linha.posicao,
                    linha.participante,
                    linha.grupos,
                    linha.cravadura,
                    linha.soma,
                ]
            )
        writer.writerow(["", "", "", "", ""])
        writer.writerow(
            [
                "",
                "Premiacao A: metade do premio para o lider desta tabela",
                "",
                "",
                "",
            ]
        )
        writer.writerow(
            [
                "",
                "Grupos: 10 pts por time na posicao correta | Cravadura: campeao/vice/3o/4o/artilheiro",
                "",
                "",
                "",
            ]
        )


def formatar_tabela_jogos(
    classificacao: list[ClassificacaoLinha],
    *,
    variacoes: dict[str, int | None] | None = None,
    mudancas_posicao: dict[str, int | None] | None = None,
) -> list[str]:
    linhas = [
        "B) RESULTADOS DOS JOGOS",
        f"{'Pos':>6}  {'Participante':<24} {'Pts':>4}  {'Rod':>4}",
        "-" * 45,
    ]
    for item in classificacao:
        chave = item.participante.strip()
        var = None if variacoes is None else variacoes.get(chave)
        delta = None if mudancas_posicao is None else mudancas_posicao.get(chave)
        pos = formatar_posicao_com_mudanca(item.posicao, delta)
        linhas.append(f"{pos:>6}  {chave:<24} {item.soma:>4}  {formatar_variacao(var):>4}")
    return linhas


def formatar_tabela_jogos_resumida(
    titulo: str,
    classificacao: list[ClassificacaoLinha],
) -> list[str]:
    linhas = [
        "",
        titulo,
        f"{'Pos':>6}  {'Participante':<24} {'Pts':>4}",
        "-" * 38,
    ]
    for item in classificacao:
        chave = item.participante.strip()
        linhas.append(f"{item.posicao:>6}  {chave:<24} {item.soma:>4}")
    return linhas


def formatar_tabela_premio_a(
    classificacao: list[ClassificacaoPremioLinha],
    *,
    cravadura_ativa: bool = False,
) -> list[str]:
    status = "ativa" if cravadura_ativa else "aguardando REAL OFICIAL (19/jul)"
    linhas = [
        "",
        "A) CRAVADURA E CLASSIFICACAO DOS GRUPOS (PALPITADURA)",
        f"Cravadura: {status}",
        f"{'Pos':>6}  {'Participante':<24} {'Grp':>4}  {'Crav':>4}  {'Pts':>4}",
        "-" * 52,
    ]
    for item in classificacao:
        chave = item.participante.strip()
        linhas.append(
            f"{item.posicao:>6}  {chave:<24} {item.grupos:>4}  {item.cravadura:>4}  {item.soma:>4}"
        )
    return linhas


def formatar_classificacao_compartilhar(
    classificacao: list[ClassificacaoLinha],
    *,
    jogos_realizados: int,
    total_jogos: int,
    variacoes: dict[str, int | None] | None = None,
    mudancas_posicao: dict[str, int | None] | None = None,
    jogos_novos: list[str] | None = None,
    legenda_rodada: str | None = None,
    premio_a: list[ClassificacaoPremioLinha] | None = None,
    cravadura_ativa: bool = False,
    classificacao_32avos: list[ClassificacaoLinha] | None = None,
    classificacao_grupos_32avos: list[ClassificacaoLinha] | None = None,
    secoes: SecoesTextoCompartilhar | None = None,
) -> str:
    if secoes is None:
        from src.share_options import SecoesTextoCompartilhar as _Secoes

        secoes = _Secoes()
    linhas = [
        "CLASSIFICADURA BOLAO - COPA DO MUNDO 2026",
        f"Atualizada apos {jogos_realizados} de {total_jogos} jogos",
    ]
    if jogos_novos:
        for texto in jogos_novos[:5]:
            linhas.append(texto)
    if secoes.classificacao_geral:
        linhas.extend(
            formatar_tabela_jogos(
                classificacao,
                variacoes=variacoes,
                mudancas_posicao=mudancas_posicao,
            )
        )
    if secoes.premio_a and premio_a:
        linhas.extend(formatar_tabela_premio_a(premio_a, cravadura_ativa=cravadura_ativa))
    if secoes.fase_32avos and classificacao_32avos is not None:
        linhas.extend(
            formatar_tabela_jogos_resumida(
                "32 AVOS DE FINAL (J73-J88)",
                classificacao_32avos,
            )
        )
    if secoes.fase_grupos_32avos and classificacao_grupos_32avos is not None:
        linhas.extend(
            formatar_tabela_jogos_resumida(
                "FASE DE GRUPOS + 32 AVOS (J1-J88)",
                classificacao_grupos_32avos,
            )
        )
    linhas.extend(
        [
            "",
            legenda_rodada or "Rod = pontos nos jogos novos desde a ultima rodada confirmada",
            "Premiacao: 50% para lider de A, 50% para lider de B; 100% se liderar as duas",
            "A: grupos (10/time) + cravadura quando REAL OFICIAL estiver preenchido",
            "B: todos os jogos realizados (grupos 3/2/1, mata-mata conforme fase)",
            "Desempate jogos: placar -> vencedor -> gols casa -> gols fora",
            "Desempate A: soma -> grupos -> cravadura",
        ]
    )
    return "\n".join(linhas)


def exportar_classificacao_texto(
    classificacao: list[ClassificacaoLinha],
    path: str | Path,
    *,
    jogos_realizados: int,
    total_jogos: int,
    variacoes: dict[str, int | None] | None = None,
    mudancas_posicao: dict[str, int | None] | None = None,
    jogos_novos: list[str] | None = None,
    legenda_rodada: str | None = None,
    premio_a: list[ClassificacaoPremioLinha] | None = None,
    cravadura_ativa: bool = False,
    classificacao_32avos: list[ClassificacaoLinha] | None = None,
    classificacao_grupos_32avos: list[ClassificacaoLinha] | None = None,
    secoes: SecoesTextoCompartilhar | None = None,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    texto = formatar_classificacao_compartilhar(
        classificacao,
        jogos_realizados=jogos_realizados,
        total_jogos=total_jogos,
        variacoes=variacoes,
        mudancas_posicao=mudancas_posicao,
        jogos_novos=jogos_novos,
        legenda_rodada=legenda_rodada,
        premio_a=premio_a,
        cravadura_ativa=cravadura_ativa,
        classificacao_32avos=classificacao_32avos,
        classificacao_grupos_32avos=classificacao_grupos_32avos,
        secoes=secoes,
    )
    path.write_text(texto + "\n", encoding="utf-8")


def sugerir_jogos_provisorios(
    bolao: BolaoData,
    jogos_ids_baseline: set[int],
    *,
    limite: int = 2,
) -> list[int]:
    novos = [
        jogo.id
        for jogo in bolao.jogos
        if jogo.realizado and jogo.id not in jogos_ids_baseline
    ]
    if novos:
        return novos[-limite:]
    com_placar = [jogo.id for jogo in bolao.jogos if jogo.realizado]
    return com_placar[-limite:]


def jogos_recem_realizados(bolao: BolaoData, jogos_ids_anteriores: set[int]) -> list[str]:
    novos = []
    for jogo in bolao.jogos:
        if jogo.realizado and jogo.id not in jogos_ids_anteriores:
            novos.append(
                f"Novo: {jogo.casa} {jogo.gols_casa}x{jogo.gols_fora} {jogo.fora} (jogo {jogo.id})"
            )
    return novos


def resumir_jogos_export(bolao: BolaoData, jogo_ids: list[int]) -> list[str]:
    jogos_por_id = {jogo.id: jogo for jogo in bolao.jogos}
    linhas: list[str] = []
    for jogo_id in jogo_ids:
        jogo = jogos_por_id.get(jogo_id)
        if jogo is None or not jogo.realizado:
            continue
        linhas.append(
            f"Novo: {jogo.casa} {jogo.gols_casa}x{jogo.gols_fora} {jogo.fora} (jogo {jogo.id})"
        )
    return linhas


def _indice_cabecalho_secao(
    rows: list[list[str]],
    secao: SecaoClassificacaoReferencia,
) -> int:
    if secao == "grupos_32avos":
        for indice, row in enumerate(rows):
            if any(_MARCADOR_SECAO_GRUPOS_32_AVOS in cell for cell in row):
                if indice + 1 < len(rows):
                    return indice + 1
                break
        raise ValueError(f"Secao grupos+32 avos nao encontrada em {secao!r}")

    if len(rows) < 2:
        raise ValueError("CSV de referencia vazio ou invalido")
    return 1


def _parse_linhas_classificacao(
    rows: list[list[str]],
    cabecalho_idx: int,
) -> list[ClassificacaoLinha]:
    linhas: list[ClassificacaoLinha] = []
    for row in rows[cabecalho_idx + 1 :]:
        if len(row) < 7:
            continue
        posicao = row[0].strip()
        if not posicao.isdigit():
            if linhas:
                break
            continue
        linhas.append(
            ClassificacaoLinha(
                posicao=int(posicao),
                participante=row[1],
                placar=int(row[2]),
                vencedor=int(row[3]),
                gols_casa=int(row[4]),
                gols_fora=int(row[5]),
                soma=int(row[6]),
            )
        )
    return linhas


def carregar_classificacao_referencia(
    path: str | Path,
    *,
    secao: SecaoClassificacaoReferencia = "grupos",
) -> list[ClassificacaoLinha]:
    path = Path(path)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    cabecalho_idx = _indice_cabecalho_secao(rows, secao)
    return _parse_linhas_classificacao(rows, cabecalho_idx)


def comparar_classificacoes(
    calculada: list[ClassificacaoLinha], referencia: list[ClassificacaoLinha]
) -> list[str]:
    diferencas: list[str] = []

    if len(calculada) != len(referencia):
        diferencas.append(
            f"Quantidade de participantes difere: calculada={len(calculada)}, referencia={len(referencia)}"
        )

    ref_por_nome = {linha.participante.strip(): linha for linha in referencia}
    for linha in calculada:
        ref = ref_por_nome.get(linha.participante.strip())
        if ref is None:
            ref = ref_por_nome.get(linha.participante)
        if ref is None:
            diferencas.append(f"Participante ausente na referência: {linha.participante}")
            continue

        campos = ("placar", "vencedor", "gols_casa", "gols_fora", "soma")
        for campo in campos:
            calc_val = getattr(linha, campo)
            ref_val = getattr(ref, campo)
            if calc_val != ref_val:
                diferencas.append(
                    f"{linha.participante}: {campo} calculado={calc_val}, referencia={ref_val}"
                )

        if linha.posicao != ref.posicao:
            diferencas.append(
                f"{linha.participante}: posicao calculada={linha.posicao}, referencia={ref.posicao}"
            )

    return diferencas
