import csv
import tempfile
import unittest
from pathlib import Path

from src.loader import (
    aplicar_resultados_externos,
    importar_resultados_da_planilha,
    limpar_todos_resultados,
    salvar_resultados,
)
from src.data_paths import resolver_arquivo_base
from src.thdfm_parser import parse_thdfm_csv


class TestLoaderResultados(unittest.TestCase):
    def test_resultados_vazios_ignoram_placar_da_planilha(self):
        with tempfile.TemporaryDirectory() as tmp:
            origem = resolver_arquivo_base("bolao.csv")
            if not origem.exists():
                self.skipTest("CSV do bolão ausente")

            destino = Path(tmp) / "resultados.csv"
            bolao = parse_thdfm_csv(origem)
            limpar_todos_resultados(bolao)
            salvar_resultados(bolao, destino)

            bolao_carregado = parse_thdfm_csv(origem)
            aplicar_resultados_externos(bolao_carregado, destino)
            self.assertEqual(sum(1 for j in bolao_carregado.jogos if j.realizado), 0)

    def test_importar_resultados_da_planilha(self):
        origem = resolver_arquivo_base("bolao.csv")
        if not origem.exists():
            self.skipTest("CSV do bolão ausente")

        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / "resultados.csv"
            realizados, total = importar_resultados_da_planilha(origem, destino)
            self.assertEqual(total, 96)
            self.assertGreater(realizados, 0)

    def test_resultados_externos_sobrescrevem_planilha(self):
        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / "resultados.csv"
            with destino.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["jogo_id", "gols_casa", "gols_fora"])
                writer.writerow([1, 3, 2])

            from src.models import BolaoData, Jogo

            bolao = BolaoData(
                jogos=[Jogo(id=1, data="", casa="A", fora="B", gols_casa=0, gols_fora=0)],
                participantes=[],
                palpites=[],
            )
            aplicar_resultados_externos(bolao, destino)
            self.assertEqual(bolao.jogos[0].gols_casa, 3)
            self.assertEqual(bolao.jogos[0].gols_fora, 2)


if __name__ == "__main__":
    unittest.main()
