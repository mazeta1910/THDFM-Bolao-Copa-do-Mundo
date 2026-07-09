import unittest

from scripts.import_quartas import JOGOS_QUARTAS, carregar_palpites_planilha_quartas

from src.data_paths import PLANILHA_QUARTAS_CSV


class TestImportQuartas(unittest.TestCase):
    def test_j97_mandante_oficial(self) -> None:
        casa, fora = JOGOS_QUARTAS[97]
        self.assertEqual(casa, "França")
        self.assertEqual(fora, "Marrocos")

    def test_j100_confronto(self) -> None:
        casa, fora = JOGOS_QUARTAS[100]
        self.assertEqual(casa, "Argentina")
        self.assertEqual(fora, "Suíça")

    def test_marlon_j100_10_mais_zero(self) -> None:
        if not PLANILHA_QUARTAS_CSV.exists():
            self.skipTest("planilha das quartas ausente")
        palpites, _ = carregar_palpites_planilha_quartas(PLANILHA_QUARTAS_CSV)
        self.assertEqual(palpites[("marlon wietzikoski", 100)], (10, 0))

    def test_xonha_j97_2_0(self) -> None:
        if not PLANILHA_QUARTAS_CSV.exists():
            self.skipTest("planilha das quartas ausente")
        palpites, _ = carregar_palpites_planilha_quartas(PLANILHA_QUARTAS_CSV)
        self.assertEqual(palpites[("xonha", 97)], (2, 0))

    def test_emboava_j100_penaltis(self) -> None:
        if not PLANILHA_QUARTAS_CSV.exists():
            self.skipTest("planilha das quartas ausente")
        _, penaltis = carregar_palpites_planilha_quartas(PLANILHA_QUARTAS_CSV)
        self.assertEqual(penaltis[("emboava", 100)], "Suíça")


if __name__ == "__main__":
    unittest.main()
