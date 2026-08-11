import tempfile
import unittest
from pathlib import Path

from scripts.gerar_grids_estados import REGIOES, gerar_cinco_grids
from src.estados_brasil import ufs_registradas


class TestGridsEstados(unittest.TestCase):
    def test_cinco_regioes_cobrem_27_ufs(self):
        ufs = {uf for _, grupo in REGIOES for uf in grupo}
        self.assertEqual(len(REGIOES), 5)
        self.assertEqual(ufs, ufs_registradas())

    def test_gera_cinco_grids_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            gerados = gerar_cinco_grids(pasta)
            self.assertEqual(len(gerados), 5)
            for caminho in gerados:
                with self.subTest(nome=caminho.name):
                    self.assertTrue(caminho.is_file())
                    self.assertGreater(caminho.stat().st_size, 1000)
                    self.assertTrue(caminho.name.startswith("grid_"))
                    self.assertTrue(caminho.name.endswith(".png"))


if __name__ == "__main__":
    unittest.main()
