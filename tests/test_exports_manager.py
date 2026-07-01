import tempfile
import unittest
from pathlib import Path

from src.exports_manager import (
    caminho_fase,
    caminho_palpites,
    caminho_ultimo,
    limpar_exports_legados,
    migrar_estrutura_ultimo,
    ultimo_dir,
)


class TestExportsManager(unittest.TestCase):
    def test_caminhos_usam_subpastas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            self.assertEqual(
                caminho_ultimo(data, "classificacao_png").name,
                "classificacao.png",
            )
            self.assertEqual(
                caminho_ultimo(data, "classificacao_png").parent.name,
                "png",
            )
            self.assertEqual(caminho_ultimo(data, "classificacao_txt").parent.name, "txt")
            self.assertEqual(caminho_ultimo(data, "classificacao_csv").parent.name, "csv")
            self.assertEqual(caminho_fase(data, "grupos", "png").parent.name, "png")
            self.assertEqual(caminho_palpites(data, False, "txt").parent.name, "txt")

    def test_migrar_estrutura_ultimo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            destino = ultimo_dir(data)
            (destino / "classificacao.png").write_bytes(b"png")
            (destino / "classificacao.txt").write_text("txt", encoding="utf-8")
            (destino / "classificacao.csv").write_text("csv", encoding="utf-8")

            movidos = migrar_estrutura_ultimo(data)
            self.assertEqual(len(movidos), 3)
            self.assertTrue((destino / "png" / "classificacao.png").exists())
            self.assertTrue((destino / "txt" / "classificacao.txt").exists())
            self.assertTrue((destino / "csv" / "classificacao.csv").exists())
            self.assertFalse((destino / "classificacao.png").exists())

    def test_limpar_exports_legados_na_raiz(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            legado = data / "palpites_j51_52.txt"
            legado.write_text("x", encoding="utf-8")
            removidos = limpar_exports_legados(data)
            self.assertIn("palpites_j51_52.txt", removidos)
            self.assertFalse(legado.exists())


if __name__ == "__main__":
    unittest.main()
