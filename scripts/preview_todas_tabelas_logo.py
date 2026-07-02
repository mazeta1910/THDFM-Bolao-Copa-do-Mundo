"""Protótipos PNG de todas as tabelas com logo do bolão (issue #5)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.bolao_logo import LOGO_PATH, compor_faixa_logo
from src.cli import (
    _classificacao_jogos,
    _classificacao_premio_a,
    _contar_jogos_fase,
    carregar_bolao,
)
from src.data_paths import DATA_DIR, SNAPSHOT_JSON
from src.image_export import (
    _ALTURA_TITULO_RODADA,
    _MARGEM_RODADA,
    combinar_imagens_horizontal,
    exportar_palpites_png,
    renderizar_classificacao_png,
    renderizar_palpites_provisorios_png,
    renderizar_premio_a_png,
)
from src.models import PontosJogo
from src.palpites_view import listar_palpites_jogos
from src.ranking import (
    FASES_BOLAO,
    calcular_pontos_faixa,
    gerar_classificacao_fase,
    legenda_pesos_fase_linhas,
    legenda_pesos_jogos_linhas,
    sugerir_jogos_provisorios,
)
from src.snapshot import calcular_mudancas_posicao, carregar_snapshot

SAIDA_DIR = DATA_DIR / "ultimo" / "png" / "preview_logo"


def _salvar(nome: str, imagem) -> Path:
    SAIDA_DIR.mkdir(parents=True, exist_ok=True)
    caminho = SAIDA_DIR / nome
    compor_faixa_logo(imagem, LOGO_PATH).save(caminho, format="PNG")
    return caminho


def _variacoes_nulas(classificacao) -> dict[str, int | None]:
    return {linha.participante.strip(): None for linha in classificacao}


def _render_classificacao(
    classificacao,
    bolao,
    *,
    titulo: str = "B - CLASSIFICAÇÃO GERAL",
    mostrar_rod: bool | None = None,
    rotulo_soma: str = "Pts",
    rodape_linhas: list[tuple[str, str]] | None = None,
):
    realizados = sum(1 for j in bolao.jogos if j.realizado)
    variacoes = _variacoes_nulas(classificacao)
    return renderizar_classificacao_png(
        classificacao,
        jogos_realizados=realizados,
        total_jogos=len(bolao.jogos),
        variacoes=variacoes,
        mudancas_posicao=variacoes,
        titulo=titulo,
        rodape_linhas=rodape_linhas,
        mostrar_rod=mostrar_rod,
        rotulo_soma=rotulo_soma,
    )


def main() -> None:
    if not LOGO_PATH.is_file():
        raise SystemExit(f"Logo não encontrado: {LOGO_PATH}")

    bolao = carregar_bolao()
    snap = carregar_snapshot(SNAPSHOT_JSON)
    baseline_ids = set(snap["jogos_ids"]) if snap else set()
    realizados_total = sum(1 for j in bolao.jogos if j.realizado)

    gerados: list[str] = []
    pulados: list[str] = []

    classificacao = _classificacao_jogos(bolao)

    caminho = _salvar(
        "classificacao_preview_logo.png",
        _render_classificacao(classificacao, bolao),
    )
    gerados.append(caminho.name)

    premio_a, cravadura_ativa = _classificacao_premio_a(bolao)
    caminho = _salvar(
        "premio_a_preview_logo.png",
        renderizar_premio_a_png(premio_a, cravadura_ativa=cravadura_ativa),
    )
    gerados.append(caminho.name)

    for fase_id in ("32avos", "grupos_mais_32avos", "grupos"):
        fase = FASES_BOLAO[fase_id]
        realizados_fase, _total_fase = _contar_jogos_fase(bolao, fase_id)
        if realizados_fase == 0 and fase_id != "grupos":
            pulados.append(f"{fase_id} (sem jogos realizados na fase)")
            continue
        classificacao_fase = gerar_classificacao_fase(bolao, fase_id)
        imagem = _render_classificacao(
            classificacao_fase,
            bolao,
            titulo=fase.titulo,
            rodape_linhas=legenda_pesos_fase_linhas(fase_id),
            mostrar_rod=False,
            rotulo_soma="Soma",
        )
        caminho = _salvar(f"fase_{fase_id}_preview_logo.png", imagem)
        gerados.append(caminho.name)

    jogo_ids = sugerir_jogos_provisorios(bolao, baseline_ids, limite=1)
    if jogo_ids:
        blocos = listar_palpites_jogos(bolao, jogo_ids)
        mudancas = calcular_mudancas_posicao(classificacao, None)
        totais_rodada = calcular_pontos_faixa(bolao, set(jogo_ids))
        destaques_rodada = {
            nome: PontosJogo(
                placar=item.placar,
                vencedor=item.vencedor,
                gols_casa=item.gols_casa,
                gols_fora=item.gols_fora,
            )
            for nome, item in totais_rodada.items()
        }
        variacoes_rodada = {nome: item.soma for nome, item in totais_rodada.items()}
        imagem_classificacao = renderizar_classificacao_png(
            classificacao,
            jogos_realizados=realizados_total,
            total_jogos=len(bolao.jogos),
            variacoes=variacoes_rodada,
            mudancas_posicao=mudancas,
            titulo="CLASSIFICAÇÃO GERAL",
            rodape_linhas=legenda_pesos_jogos_linhas(set(jogo_ids)),
            margem_superior=_MARGEM_RODADA,
            fonte_titulo="secao_grande",
            altura_titulo=_ALTURA_TITULO_RODADA,
            rotulo_coluna_extra="TOTAL",
            destaques_rodada=destaques_rodada,
        )
        imagem_provisorio = renderizar_palpites_provisorios_png(
            blocos,
            mesclar_titulo_jogo=True,
            margem_superior=_MARGEM_RODADA,
        )
        combinada = combinar_imagens_horizontal(
            [imagem_classificacao, imagem_provisorio],
            espaco=20,
            alinhar_topo=True,
        )
        caminho = _salvar("rodada_preview_logo.png", combinada)
        gerados.append(f"{caminho.name} (jogo {jogo_ids[0]})")
    else:
        pulados.append("rodada (sem jogos com placar)")

    ultimos_jogos = [j.id for j in bolao.jogos if j.realizado][-2:]
    if ultimos_jogos:
        blocos = listar_palpites_jogos(bolao, ultimos_jogos)
        tmp = SAIDA_DIR / "_tmp_palpites.png"
        exportar_palpites_png(blocos, tmp)
        from PIL import Image

        imagem = Image.open(tmp)
        caminho = _salvar("palpites_preview_logo.png", imagem)
        tmp.unlink(missing_ok=True)
        gerados.append(f"{caminho.name} (jogos {ultimos_jogos})")
    else:
        pulados.append("palpites (sem jogos realizados)")

    if jogo_ids:
        blocos = listar_palpites_jogos(bolao, jogo_ids)
        imagem = renderizar_palpites_provisorios_png(blocos)
        caminho = _salvar("palpites_provisorios_preview_logo.png", imagem)
        gerados.append(f"{caminho.name} (jogo {jogo_ids[0]})")
    else:
        pulados.append("palpites_provisorios (sem jogos com placar)")

    print(f"Protótipos em: {SAIDA_DIR}")
    print("\nGerados:")
    for nome in gerados:
        print(f"  - {nome}")
    if pulados:
        print("\nPulados:")
        for motivo in pulados:
            print(f"  - {motivo}")


if __name__ == "__main__":
    main()
