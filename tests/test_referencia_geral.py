import unittest
from pathlib import Path

from src.cli import carregar_bolao
from src.ranking import (
    carregar_classificacao_referencia,
    classificacao_geral_ativa,
    resolver_referencia_geral_csv,
)

DATA = Path(__file__).resolve().parent.parent / "data"
REFERENCIA = DATA / "BOLÃO THDFM WC26 - CLASSIFICAÇÃO PROVISÓRIA (1).csv"


@unittest.skipUnless(REFERENCIA.exists(), "planilha de referencia ausente")
class TestReferenciaGeral(unittest.TestCase):
    def test_carrega_secao_grupos_32_avos(self) -> None:
        linhas = carregar_classificacao_referencia(REFERENCIA, secao="grupos_32avos")
        self.assertEqual(len(linhas), 25)
        self.assertEqual(linhas[0].participante.strip(), "Juan")
        self.assertEqual(linhas[0].soma, 219)

    def test_tabela_geral_usa_referencia_ate_j79(self) -> None:
        bolao = carregar_bolao()
        classificacao = classificacao_geral_ativa(bolao, data_dir=DATA)
        por_nome = {linha.participante.strip(): linha for linha in classificacao}
        self.assertEqual(por_nome["Juan"].soma, 219)
        self.assertEqual(por_nome["Mazeta"].soma, 194)
        self.assertEqual(por_nome["Benevides"].soma, 218)

    def test_resolver_encontra_arquivo_com_secao(self) -> None:
        path = resolver_referencia_geral_csv(DATA)
        self.assertIsNotNone(path)
        self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
