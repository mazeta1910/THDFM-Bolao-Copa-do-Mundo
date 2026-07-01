import unittest
from pathlib import Path

from scripts.import_32avos import JOGOS_32_AVOS, _carregar_palpites_respostas, validar_colunas_respostas

DATA = Path(__file__).resolve().parent.parent / "data"
RESPOSTAS = DATA / "BOLÃO THDFM WC26 - RESPOSTAS 32 AVOS.csv"


class TestImport32Avos(unittest.TestCase):
    def test_j73_mandante_oficial(self) -> None:
        casa, fora = JOGOS_32_AVOS[73]
        self.assertEqual(casa, "África do Sul")
        self.assertEqual(fora, "Canadá")

    def test_mazeta_j79_equador_2_1(self) -> None:
        if not RESPOSTAS.exists():
            self.skipTest("planilha de respostas ausente")
        palpites = _carregar_palpites_respostas(RESPOSTAS)
        # Formulario: Mexico=1, Equador=2 -> Mexico x Equador no bolao = 1x2
        self.assertEqual(palpites["Mazeta"][79], (1, 2))

    def test_colunas_formulario_fora_de_ordem_alfabetica(self) -> None:
        if not RESPOSTAS.exists():
            self.skipTest("planilha de respostas ausente")
        palpites = _carregar_palpites_respostas(RESPOSTAS)
        # Ramos J79 no form: Mexico=0, Equador=1
        self.assertEqual(palpites["Ramos"][79], (0, 1))

    def test_juan_j73_canada_3_0(self) -> None:
        if not RESPOSTAS.exists():
            self.skipTest("planilha de respostas ausente")
        palpites = _carregar_palpites_respostas(RESPOSTAS)
        # Form: Canada=3, Africa=0 -> bolao casa Africa fora Canada = 0x3
        self.assertEqual(palpites["Juan"][73], (0, 3))

    def test_colunas_respostas_cobrem_todos_jogos(self) -> None:
        if not RESPOSTAS.exists():
            self.skipTest("planilha de respostas ausente")
        erros = validar_colunas_respostas(RESPOSTAS)
        self.assertEqual(erros, [])


if __name__ == "__main__":
    unittest.main()
