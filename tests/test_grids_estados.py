import tempfile
import unittest
from pathlib import Path

from scripts.gerar_grids_estados import (
    TAMANHO,
    gerar_cinco_grids,
    gerar_grid_aleatorio,
    gerar_n_grids,
)
from src.estados_brasil import ufs_registradas


class TestGridsJogo(unittest.TestCase):
    def test_grid_aleatorio_usa_6_ufs_distintas(self):
        grid = gerar_grid_aleatorio(1, seed=42)
        ufs = [e.uf for e in (*grid.colunas, *grid.linhas)]
        self.assertEqual(len(grid.colunas), TAMANHO)
        self.assertEqual(len(grid.linhas), TAMANHO)
        self.assertEqual(len(ufs), len(set(ufs)))
        self.assertTrue(set(ufs).issubset(ufs_registradas()))

    def test_cinco_grids_sao_distintos_e_reproduziveis(self):
        a = gerar_n_grids(5, seed_base=20260811)
        b = gerar_n_grids(5, seed_base=20260811)
        self.assertEqual(len(a), 5)
        chaves_a = [tuple(e.uf for e in (*g.colunas, *g.linhas)) for g in a]
        chaves_b = [tuple(e.uf for e in (*g.colunas, *g.linhas)) for g in b]
        self.assertEqual(chaves_a, chaves_b)
        self.assertEqual(len(set(chaves_a)), 5)

    def test_gera_cinco_pngs_de_jogo(self):
        with tempfile.TemporaryDirectory() as tmp:
            gerados = gerar_cinco_grids(Path(tmp), seed_base=20260811)
            self.assertEqual(len(gerados), 5)
            for caminho in gerados:
                with self.subTest(nome=caminho.name):
                    self.assertTrue(caminho.is_file())
                    self.assertGreater(caminho.stat().st_size, 2000)
                    self.assertTrue(caminho.name.startswith("grid_jogo_"))


if __name__ == "__main__":
    unittest.main()
