"""Preview: classificação com logo do bolão (issue #5)."""



from __future__ import annotations



import sys

from pathlib import Path



ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:

    sys.path.insert(0, str(ROOT))



from src.bolao_logo import LOGO_PATH, compor_faixa_logo

from src.cli import carregar_bolao

from src.data_paths import DATA_DIR, SNAPSHOT_JSON

from src.image_export import PAL_FUNDO, renderizar_classificacao_png

from src.ranking import classificacao_ativa, gerar_classificacao

from src.snapshot import carregar_snapshot





def main() -> None:

    if not LOGO_PATH.is_file():

        raise SystemExit(f"Logo não encontrado: {LOGO_PATH}")



    bolao = carregar_bolao()

    snap = carregar_snapshot(SNAPSHOT_JSON)

    baseline = set(snap["jogos_ids"]) if snap else set()

    classificacao = classificacao_ativa(bolao, jogos_ids_baseline=baseline)

    if not classificacao:

        classificacao = gerar_classificacao(bolao)



    variacoes = {linha.participante.strip(): None for linha in classificacao}

    realizados = sum(1 for j in bolao.jogos if j.realizado)



    tabela = renderizar_classificacao_png(

        classificacao,

        jogos_realizados=realizados,

        total_jogos=len(bolao.jogos),

        variacoes=variacoes,

        mudancas_posicao=variacoes,

        titulo="B - CLASSIFICAÇÃO GERAL",

    )

    preview = compor_faixa_logo(tabela, LOGO_PATH)



    saida = DATA_DIR / "ultimo" / "png" / "classificacao_preview_logo.png"

    saida.parent.mkdir(parents=True, exist_ok=True)

    preview.save(saida, format="PNG")

    print(f"Preview salvo em: {saida}")

    print(f"Logo: {LOGO_PATH.name} · fundo {PAL_FUNDO}")





if __name__ == "__main__":

    main()

