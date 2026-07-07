import unittest
from pathlib import Path

from src.cli import carregar_bolao
from src.ranking import (
    carregar_classificacao_referencia,
    classificacao_geral_ativa,
    resolver_referencia_geral_csv,
)

DATA = Path(__file__).resolve().parent.parent / "data"
CLASSIFICACAO_18AVOS = DATA / "base" / "classificacao_18avos.csv"


@unittest.skipUnless(CLASSIFICACAO_18AVOS.exists(), "classificacao_18avos.csv ausente")
class TestClassificacao18Avos(unittest.TestCase):
    def test_carrega_secao_oitavas(self) -> None:
        linhas = carregar_classificacao_referencia(
            CLASSIFICACAO_18AVOS, secao="grupos_32avos_oitavas"
        )
        self.assertEqual(len(linhas), 25)
        xonha = next(l for l in linhas if l.participante.strip() == "Xonha")
        self.assertEqual(xonha.soma, 394)

    def test_tabela_geral_usa_baseline_ate_j94(self) -> None:
        bolao = carregar_bolao()
        classificacao = classificacao_geral_ativa(bolao, data_dir=DATA)
        por_nome = {linha.participante.strip(): linha for linha in classificacao}
        self.assertEqual(por_nome["Xonha"].soma, 394)
        self.assertEqual(por_nome["Benevides"].soma, 396)

    def test_resolver_prioriza_classificacao_18avos(self) -> None:
        path = resolver_referencia_geral_csv(DATA)
        self.assertIsNotNone(path)
        self.assertEqual(path.name, "classificacao_18avos.csv")


if __name__ == "__main__":
    unittest.main()
