import tempfile
import unittest
from pathlib import Path

from src.grupos_ranking import (
    calcular_pontos_participante,
    carregar_classificacoes_reais,
    carregar_palpites_grupos,
    gerar_ranking_grupos,
    pontos_por_grupo,
    times_iguais,
)


class TestGruposRanking(unittest.TestCase):
    def test_times_iguais_normaliza_alias(self):
        self.assertTrue(times_iguais("Holanda", "Países Baixos"))
        self.assertTrue(times_iguais("Curaçau", "Curação"))
        self.assertFalse(times_iguais("Brasil", "Argentina"))

    def test_pontos_por_grupo(self):
        real = {1: "México", 2: "África do Sul", 3: "Coreia do Sul", 4: "Tchéquia"}
        palpite = {1: "México", 2: "Tchéquia", 3: "Coreia do Sul", 4: "África do Sul"}
        pontos, acertos = pontos_por_grupo(palpite, real)
        self.assertEqual(pontos, 20)
        self.assertEqual(acertos, 2)

    def test_calcular_pontos_participante_soma_grupos(self):
        reais = {
            "A": {1: "México", 2: "África do Sul", 3: "Coreia do Sul", 4: "Tchéquia"},
            "B": {1: "Suíça", 2: "Canadá", 3: "Bósnia e Herzegovina", 4: "Catar"},
        }
        palpite = {
            "A": {1: "México", 2: "Tchéquia", 3: "Coreia do Sul", 4: "África do Sul"},
            "B": {1: "Suíça", 2: "Canadá", 3: "Catar", 4: "Bósnia e Herzegovina"},
        }
        pontos, acertos, por_grupo = calcular_pontos_participante(palpite, reais)
        self.assertEqual(pontos, 40)
        self.assertEqual(acertos, 4)
        self.assertEqual(por_grupo["A"], 20)
        self.assertEqual(por_grupo["B"], 20)

    def test_carregar_classificacoes_reais(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reais.csv"
            path.write_text(
                "GRUPO A;;;;;;;\n"
                "Posição;Equipe;Pts;V;E;D;GP;GC;SG\n"
                "1;México;9;3;0;0;6;0;6\n"
                "2;África do Sul;4;1;1;1;2;3;-1\n"
                "GRUPO B;;;;;;;\n"
                "Posição;Equipe;Pts;V;E;D;GP;GC;SG\n"
                "1;Suíça;7;2;1;0;7;3;4\n",
                encoding="utf-8",
            )
            reais = carregar_classificacoes_reais(path)
            self.assertEqual(reais["A"][1], "México")
            self.assertEqual(reais["B"][1], "Suíça")

    def test_carregar_palpites_grupos(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "palpites.csv"
            path.write_text(
                "Carimbo,QUAL SEU NOME NA THDFM,GRUPO A [1],GRUPO A [2],GRUPO B [1]\n"
                "x,Ana,México,Tchéquia,Suíça\n",
                encoding="utf-8",
            )
            palpites = carregar_palpites_grupos(path)
            self.assertEqual(palpites["Ana"]["A"][1], "México")
            self.assertEqual(palpites["Ana"]["B"][1], "Suíça")

    def test_gerar_ranking_grupos(self):
        with tempfile.TemporaryDirectory() as tmp:
            reais = Path(tmp) / "reais.csv"
            reais.write_text(
                "GRUPO A;;;;;;;\n"
                "Posição;Equipe;Pts;V;E;D;GP;GC;SG\n"
                "1;México;9;3;0;0;6;0;6\n"
                "2;África do Sul;4;1;1;1;2;3;-1\n"
                "3;Coreia do Sul;3;1;0;2;2;3;-1\n"
                "4;Tchéquia;1;0;1;2;2;6;-4\n",
                encoding="utf-8",
            )
            palpites = Path(tmp) / "palpites.csv"
            palpites.write_text(
                "Carimbo,QUAL SEU NOME NA THDFM,GRUPO A [1],GRUPO A [2],GRUPO A [3],GRUPO A [4]\n"
                "x,Ana,México,África do Sul,Coreia do Sul,Tchéquia\n"
                "x,Bob,México,Tchéquia,Coreia do Sul,África do Sul\n",
                encoding="utf-8",
            )
            ranking, resumo = gerar_ranking_grupos(reais, palpites)
            self.assertEqual(resumo.grupos_definidos, ["A"])
            self.assertEqual(resumo.pontos_maximos, 40)
            self.assertEqual(ranking[0].participante, "Ana")
            self.assertEqual(ranking[0].pontos, 40)
            self.assertEqual(ranking[1].pontos, 20)


if __name__ == "__main__":
    unittest.main()
