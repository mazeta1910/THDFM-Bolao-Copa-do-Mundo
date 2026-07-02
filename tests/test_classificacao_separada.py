import tempfile
import unittest
from pathlib import Path

from src.cravadura import carregar_cravadura_planilha, pontos_cravadura_por_participante
from src.models import BolaoData, Jogo, Palpite
from src.ranking import (
    FASES_BOLAO,
    gerar_classificacao_fase,
    gerar_classificacao_jogos,
    gerar_classificacao_premio_a,
    gerar_classificacao_32avos,
    legenda_pesos_fase,
)


class TestCravaduraPlanilha(unittest.TestCase):
    def test_cravadura_inativa_quando_real_oficial_vazio(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "crav.csv"
            path.write_text(
                ",CAMPEÃO (250),Vice-campeão (200),3º lugar (150),4º lugar (120),Artilheiro (300),,TOTAL\n"
                "REAL OFICIAL,-,-,-,-,-,,\n"
                "Ana,Brasil,França,Espanha,Argentina,Mbappé,,0\n",
                encoding="utf-8",
            )
            planilha = carregar_cravadura_planilha(path)
            self.assertFalse(planilha.ativa)
            pontos, ativa = pontos_cravadura_por_participante(path)
            self.assertFalse(ativa)
            self.assertEqual(pontos["Ana"], 0)

    def test_cravadura_ativa_quando_real_oficial_preenchido(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "crav.csv"
            path.write_text(
                ",CAMPEÃO (250),Vice-campeão (200),3º lugar (150),4º lugar (120),Artilheiro (300),,TOTAL\n"
                "REAL OFICIAL,Brasil,França,Espanha,Argentina,Mbappé,,\n"
                "Ana,Brasil,França,Espanha,Argentina,Mbappé,,0\n"
                "Bob,Alemanha,Holanda,Portugal,Italia,Ronaldo,,0\n",
                encoding="utf-8",
            )
            pontos, ativa = pontos_cravadura_por_participante(path)
            self.assertTrue(ativa)
            self.assertEqual(pontos["Ana"], 250 + 200 + 150 + 120 + 300)
            self.assertEqual(pontos["Bob"], 0)


class TestClassificacaoSeparada(unittest.TestCase):
    def test_premio_a_separado_dos_jogos(self):
        bolao = BolaoData(
            jogos=[Jogo(id=1, casa="A", fora="B", data="01/01", gols_casa=1, gols_fora=0)],
            participantes=["Ana"],
            palpites=[Palpite(participante="Ana", jogo_id=1, palpite_casa=1, palpite_fora=0)],
        )
        with tempfile.TemporaryDirectory() as tmp:
            reais = Path(tmp) / "reais.csv"
            reais.write_text(
                "GRUPO A;;;;;;;\n"
                "Posição;Equipe;Pts;V;E;D;GP;GC;SG\n"
                "1;México;9;3;0;0;6;0;6\n"
                "2;Tchéquia;4;1;1;1;2;3;-1\n"
                "3;Coreia do Sul;3;1;0;2;2;3;-1\n"
                "4;África do Sul;1;0;1;2;2;6;-4\n",
                encoding="utf-8",
            )
            palpites = Path(tmp) / "palpites.csv"
            palpites.write_text(
                "QUAL SEU NOME NA THDFM,GRUPO A [1],GRUPO A [2],GRUPO A [3],GRUPO A [4]\n"
                "Ana,México,Tchéquia,Coreia do Sul,África do Sul\n",
                encoding="utf-8",
            )
            crav = Path(tmp) / "crav.csv"
            crav.write_text(
                ",CAMPEÃO (250),Vice-campeão (200),3º lugar (150),4º lugar (120),Artilheiro (300),,TOTAL\n"
                "REAL OFICIAL,-,-,-,-,-,,\n"
                "Ana,Brasil,França,Espanha,Argentina,Mbappé,,0\n",
                encoding="utf-8",
            )
            jogos = gerar_classificacao_jogos(bolao)
            premio_a, ativa = gerar_classificacao_premio_a(
                bolao.participantes,
                classificacoes_reais_path=reais,
                palpites_grupos_path=palpites,
                cravadura_path=crav,
            )
            self.assertEqual(jogos[0].soma, 5)
            self.assertEqual(premio_a[0].grupos, 40)
            self.assertEqual(premio_a[0].cravadura, 0)
            self.assertEqual(premio_a[0].soma, 40)
            self.assertFalse(ativa)

    def test_32avos_somente_jogos_73_88(self):
        bolao = BolaoData(
            jogos=[
                Jogo(id=1, casa="A", fora="B", data="01/01", gols_casa=1, gols_fora=0),
                Jogo(id=73, casa="C", fora="D", data="02/01", gols_casa=2, gols_fora=1),
            ],
            participantes=["Ana"],
            palpites=[
                Palpite(participante="Ana", jogo_id=1, palpite_casa=1, palpite_fora=0),
                Palpite(participante="Ana", jogo_id=73, palpite_casa=2, palpite_fora=1),
            ],
        )
        avos = gerar_classificacao_32avos(bolao)
        self.assertEqual(avos[0].soma, 17)
        self.assertEqual(avos[0].placar, 10)
        self.assertEqual(avos[0].vencedor, 7)

    def test_classificacao_fase_detalhada(self):
        bolao = BolaoData(
            jogos=[
                Jogo(id=73, casa="C", fora="D", data="02/01", gols_casa=0, gols_fora=0),
            ],
            participantes=["Ana", "Bob"],
            palpites=[
                Palpite(participante="Ana", jogo_id=73, palpite_casa=0, palpite_fora=0),
                Palpite(participante="Bob", jogo_id=73, palpite_casa=1, palpite_fora=0),
            ],
        )
        fase = gerar_classificacao_fase(bolao, "32avos")
        ana = next(l for l in fase if l.participante == "Ana")
        bob = next(l for l in fase if l.participante == "Bob")
        self.assertEqual(ana.soma, 10)
        self.assertEqual(bob.gols_fora, 5)
        self.assertEqual(
            legenda_pesos_fase("32avos"),
            "PONTUAÇÕES 32 AVOS (J73-J88): Placar: 10 | Vencedor: 7 | Gols: 5",
        )
        self.assertIn("32avos", FASES_BOLAO)


if __name__ == "__main__":
    unittest.main()
