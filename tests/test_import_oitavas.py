import unittest
from pathlib import Path

from scripts.import_oitavas import JOGOS_OITAVAS, _carregar_palpites_respostas, validar_colunas_respostas

from src.data_paths import RESPOSTAS_OITAVAS_CSV

RESPOSTAS = RESPOSTAS_OITAVAS_CSV


class TestImportOitavas(unittest.TestCase):
    def test_j89_mandante_oficial(self) -> None:
        casa, fora = JOGOS_OITAVAS[89]
        self.assertEqual(casa, "Paraguai")
        self.assertEqual(fora, "França")

    def test_mazeta_j89_paraguai_0_2(self) -> None:
        if not RESPOSTAS.exists():
            self.skipTest("planilha de respostas ausente")
        palpites = _carregar_palpites_respostas(RESPOSTAS)
        self.assertEqual(palpites["mazeta"][89], (0, 2))

    def test_matheus_honorato_j89_penaltis_franca(self) -> None:
        if not RESPOSTAS.exists():
            self.skipTest("planilha de respostas ausente")
        from src.penaltis import carregar_palpites_penaltis_respostas

        penaltis = carregar_palpites_penaltis_respostas(RESPOSTAS)
        self.assertEqual(penaltis[("matheus honorato", 89)], "França")

    def test_colunas_respostas_cobrem_todos_jogos(self) -> None:
        if not RESPOSTAS.exists():
            self.skipTest("planilha de respostas ausente")
        erros = validar_colunas_respostas(RESPOSTAS)
        self.assertEqual(erros, [])

    def test_jose_carlos_j95_planilha(self) -> None:
        from scripts.import_oitavas import carregar_palpites_planilha_oitavas

        from src.data_paths import PLANILHA_OITAVAS_CSV

        if not PLANILHA_OITAVAS_CSV.exists():
            self.skipTest("planilha das oitavas ausente")
        palpites, _ = carregar_palpites_planilha_oitavas(PLANILHA_OITAVAS_CSV)
        self.assertEqual(palpites[("jose carlos", 95)], (3, 0))


if __name__ == "__main__":
    unittest.main()
