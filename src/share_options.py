"""Presets e seleção de exports do compartilhar."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class SelecaoCompartilhar:
    """Quais tabelas/arquivos gerar ao compartilhar."""

    texto: bool = True
    classificacao_png: bool = True
    premio_a_png: bool = True
    fase_32avos_png: bool = True
    fase_grupos_32avos_png: bool = True
    rodada_png: bool = False

    def algum_export(self) -> bool:
        return any(
            (
                self.texto,
                self.classificacao_png,
                self.premio_a_png,
                self.fase_32avos_png,
                self.fase_grupos_32avos_png,
                self.rodada_png,
            )
        )

    def secoes_texto(self) -> SecoesTextoCompartilhar:
        return SecoesTextoCompartilhar(
            classificacao_geral=self.classificacao_png or self.texto,
            premio_a=self.premio_a_png or self.texto,
            fase_32avos=self.fase_32avos_png or self.texto,
            fase_grupos_32avos=self.fase_grupos_32avos_png or self.texto,
        )


@dataclass(frozen=True)
class SecoesTextoCompartilhar:
    """Seções incluídas no texto do terminal e do .txt."""

    classificacao_geral: bool = True
    premio_a: bool = True
    fase_32avos: bool = True
    fase_grupos_32avos: bool = True


@dataclass(frozen=True)
class DisponibilidadeCompartilhar:
    tem_premio_a: bool = True
    tem_fase_32avos: bool = False
    tem_fase_grupos_32avos: bool = False


def disponibilidade_compartilhar(
    *,
    tem_premio_a: bool,
    classificacao_32avos,
    classificacao_grupos_32avos,
) -> DisponibilidadeCompartilhar:
    return DisponibilidadeCompartilhar(
        tem_premio_a=tem_premio_a,
        tem_fase_32avos=classificacao_32avos is not None,
        tem_fase_grupos_32avos=classificacao_grupos_32avos is not None,
    )


def selecao_rodada_whatsapp() -> SelecaoCompartilhar:
    """Pacote tipico da rodada: ranking + imagem combinada, sem tabelas extras."""
    return SelecaoCompartilhar(
        premio_a_png=False,
        fase_32avos_png=False,
        fase_grupos_32avos_png=False,
        rodada_png=True,
    )


def selecao_completa(*, incluir_rodada: bool = False) -> SelecaoCompartilhar:
    return SelecaoCompartilhar(rodada_png=incluir_rodada)


def selecao_geral_parcial_palpites() -> SelecaoCompartilhar:
    return SelecaoCompartilhar(
        premio_a_png=False,
        rodada_png=True,
    )


def selecao_geral_parcial() -> SelecaoCompartilhar:
    return SelecaoCompartilhar(premio_a_png=False)


def selecao_geral_premio_a() -> SelecaoCompartilhar:
    return SelecaoCompartilhar(
        fase_32avos_png=False,
        fase_grupos_32avos_png=False,
    )


def selecao_so_geral() -> SelecaoCompartilhar:
    return SelecaoCompartilhar(
        premio_a_png=False,
        fase_32avos_png=False,
        fase_grupos_32avos_png=False,
    )


def selecao_so_parcial() -> SelecaoCompartilhar:
    return SelecaoCompartilhar(
        texto=False,
        classificacao_png=False,
        premio_a_png=False,
    )


def ajustar_selecao_disponivel(
    selecao: SelecaoCompartilhar,
    disponivel: DisponibilidadeCompartilhar,
) -> SelecaoCompartilhar:
    return replace(
        selecao,
        premio_a_png=selecao.premio_a_png and disponivel.tem_premio_a,
        fase_32avos_png=selecao.fase_32avos_png and disponivel.tem_fase_32avos,
        fase_grupos_32avos_png=(
            selecao.fase_grupos_32avos_png and disponivel.tem_fase_grupos_32avos
        ),
    )


def parse_export_list(valores: list[str]) -> SelecaoCompartilhar:
    """CLI: --export geral,premio_a,fase_32avos,rodada,txt,..."""
    chaves = {item.strip().lower() for item in valores}
    if not chaves or "tudo" in chaves or "completo" in chaves or "all" in chaves:
        return selecao_completa(incluir_rodada="rodada" in chaves)

    return SelecaoCompartilhar(
        texto="txt" in chaves or "texto" in chaves or not chaves.isdisjoint(
            {"geral", "premio_a", "fase_32avos", "fase_grupos_32avos"}
        ),
        classificacao_png="geral" in chaves or "classificacao" in chaves or "b" in chaves,
        premio_a_png="premio_a" in chaves or "a" in chaves,
        fase_32avos_png="fase_32avos" in chaves or "32avos" in chaves or "parcial" in chaves,
        fase_grupos_32avos_png=(
            "fase_grupos_32avos" in chaves
            or "grupos_32avos" in chaves
            or "grupos+32avos" in chaves
        ),
        rodada_png="rodada" in chaves or "palpites" in chaves,
    )


def descrever_exports(
    selecao: SelecaoCompartilhar,
    *,
    jogos_rodada: list[int] | None = None,
    disponivel: DisponibilidadeCompartilhar | None = None,
    legivel: bool = False,
) -> list[str]:
    selecao = ajustar_selecao_disponivel(selecao, disponivel) if disponivel else selecao
    itens: list[str] = []
    if selecao.texto:
        itens.append(
            "classificacao.txt — texto para WhatsApp"
            if legivel
            else "classificacao.txt"
        )
    if selecao.classificacao_png:
        itens.append(
            "classificacao.png — ranking geral"
            if legivel
            else "classificacao.png (premio B)"
        )
    if selecao.premio_a_png:
        itens.append(
            "premio_a.png — tabela dos grupos + cravadura"
            if legivel
            else "premio_a.png"
        )
    if selecao.fase_32avos_png:
        itens.append(
            "fase_32avos.png — pontos nos 32 avos"
            if legivel
            else "fase_32avos.png"
        )
    if selecao.fase_grupos_32avos_png:
        itens.append(
            "fase_grupos_mais_32avos.png — ranking grupos + 32 avos"
            if legivel
            else "fase_grupos_mais_32avos.png"
        )
    if selecao.rodada_png:
        if jogos_rodada:
            ids = ", ".join(str(jogo_id) for jogo_id in jogos_rodada)
            itens.append(
                f"rodada.png — ranking AO LADO dos palpites provisorios (J{ids})"
                if legivel
                else f"rodada.png (palpites J{ids})"
            )
        else:
            itens.append(
                "rodada.png — ranking + palpites lado a lado (informe o jogo)"
                if legivel
                else "rodada.png (palpites — informe jogos)"
            )
    return itens


BREADCRUMB_RODADA_PNG = "Menu > Rodada de hoje > Ranking + palpites"


def caminho_menu_export(nome_arquivo: str) -> str:
    """Breadcrumb textual de como gerar cada arquivo pelo menu."""
    mapa = {
        "classificacao.png": "Menu > Compartilhar > So ranking",
        "classificacao.txt": "Menu > Compartilhar > So ranking",
        "rodada.png": "Menu > Rodada de hoje > Ranking + palpites  OU  Compartilhar > Rodada ao vivo",
        "palpites.png": "Menu > Palpites > Exportar placares simples",
        "palpites_provisorios.png": "Menu > Palpites > Exportar com quesito e vencedor",
        "premio_a.png": "Menu > Compartilhar > Tudo  OU  Tabelas",
        "fase_32avos.png": "Menu > Tabelas > Pontuacao por fase > 32 avos",
        "fase_grupos_mais_32avos.png": "Menu > Compartilhar > Tudo",
    }
    return mapa.get(nome_arquivo.split()[0], "Menu > Compartilhar")
