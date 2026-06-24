import unittest

from src.models import BolaoData, Jogo, Palpite
from src.ranking import calcular_variacoes_da_rodada


class TestVariacoesDaRodada(unittest.TestCase):
    def _bolao_minimo(self) -> BolaoData:
        jogos = [
            Jogo(id=1, casa="A", fora="B", data="01/01", gols_casa=1, gols_fora=0),
            Jogo(id=2, casa="C", fora="D", data="02/01", gols_casa=2, gols_fora=2),
            Jogo(id=3, casa="E", fora="F", data="03/01", gols_casa=None, gols_fora=None),
        ]
        participantes = ["Ana", "Bob"]
        palpites = [
            Palpite(participante="Ana", jogo_id=1, palpite_casa=1, palpite_fora=0),
            Palpite(participante="Bob", jogo_id=1, palpite_casa=0, palpite_fora=0),
            Palpite(participante="Ana", jogo_id=2, palpite_casa=2, palpite_fora=2),
            Palpite(participante="Bob", jogo_id=2, palpite_casa=1, palpite_fora=1),
            Palpite(participante="Ana", jogo_id=3, palpite_casa=1, palpite_fora=0),
            Palpite(participante="Bob", jogo_id=3, palpite_casa=0, palpite_fora=1),
        ]
        return BolaoData(jogos=jogos, participantes=participantes, palpites=palpites)

    def test_somente_jogos_novos_contam(self):
        bolao = self._bolao_minimo()
        variacoes = calcular_variacoes_da_rodada(bolao, {1})
        self.assertEqual(variacoes["Ana"], 5)
        self.assertEqual(variacoes["Bob"], 2)

    def test_sem_jogos_novos_retorna_zero(self):
        bolao = self._bolao_minimo()
        variacoes = calcular_variacoes_da_rodada(bolao, {1, 2})
        self.assertEqual(variacoes["Ana"], 0)
        self.assertEqual(variacoes["Bob"], 0)

    def test_corrigir_placar_nao_gera_negativo(self):
        bolao = self._bolao_minimo()
        baseline = {1}
        calcular_variacoes_da_rodada(bolao, baseline)
        bolao.jogos[1].gols_casa = 0
        bolao.jogos[1].gols_fora = 0
        variacoes_corrigido = calcular_variacoes_da_rodada(bolao, baseline)
        self.assertTrue(all(valor >= 0 for valor in variacoes_corrigido.values()))


if __name__ == "__main__":
    unittest.main()
