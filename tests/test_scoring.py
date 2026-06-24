import unittest

from src.scoring import pontos_detalhados, pontos_jogo


class TestScoring(unittest.TestCase):
    def test_placar_exato(self):
        self.assertEqual(pontos_jogo(2, 1, 2, 1), 5)
        det = pontos_detalhados(2, 1, 2, 1)
        self.assertEqual(det.placar, 3)
        self.assertEqual(det.vencedor, 2)
        self.assertEqual(det.gols_casa, 0)
        self.assertEqual(det.gols_fora, 0)

    def test_apenas_vencedor(self):
        self.assertEqual(pontos_jogo(2, 1, 3, 2), 2)

    def test_vencedor_e_gol_casa(self):
        self.assertEqual(pontos_jogo(2, 1, 2, 0), 3)
        det = pontos_detalhados(2, 1, 2, 0)
        self.assertEqual(det.vencedor, 2)
        self.assertEqual(det.gols_casa, 1)

    def test_apenas_gol_fora(self):
        self.assertEqual(pontos_jogo(2, 1, 1, 1), 1)

    def test_empate_com_gols(self):
        self.assertEqual(pontos_jogo(1, 1, 2, 2), 2)
        det = pontos_detalhados(1, 1, 2, 2)
        self.assertEqual(det.vencedor, 2)
        self.assertEqual(det.gols_casa, 0)
        self.assertEqual(det.gols_fora, 0)

    def test_gol_fora_sem_vencedor(self):
        self.assertEqual(pontos_jogo(0, 0, 1, 0), 1)
        det = pontos_detalhados(0, 0, 1, 0)
        self.assertEqual(det.gols_fora, 1)
        self.assertEqual(det.vencedor, 0)

    def test_nada_certo(self):
        self.assertEqual(pontos_jogo(4, 0, 2, 2), 0)


if __name__ == "__main__":
    unittest.main()
