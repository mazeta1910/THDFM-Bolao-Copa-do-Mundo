import tempfile
import unittest
from pathlib import Path

from src.data_paths import (
    caminho_base,
    caminho_fonte,
    ensure_data_layout,
    migrar_estrutura_data,
    resolver_arquivo_base,
    resolver_bolao_csv,
)


class TestDataPaths(unittest.TestCase):
    def test_migrar_para_base_e_fontes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            (data / "bolao.csv").write_text("x", encoding="utf-8")
            (data / "classificacao_referencia.csv").write_text("y", encoding="utf-8")

            movidos = migrar_estrutura_data(data)
            self.assertEqual(len(movidos), 2)
            self.assertTrue((data / "base" / "bolao.csv").exists())
            self.assertTrue((data / "fontes" / "classificacao_referencia.csv").exists())
            self.assertFalse((data / "bolao.csv").exists())

    def test_resolver_arquivo_base_legado(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            legado = data / "resultados.csv"
            legado.write_text("1,0,0\n", encoding="utf-8")
            self.assertEqual(resolver_arquivo_base("resultados.csv", data_dir=data), legado)

    def test_resolver_bolao_csv_prioriza_base(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            base = caminho_base("bolao.csv", data_dir=data)
            base.parent.mkdir(parents=True, exist_ok=True)
            base.write_text("bolao", encoding="utf-8")
            self.assertEqual(resolver_bolao_csv(data), base)

    def test_ensure_data_layout_cria_pastas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            ensure_data_layout(data)
            self.assertTrue((data / "base").is_dir())
            self.assertTrue((data / "fontes").is_dir())


if __name__ == "__main__":
    unittest.main()
