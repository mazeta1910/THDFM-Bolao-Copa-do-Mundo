import tempfile
import unittest
from pathlib import Path

from src.models import BolaoData, ClassificacaoLinha, Jogo, Palpite
from src.ranking import (
    aplicar_jogos_novos,
    calcular_variacoes_da_rodada,
    classificacao_ativa,
    gerar_classificacao,
    obter_classificacao,
)


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


class TestObterClassificacao(unittest.TestCase):
    def test_usa_csv_importado_quando_existe(self):
        bolao = BolaoData(
            jogos=[Jogo(id=1, casa="A", fora="B", data="01/01", gols_casa=1, gols_fora=0)],
            participantes=["Ana"],
            palpites=[Palpite(participante="Ana", jogo_id=1, palpite_casa=0, palpite_fora=0)],
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "classificacao.csv"
            path.write_text(
                "CLASSIFICAÇÃO ATUAL - FASE DE GRUPOS (ORDENADA),,,,,,\n"
                ",,Placar,Vencedor,Gols casa,Gols fora,Soma dos pontos\n"
                "1,Ana,9,8,1,2,20\n",
                encoding="utf-8",
            )
            classificacao = obter_classificacao(bolao, importada_path=path)
            self.assertEqual(classificacao[0].soma, 20)
            self.assertNotEqual(gerar_classificacao(bolao)[0].soma, 20)


class TestClassificacaoAtiva(unittest.TestCase):
    def _bolao_minimo(self) -> BolaoData:
        jogos = [
            Jogo(id=1, casa="A", fora="B", data="01/01", gols_casa=1, gols_fora=0),
            Jogo(id=2, casa="C", fora="D", data="02/01", gols_casa=2, gols_fora=2),
        ]
        participantes = ["Ana", "Bob"]
        palpites = [
            Palpite(participante="Ana", jogo_id=1, palpite_casa=1, palpite_fora=0),
            Palpite(participante="Bob", jogo_id=1, palpite_casa=0, palpite_fora=0),
            Palpite(participante="Ana", jogo_id=2, palpite_casa=2, palpite_fora=2),
            Palpite(participante="Bob", jogo_id=2, palpite_casa=1, palpite_fora=1),
        ]
        return BolaoData(jogos=jogos, participantes=participantes, palpites=palpites)

    def test_mantem_importada_sem_jogos_novos(self):
        bolao = self._bolao_minimo()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "classificacao.csv"
            path.write_text(
                "CLASSIFICAÇÃO ATUAL - FASE DE GRUPOS (ORDENADA),,,,,,\n"
                ",,Placar,Vencedor,Gols casa,Gols fora,Soma dos pontos\n"
                "1,Ana,9,8,1,2,20\n"
                "2,Bob,0,0,0,0,0\n",
                encoding="utf-8",
            )
            classificacao = classificacao_ativa(
                bolao,
                importada_path=path,
                jogos_ids_baseline={1, 2},
            )
            self.assertEqual(classificacao[0].soma, 20)

    def test_recalcula_quando_ha_jogo_novo(self):
        bolao = self._bolao_minimo()
        bolao.jogos.append(
            Jogo(id=3, casa="E", fora="F", data="03/01", gols_casa=1, gols_fora=0)
        )
        bolao.palpites.append(
            Palpite(participante="Ana", jogo_id=3, palpite_casa=1, palpite_fora=0)
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "classificacao.csv"
            path.write_text(
                "CLASSIFICAÇÃO ATUAL - FASE DE GRUPOS (ORDENADA),,,,,,\n"
                ",,Placar,Vencedor,Gols casa,Gols fora,Soma dos pontos\n"
                "1,Ana,9,8,1,2,20\n"
                "2,Bob,0,0,0,0,0\n",
                encoding="utf-8",
            )
            classificacao = classificacao_ativa(
                bolao,
                importada_path=path,
                jogos_ids_baseline={1, 2},
            )
            ana = next(linha for linha in classificacao if linha.participante == "Ana")
            self.assertEqual(ana.soma, 25)
            self.assertEqual(ana.soma, 20 + 5)


class TestAplicarJogosNovos(unittest.TestCase):
    def test_soma_apenas_jogos_novos_sobre_base_importada(self):
        bolao = BolaoData(
            jogos=[
                Jogo(id=1, casa="A", fora="B", data="01/01", gols_casa=1, gols_fora=0),
                Jogo(id=2, casa="C", fora="D", data="02/01", gols_casa=0, gols_fora=0),
            ],
            participantes=["Ana", "Bob"],
            palpites=[
                Palpite(participante="Ana", jogo_id=2, palpite_casa=0, palpite_fora=0),
                Palpite(participante="Bob", jogo_id=2, palpite_casa=1, palpite_fora=1),
            ],
        )
        base = [
            ClassificacaoLinha(
                posicao=1,
                participante="Ana",
                placar=9,
                vencedor=8,
                gols_casa=1,
                gols_fora=2,
                soma=20,
            ),
            ClassificacaoLinha(
                posicao=2,
                participante="Bob",
                placar=0,
                vencedor=0,
                gols_casa=0,
                gols_fora=0,
                soma=0,
            ),
        ]
        classificacao = aplicar_jogos_novos(bolao, base, {1})
        ana = next(linha for linha in classificacao if linha.participante == "Ana")
        bob = next(linha for linha in classificacao if linha.participante == "Bob")
        self.assertEqual(ana.soma, 25)
        self.assertEqual(bob.soma, 2)


if __name__ == "__main__":
    unittest.main()
