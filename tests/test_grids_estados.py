import tempfile
import unittest
from pathlib import Path

from scripts.gerar_grids_estados import gerar_cinco_grids
from src.gerador_grid import (
    MIN_RESPOSTAS_CELULA,
    TAMANHO,
    gerar_grid_soluvel,
    gerar_n_grids,
)
from src.jogadores_grid import contar_intersecao, jogadores_grid


class TestSolubilidadeGrid(unittest.TestCase):
    def test_base_de_jogadores_carrega(self):
        self.assertGreaterEqual(len(jogadores_grid()), 50)

    def test_eixos_sorteiam_3_e_3_sem_repetir_criterio(self):
        grid = gerar_grid_soluvel(1, seed=42, minimo=MIN_RESPOSTAS_CELULA)
        self.assertEqual(len(grid.linhas), TAMANHO)
        self.assertEqual(len(grid.colunas), TAMANHO)
        ids = [c.id for c in (*grid.linhas, *grid.colunas)]
        self.assertEqual(len(ids), len(set(ids)))

    def test_todas_as_9_celulas_tem_minimo_de_respostas(self):
        grid = gerar_grid_soluvel(1, seed=99, minimo=5)
        for i, linha in enumerate(grid.linhas):
            for j, coluna in enumerate(grid.colunas):
                with self.subTest(linha=linha.id, coluna=coluna.id):
                    n = contar_intersecao(linha, coluna)
                    self.assertGreaterEqual(n, 5)
                    self.assertEqual(grid.contagens[i][j], n)

    def test_linhas_podem_nao_ser_somente_times(self):
        # Em varios seeds, deve aparecer pelo menos um grid com categoria na linha.
        viu_categoria_na_linha = False
        for seed in range(100, 160):
            grid = gerar_grid_soluvel(1, seed=seed, minimo=3)
            if any(c.tipo != "time" for c in grid.linhas):
                viu_categoria_na_linha = True
                break
        self.assertTrue(
            viu_categoria_na_linha,
            "Esperava criterios nao-time tambem nas linhas (pool unico).",
        )

    def test_cinco_grids_reproduziveis(self):
        a = gerar_n_grids(5, seed_base=20260811, minimo=3)
        b = gerar_n_grids(5, seed_base=20260811, minimo=3)
        chaves_a = [
            tuple(c.id for c in g.linhas) + tuple(c.id for c in g.colunas) for g in a
        ]
        chaves_b = [
            tuple(c.id for c in g.linhas) + tuple(c.id for c in g.colunas) for g in b
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
