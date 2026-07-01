import unittest
from pathlib import Path

from src.data_paths import (
    DATA_DIR,
    resolver_arquivo_base,
    resolver_arquivo_fonte,
)
from src.loader import aplicar_resultados_externos
from src.ranking import gerar_classificacao_jogos
from src.thdfm_parser import parse_thdfm_csv

BOLAO_PATH = resolver_arquivo_base("bolao.csv", data_dir=DATA_DIR)
REFERENCIA_PATH = resolver_arquivo_fonte(
    "classificacao_referencia.csv",
    data_dir=DATA_DIR,
)
RESULTADOS_PATH = resolver_arquivo_base("resultados.csv", data_dir=DATA_DIR)


def _resultados_preenchidos() -> bool:
    path = RESULTADOS_PATH
    if not path.exists():
        return False
    import csv

    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("gols_casa", "").strip() and row.get("gols_fora", "").strip():
                return True
    return False


@unittest.skipUnless(BOLAO_PATH.exists(), "CSV do bolão ausente")
class TestThdfmParser(unittest.TestCase):
    def test_extrai_jogos_e_participantes(self):
        bolao = parse_thdfm_csv(BOLAO_PATH)
        self.assertEqual(len(bolao.jogos), 88)
        self.assertEqual(len(bolao.participantes), 25)
        self.assertEqual(len(bolao.palpites), 88 * 25)

    def test_primeiro_jogo(self):
        bolao = parse_thdfm_csv(BOLAO_PATH)
        jogo1 = bolao.jogos[0]
        self.assertEqual(jogo1.id, 1)
        self.assertEqual(jogo1.casa, "México")
        self.assertEqual(jogo1.fora, "África do Sul")
        self.assertEqual(jogo1.gols_casa, 2)
        self.assertEqual(jogo1.gols_fora, 0)

    def test_jogos_realizados(self):
        bolao = parse_thdfm_csv(BOLAO_PATH)
        realizados = sum(1 for j in bolao.jogos if j.realizado)
        self.assertEqual(realizados, 48)

    def test_jogo_sem_resultado(self):
        bolao = parse_thdfm_csv(BOLAO_PATH)
        jogo88 = bolao.jogos[-1]
        self.assertEqual(jogo88.id, 88)
        self.assertFalse(jogo88.realizado)


@unittest.skipUnless(
    BOLAO_PATH.exists() and REFERENCIA_PATH.exists() and _resultados_preenchidos(),
    "CSVs de dados ausentes ou bolao sem resultados registrados",
)
class TestParity(unittest.TestCase):
    def test_classificacao_soma_consistente(self):
        bolao = parse_thdfm_csv(BOLAO_PATH)
        aplicar_resultados_externos(bolao, RESULTADOS_PATH)
        calculada = gerar_classificacao_jogos(bolao)
        for linha in calculada:
            esperado = linha.placar + linha.vencedor + linha.gols_casa + linha.gols_fora
            self.assertEqual(linha.soma, esperado, linha.participante)


if __name__ == "__main__":
    unittest.main()
