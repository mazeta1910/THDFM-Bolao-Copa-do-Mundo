from __future__ import annotations

import csv
from pathlib import Path

from src.models import BolaoData, ClassificacaoLinha, PontosParticipante
from src.scoring import pontos_detalhados, pontos_jogo
from src.snapshot import formatar_posicao_com_mudanca, formatar_variacao


def calcular_pontos(bolao: BolaoData) -> dict[str, PontosParticipante]:
    totais = {nome: PontosParticipante(participante=nome) for nome in bolao.participantes}
    jogos_realizados = {jogo.id: jogo for jogo in bolao.jogos if jogo.realizado}

    for palpite in bolao.palpites:
        jogo = jogos_realizados.get(palpite.jogo_id)
        if jogo is None:
            continue
        pontos = pontos_detalhados(
            palpite.palpite_casa,
            palpite.palpite_fora,
            jogo.gols_casa,
            jogo.gols_fora,
        )
        totais[palpite.participante].adicionar(pontos)

    return totais


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
        variacoes[palpite.participante] += pontos_jogo(
            palpite.palpite_casa,
            palpite.palpite_fora,
            jogo.gols_casa,
            jogo.gols_fora,
        )
    return variacoes


def _sort_key(item: PontosParticipante) -> tuple[int, int, int, int, int, str]:
    # Desempate: soma, depois placar, vencedor, gols casa, gols fora (maior vence).
    return (
        -item.soma,
        -item.placar,
        -item.vencedor,
        -item.gols_casa,
        -item.gols_fora,
        item.participante.lower(),
    )


def gerar_classificacao(bolao: BolaoData) -> list[ClassificacaoLinha]:
    totais = calcular_pontos(bolao)
    ordenados = sorted(totais.values(), key=_sort_key)

    classificacao: list[ClassificacaoLinha] = []
    for posicao, item in enumerate(ordenados, start=1):
        classificacao.append(
            ClassificacaoLinha(
                posicao=posicao,
                participante=item.participante,
                placar=item.placar,
                vencedor=item.vencedor,
                gols_casa=item.gols_casa,
                gols_fora=item.gols_fora,
                soma=item.soma,
            )
        )
    return classificacao


def obter_classificacao(
    bolao: BolaoData,
    *,
    importada_path: str | Path | None = None,
) -> list[ClassificacaoLinha]:
    """Carrega a tabela importada do Excel, se existir; senao calcula dos palpites."""
    if importada_path is not None:
        path = Path(importada_path)
        if path.exists():
            return carregar_classificacao_referencia(path)
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
        )
    return totais


def _classificacao_de_totais(totais: dict[str, PontosParticipante]) -> list[ClassificacaoLinha]:
    ordenados = sorted(totais.values(), key=_sort_key)
    return [
        ClassificacaoLinha(
            posicao=posicao,
            participante=item.participante,
            placar=item.placar,
            vencedor=item.vencedor,
            gols_casa=item.gols_casa,
            gols_fora=item.gols_fora,
            soma=item.soma,
        )
        for posicao, item in enumerate(ordenados, start=1)
    ]


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
        totais[chave].adicionar(
            pontos_detalhados(
                palpite.palpite_casa,
                palpite.palpite_fora,
                jogo.gols_casa,
                jogo.gols_fora,
            )
        )

    return _classificacao_de_totais(totais)


def classificacao_ativa(
    bolao: BolaoData,
    *,
    importada_path: str | Path | None = None,
    jogos_ids_baseline: set[int] | None = None,
) -> list[ClassificacaoLinha]:
    """Usa a importacao do Excel na baseline e soma apenas os jogos novos."""
    calculada = gerar_classificacao(bolao)
    jogos_atuais = {jogo.id for jogo in bolao.jogos if jogo.realizado}
    novos = jogos_atuais - jogos_ids_baseline if jogos_ids_baseline is not None else set()

    if novos and jogos_ids_baseline is not None:
        if importada_path is not None:
            path = Path(importada_path)
            if path.exists():
                base = carregar_classificacao_referencia(path)
                return aplicar_jogos_novos(bolao, base, jogos_ids_baseline)
        return calculada

    if importada_path is not None:
        path = Path(importada_path)
        if path.exists():
            return carregar_classificacao_referencia(path)

    return calculada


def exportar_classificacao(classificacao: list[ClassificacaoLinha], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["CLASSIFICAÇÃO ATUAL - FASE DE GRUPOS (ORDENADA)", "", "", "", "", "", ""]
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
                "Placar vale 3, Vencedor vale 2, Gols Casa/Fora vale 1",
                "",
                "",
                "",
                "",
                "",
            ]
        )


def formatar_classificacao_compartilhar(
    classificacao: list[ClassificacaoLinha],
    *,
    jogos_realizados: int,
    total_jogos: int,
    variacoes: dict[str, int | None] | None = None,
    mudancas_posicao: dict[str, int | None] | None = None,
    jogos_novos: list[str] | None = None,
    legenda_rodada: str | None = None,
) -> str:
    linhas = [
        "CLASSIFICADURA BOLAO - COPA DO MUNDO 2026",
        f"Atualizada apos {jogos_realizados} de {total_jogos} jogos",
    ]
    if jogos_novos:
        for texto in jogos_novos[:5]:
            linhas.append(texto)
    linhas.extend(["", f"{'Pos':>6}  {'Participante':<24} {'Pts':>4}  {'Rod':>4}", "-" * 45])
    for item in classificacao:
        chave = item.participante.strip()
        var = None if variacoes is None else variacoes.get(chave)
        delta = None if mudancas_posicao is None else mudancas_posicao.get(chave)
        pos = formatar_posicao_com_mudanca(item.posicao, delta)
        linhas.append(f"{pos:>6}  {chave:<24} {item.soma:>4}  {formatar_variacao(var):>4}")
    linhas.extend(
        [
            "",
            legenda_rodada or "Rod = pontos nos jogos novos desde a ultima rodada confirmada",
            "Placar 3 | Vencedor 2 | Gols casa/fora 1",
            "Desempate: placar -> vencedor -> gols casa -> gols fora",
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
    )
    path.write_text(texto + "\n", encoding="utf-8")


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


def carregar_classificacao_referencia(path: str | Path) -> list[ClassificacaoLinha]:
    path = Path(path)
    linhas: list[ClassificacaoLinha] = []

    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        rows = list(reader)

    for row in rows[2:]:
        if len(row) < 7:
            continue
        posicao = row[0].strip()
        if not posicao.isdigit():
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
