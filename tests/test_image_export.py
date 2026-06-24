import unittest

from PIL import Image

from src.image_export import combinar_imagens_horizontal


class TestImageExport(unittest.TestCase):
    def test_combinar_imagens_horizontal(self):
        esquerda = Image.new("RGB", (100, 80), (10, 10, 10))
        direita = Image.new("RGB", (200, 120), (20, 20, 20))
        combinada = combinar_imagens_horizontal([esquerda, direita], espaco=20)

        self.assertEqual(combinada.size, (320, 120))
        self.assertEqual(combinada.getpixel((50, 40)), (10, 10, 10))
        self.assertEqual(combinada.getpixel((200, 60)), (20, 20, 20))


if __name__ == "__main__":
    unittest.main()
