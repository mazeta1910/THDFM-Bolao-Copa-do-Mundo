import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from src.cli import carregar_bolao
from src.image_export import _altura_corpo_tabela_palpites, _titulo_palpites_jogo
from src.palpites_view import agrupar_linhas_palpites, listar_palpites_jogos


class TestTituloPalpites(unittest.TestCase):
    def test_titulo_jogo_unico(self) -> None:
        jogo = MagicMock(id=88, casa="Austrália", fora="Egito")
        self.assertEqual(
            _titulo_palpites_jogo(jogo),
            "PALPITES - JOGO 88: AUSTRÁLIA X EGITO",
        )


class TestExportPalpitesAgrupado(unittest.TestCase):
    def test_altura_tabela_inclui_faixas_de_grupo(self) -> None:
        bolao = carregar_bolao()
        blocos = listar_palpites_jogos(bolao, [88])
        grupos = agrupar_linhas_palpites(blocos[0].jogo, blocos[0].linhas)
        altura = _altura_corpo_tabela_palpites(blocos[0], 34)
        self.assertEqual(altura, len(blocos[0].linhas) * 34 + len(grupos) * 32)

    def test_export_png_agrupado(self) -> None:
        from src.image_export import exportar_palpites_png

        bolao = carregar_bolao()
        blocos = listar_palpites_jogos(bolao, [88])
        with tempfile.TemporaryDirectory() as tmp:
            caminho = Path(tmp) / "palpites.png"
            exportar_palpites_png(blocos, caminho)
            self.assertTrue(caminho.is_file())
            self.assertGreater(caminho.stat().st_size, 10_000)


if __name__ == "__main__":
    unittest.main()
