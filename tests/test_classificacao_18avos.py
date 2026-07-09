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
        self.assertEqual(xonha.soma, 409)

    def test_tabela_geral_usa_baseline_ate_j96(self) -> None:
        from src.ranking import calcular_pontos_faixa, JOGOS_BASELINE_OITAVAS

        bolao = carregar_bolao()
        classificacao = classificacao_geral_ativa(bolao, data_dir=DATA)
        por_nome = {linha.participante.strip(): linha for linha in classificacao}
        novos = {j.id for j in bolao.jogos if j.realizado} - set(JOGOS_BASELINE_OITAVAS)
        extras_xonha = calcular_pontos_faixa(bolao, novos)["Xonha"].soma if novos else 0
        self.assertEqual(por_nome["Xonha"].soma, 409 + extras_xonha)

    def test_resolver_prioriza_classificacao_18avos(self) -> None:
        path = resolver_referencia_geral_csv(DATA)
        self.assertIsNotNone(path)
        self.assertEqual(path.name, "classificacao_18avos.csv")

    def test_fase_ate_oitavas_bate_referencia(self) -> None:
        from src.ranking import gerar_classificacao_ate_oitavas

        bolao = carregar_bolao()
        referencia = {
            linha.participante.strip(): linha.soma
            for linha in carregar_classificacao_referencia(
                CLASSIFICACAO_18AVOS, secao="grupos_32avos_oitavas"
            )
        }
        calculada = {
            linha.participante.strip(): linha.soma
            for linha in gerar_classificacao_ate_oitavas(bolao)
        }
        self.assertEqual(calculada, referencia)


if __name__ == "__main__":
    unittest.main()
