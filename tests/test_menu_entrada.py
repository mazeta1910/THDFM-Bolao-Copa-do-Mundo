import unittest
from unittest.mock import patch

from src.menu import _confirmar, _ler_opcao_numerica


class TestMenuEntrada(unittest.TestCase):
    @patch("src.menu._ler_linha", return_value="s")
    def test_confirmar_s_e_sim(self, _mock: unittest.mock.MagicMock) -> None:
        self.assertTrue(_confirmar("Gerar?", padrao=True))

    @patch("src.menu._ler_linha", return_value="n")
    def test_confirmar_n_e_nao(self, _mock: unittest.mock.MagicMock) -> None:
        self.assertFalse(_confirmar("Gerar?", padrao=True))

    @patch("src.menu._ler_linha", return_value="")
    def test_opcao_numerica_enter_usa_padrao(self, _mock: unittest.mock.MagicMock) -> None:
        self.assertEqual(_ler_opcao_numerica("Escolha: ", padrao="2"), "2")


if __name__ == "__main__":
    unittest.main()
