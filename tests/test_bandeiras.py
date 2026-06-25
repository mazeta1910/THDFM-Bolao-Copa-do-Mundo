import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from src.bandeiras import iso_time
from src.bandeiras_img import imagem_bandeira, largura_confronto
from src.flag_cache import codigo_flagcdn, codigos_bandeira_necessarios


class TestFlagCache(unittest.TestCase):
    def test_codigo_flagcdn_especiais(self):
        self.assertEqual(codigo_flagcdn("SCO"), "gb-sct")
        self.assertEqual(codigo_flagcdn("GB"), "gb-eng")
        self.assertEqual(codigo_flagcdn("MX"), "mx")

    def test_codigos_necessarios_inclui_escocia(self):
        self.assertIn("SCO", codigos_bandeira_necessarios())
        self.assertIn("BR", codigos_bandeira_necessarios())


class TestBandeiras(unittest.TestCase):
    def test_iso_time(self):
        self.assertEqual(iso_time("Tchéquia"), "CZ")
        self.assertEqual(iso_time("África do Sul"), "ZA")
        self.assertEqual(iso_time("México"), "MX")
        self.assertEqual(iso_time("Coréia do Sul"), "KR")
        self.assertEqual(iso_time("Curaçau"), "CW")
        self.assertEqual(iso_time("Curaçao"), "CW")

    def test_imagem_bandeira_do_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            flag_dir = Path(tmp)
            caminho = flag_dir / "MX.png"
            imagem = Image.new("RGB", (80, 60), (0, 120, 60))
            imagem.save(caminho)

            with patch("src.flag_cache.FLAG_DIR", flag_dir):
                imagem_bandeira.cache_clear()
                resultado = imagem_bandeira("MX")
                self.assertEqual(resultado.size, (40, 28))
                self.assertNotEqual(resultado.getpixel((5, 5)), (71, 85, 105, 255))

    def test_largura_confronto(self):
        from PIL import ImageFont

        fonte = ImageFont.load_default()
        self.assertGreater(largura_confronto(fonte), 70)


if __name__ == "__main__":
    unittest.main()
