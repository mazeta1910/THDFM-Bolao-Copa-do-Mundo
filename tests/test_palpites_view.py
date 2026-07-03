import unittest
from pathlib import Path

from src.loader import aplicar_resultados_externos
from src.models import BolaoData, Jogo, Palpite
from src.palpites_view import (
    EMPATE_GRUPO,
    EMPATE_SEM_PEN,
    PalpiteLinha,
    _jogo_mata_mata,
    _mapas_palpites_provisorio,
    _total_pontos_provisorio,
    agrupar_linhas_palpites,
    formatar_palpites_provisorio_texto,
    formatar_palpites_texto,
    listar_palpites_jogos,
    nome_arquivo_palpites,
    nome_arquivo_rodada,
    participantes_ordenados_provisorio,
    rotulo_grupo_palpite,
    rotulo_vencedor_jogo,
)
from src.thdfm_parser import parse_thdfm_csv

from src.data_paths import BOLAO_CSV, DATA_DIR, RESULTADOS_CSV, resolver_arquivo_base


BOLAO_PATH = resolver_arquivo_base("bolao.csv", data_dir=DATA_DIR)
RESULTADOS_PATH = resolver_arquivo_base("resultados.csv", data_dir=DATA_DIR)


@unittest.skipUnless(BOLAO_PATH.exists(), "CSV do bolao ausente")
class TestPalpitesView(unittest.TestCase):
    def setUp(self):
        self.bolao = parse_thdfm_csv(BOLAO_PATH)
        aplicar_resultados_externos(self.bolao, RESULTADOS_PATH)
        jogo1 = next(j for j in self.bolao.jogos if j.id == 1)
        if not jogo1.realizado:
            jogo1.gols_casa = 2
            jogo1.gols_fora = 0

    def test_lista_palpites_do_jogo(self):
        blocos = listar_palpites_jogos(self.bolao, [1])
        self.assertEqual(len(blocos), 1)
        self.assertEqual(blocos[0].jogo.id, 1)
        self.assertEqual(len(blocos[0].linhas), 25)
        self.assertTrue(all(linha.pontos is not None for linha in blocos[0].linhas))

    def test_ordenacao_por_pontos(self):
        blocos = listar_palpites_jogos(self.bolao, [1])
        pontos = [linha.pontos or 0 for linha in blocos[0].linhas]
        self.assertEqual(pontos, sorted(pontos, reverse=True))

    def test_formatar_texto(self):
        blocos = listar_palpites_jogos(self.bolao, [1])
        texto = formatar_palpites_texto(blocos)
        self.assertIn("Jogo 1:", texto)
        self.assertIn("Resultado:", texto)
        self.assertIn("Palpite", texto)

    def test_nome_arquivo(self):
        self.assertEqual(nome_arquivo_palpites([51, 52], "png"), "palpites_j51_52.png")
        self.assertEqual(
            nome_arquivo_palpites([51], "png", provisorio=True),
            "palpites_provisorios_j51.png",
        )
        self.assertEqual(nome_arquivo_rodada([51, 52]), "rodada_j51_52.png")

    def test_classificacao_provisorio(self):
        jogo = next(j for j in self.bolao.jogos if j.id == 1)
        jogo.gols_casa = 0
        jogo.gols_fora = 0
        blocos = listar_palpites_jogos(self.bolao, [1])
        linhas = blocos[0].linhas

        self.assertEqual(rotulo_vencedor_jogo(jogo), "Empate")
        for linha in linhas:
            if linha.palpite_casa == 0 and linha.palpite_fora == 0:
                self.assertEqual(linha.categoria, "Placar")
                self.assertTrue(linha.acertou_vencedor)
            elif linha.palpite_fora == 0:
                self.assertEqual(linha.categoria, "Gols fora")
            elif linha.palpite_casa == linha.palpite_fora:
                self.assertEqual(linha.categoria, "Nada")
                self.assertTrue(linha.acertou_vencedor)
            else:
                self.assertEqual(linha.categoria, "Nada")
                self.assertFalse(linha.acertou_vencedor)

    def test_formatar_provisorio(self):
        jogo = next(j for j in self.bolao.jogos if j.id == 1)
        jogo.gols_casa = 1
        jogo.gols_fora = 0
        blocos = listar_palpites_jogos(self.bolao, [1])
        texto = formatar_palpites_provisorio_texto(blocos)
        self.assertIn("PALPITES PROVISORIOS", texto)
        self.assertIn("Quesito", texto)
        self.assertIn("Venc", texto)
        self.assertIn("Pts", texto)
        participantes = participantes_ordenados_provisorio(blocos)
        _, mapas = _mapas_palpites_provisorio(blocos)
        totais = [_total_pontos_provisorio(nome, mapas) for nome in participantes]
        self.assertEqual(totais, sorted(totais, reverse=True))

    def test_jogo_inexistente(self):
        with self.assertRaises(ValueError):
            listar_palpites_jogos(self.bolao, [999])

    def test_penaltis_no_texto_mata_mata(self):
        jogo = Jogo(
            id=73,
            data="28 DE JUNHO",
            casa="Canadá",
            fora="África do Sul",
            gols_casa=0,
            gols_fora=0,
        )
        palpites = [
            Palpite("Ana", 73, 0, 0, vencedor_penaltis="Canadá"),
            Palpite("Bob", 73, 1, 0),
        ]
        bolao = BolaoData(jogos=[jogo], participantes=["Ana", "Bob"], palpites=palpites)
        blocos = listar_palpites_jogos(bolao, [73])
        texto = formatar_palpites_texto(blocos)
        self.assertTrue(_jogo_mata_mata(jogo))
        self.assertIn("Pen.", texto)
        self.assertIn("Canadá", texto)
        self.assertIn("Ana", texto)
        linha_bob = next(l for l in blocos[0].linhas if l.participante == "Bob")
        self.assertEqual(linha_bob.penaltis_texto, "-")


