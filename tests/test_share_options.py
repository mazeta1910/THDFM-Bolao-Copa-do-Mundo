import unittest

from src.share_options import (
    SelecaoCompartilhar,
    ajustar_selecao_disponivel,
    descrever_exports,
    disponibilidade_compartilhar,
    parse_export_list,
    selecao_geral_parcial_palpites,
)


class TestShareOptions(unittest.TestCase):
    def test_preset_palpites_ativa_rodada(self) -> None:
        selecao = selecao_geral_parcial_palpites()
        self.assertTrue(selecao.rodada_png)
        self.assertFalse(selecao.premio_a_png)

    def test_parse_export_somente_rodada(self) -> None:
        selecao = parse_export_list(["rodada"])
        self.assertTrue(selecao.rodada_png)
        self.assertFalse(selecao.classificacao_png)
        self.assertFalse(selecao.texto)

    def test_ajustar_remove_fase_indisponivel(self) -> None:
        selecao = SelecaoCompartilhar(fase_32avos_png=True)
        disponivel = disponibilidade_compartilhar(
            tem_premio_a=True,
            classificacao_32avos=None,
            classificacao_grupos_32avos=None,
        )
        ajustada = ajustar_selecao_disponivel(selecao, disponivel)
        self.assertFalse(ajustada.fase_32avos_png)

    def test_descrever_exports(self) -> None:
        selecao = SelecaoCompartilhar(classificacao_png=True, rodada_png=True)
        itens = descrever_exports(selecao, jogos_rodada=[73, 74])
        self.assertIn("classificacao.png (premio B)", itens)
        self.assertTrue(any("rodada.png" in item for item in itens))


if __name__ == "__main__":
    unittest.main()
