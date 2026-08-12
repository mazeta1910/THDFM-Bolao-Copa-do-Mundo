import tempfile
import unittest
from pathlib import Path

from scripts.gerar_grids_estados import (
    TAMANHO,
    gerar_cinco_grids,
    gerar_grid_aleatorio,
    gerar_n_grids,
)
from src.categorias_grid import CATEGORIAS_GRID
from src.estados_brasil import ufs_registradas


class TestGridsHoopsStyle(unittest.TestCase):
    def test_estrutura_times_nas_linhas_categorias_nas_colunas(self):
        grid = gerar_grid_aleatorio(1, seed=42)
        self.assertEqual(len(grid.times), TAMANHO)
        self.assertEqual(len(grid.categorias), TAMANHO)

        ufs = [e.uf for e in grid.times]
        self.assertEqual(len(ufs), len(set(ufs)))
        self.assertTrue(set(ufs).issubset(ufs_registradas()))

        ids = [c.id for c in grid.categorias]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(set(ids).issubset({c.id for c in CATEGORIAS_GRID}))

    def test_categorias_priorizam_tipos_distintos(self):
        # Com seed fixa, deve haver pelo menos 2 tipos diferentes nas colunas.
        grid = gerar_grid_aleatorio(1, seed=7)
        tipos = {c.tipo for c in grid.categorias}
        self.assertGreaterEqual(len(tipos), 2)

    def test_cinco_grids_reproduziveis_e_distintos(self):
        a = gerar_n_grids(5, seed_base=20260811)
        b = gerar_n_grids(5, seed_base=20260811)
        chaves_a = [
            tuple(e.uf for e in g.times) + tuple(c.id for c in g.categorias) for g in a
        ]
        chaves_b = [
            tuple(e.uf for e in g.times) + tuple(c.id for c in g.categorias) for g in b
        ]
        self.assertEqual(chaves_a, chaves_b)
        self.assertEqual(len(set(chaves_a)), 5)

    def test_gera_cinco_pngs(self):
        with tempfile.TemporaryDirectory() as tmp:
            gerados = gerar_cinco_grids(Path(tmp), seed_base=20260811)
            self.assertEqual(len(gerados), 5)
            for caminho in gerados:
                self.assertTrue(caminho.is_file())
                self.assertGreater(caminho.stat().st_size, 2000)


if __name__ == "__main__":
    unittest.main()
