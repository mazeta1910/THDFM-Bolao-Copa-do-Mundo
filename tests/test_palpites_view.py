import unittest
from pathlib import Path

from src.loader import aplicar_resultados_externos
from src.palpites_view import (
    _mapas_palpites_provisorio,
    _total_pontos_provisorio,
    formatar_palpites_provisorio_texto,
    formatar_palpites_texto,
    listar_palpites_jogos,
    nome_arquivo_palpites,
    participantes_ordenados_provisorio,
    rotulo_vencedor_jogo,
)
from src.thdfm_parser import parse_thdfm_csv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOWNLOADS = Path.home() / "Downloads"


def _resolve_bolao() -> Path:
    candidatos = [
        DATA_DIR / "bolao.csv",
        DATA_DIR / "BOLÃO THDFM WC26 - Fase de grupos (1).csv",
        DOWNLOADS / "BOLÃO THDFM WC26 - Fase de grupos.csv",
    ]
    for path in candidatos:
        if path.exists():
            return path
    return candidatos[0]


BOLAO_PATH = _resolve_bolao()


@unittest.skipUnless(BOLAO_PATH.exists(), "CSV do bolao ausente")
class TestPalpitesView(unittest.TestCase):
    def setUp(self):
        self.bolao = parse_thdfm_csv(BOLAO_PATH)
        aplicar_resultados_externos(self.bolao, DATA_DIR / "resultados.csv")
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


if __name__ == "__main__":
    unittest.main()