class TestAgrupamentoPalpites(unittest.TestCase):
    def test_rotulo_vitoria_casa(self) -> None:
        jogo = Jogo(id=1, data="", casa="Brasil", fora="Mexico", gols_casa=0, gols_fora=0)
        linha = PalpiteLinha("Ana", 2, 0)
        self.assertEqual(rotulo_grupo_palpite(jogo, linha), "Brasil")

    def test_rotulo_vitoria_fora(self) -> None:
        jogo = Jogo(id=1, data="", casa="Brasil", fora="Mexico", gols_casa=0, gols_fora=0)
        linha = PalpiteLinha("Ana", 0, 1)
        self.assertEqual(rotulo_grupo_palpite(jogo, linha), "Mexico")

    def test_rotulo_empate_grupos(self) -> None:
        jogo = Jogo(id=1, data="", casa="Brasil", fora="Mexico", gols_casa=0, gols_fora=0)
        linha = PalpiteLinha("Ana", 1, 1)
        self.assertEqual(rotulo_grupo_palpite(jogo, linha), EMPATE_GRUPO)

    def test_rotulo_empate_mata_mata_com_pen(self) -> None:
        jogo = Jogo(id=73, data="", casa="Canada", fora="Africa do Sul", gols_casa=0, gols_fora=0)
        linha = PalpiteLinha("Ana", 0, 0, vencedor_penaltis="Canada")
        self.assertEqual(rotulo_grupo_palpite(jogo, linha), "Canada")

    def test_rotulo_empate_mata_mata_sem_pen(self) -> None:
        jogo = Jogo(id=73, data="", casa="Canada", fora="Africa do Sul", gols_casa=0, gols_fora=0)
        linha = PalpiteLinha("Ana", 0, 0)
        self.assertEqual(rotulo_grupo_palpite(jogo, linha), EMPATE_SEM_PEN)

    def test_agrupar_ordem_casa_empate_fora(self) -> None:
        jogo = Jogo(id=1, data="", casa="Australia", fora="Egito", gols_casa=0, gols_fora=0)
        linhas = [
            PalpiteLinha("Zeca", 0, 2),
            PalpiteLinha("Ana", 2, 0),
            PalpiteLinha("Bob", 1, 1),
        ]
        grupos = agrupar_linhas_palpites(jogo, linhas)
        self.assertEqual([nome for nome, _ in grupos], ["Australia", EMPATE_GRUPO, "Egito"])
        self.assertEqual([linha.participante for linha in grupos[0][1]], ["Ana"])
        self.assertEqual([linha.participante for linha in grupos[2][1]], ["Zeca"])


if __name__ == "__main__":
    unittest.main()
