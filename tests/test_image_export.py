import unittest

from PIL import Image

from src.image_export import (
    PAL_ZONA_AZUL,
    PAL_ZONA_LIDER,
    PAL_ZONA_VERDE,
    PAL_ZONA_NEUTRA,
    PAL_ZONA_VERMELHA,
    _cor_fundo_zona_posicao,
    combinar_imagens_horizontal,
)


class TestImageExport(unittest.TestCase):
    def test_zonas_posicao(self):
        self.assertEqual(_cor_fundo_zona_posicao(1), PAL_ZONA_LIDER)
        self.assertEqual(_cor_fundo_zona_posicao(2), PAL_ZONA_AZUL)
        self.assertEqual(_cor_fundo_zona_posicao(6), PAL_ZONA_AZUL)
        self.assertEqual(_cor_fundo_zona_posicao(7), PAL_ZONA_VERDE)
        self.assertEqual(_cor_fundo_zona_posicao(13), PAL_ZONA_VERDE)
        self.assertEqual(_cor_fundo_zona_posicao(14), PAL_ZONA_NEUTRA)
        self.assertEqual(_cor_fundo_zona_posicao(20), PAL_ZONA_NEUTRA)
        self.assertEqual(_cor_fundo_zona_posicao(21), PAL_ZONA_VERMELHA)
        self.assertEqual(_cor_fundo_zona_posicao(25), PAL_ZONA_VERMELHA)

    def test_combinar_imagens_horizontal(self):
        esquerda = Image.new("RGB", (100, 80), (10, 10, 10))
        direita = Image.new("RGB", (200, 120), (20, 20, 20))
        combinada = combinar_imagens_horizontal([esquerda, direita], espaco=20)

        self.assertEqual(combinada.size, (320, 120))
        self.assertEqual(combinada.getpixel((50, 40)), (10, 10, 10))
        self.assertEqual(combinada.getpixel((200, 60)), (20, 20, 20))

    def test_combinar_imagens_horizontal_alinhar_topo(self):
        esquerda = Image.new("RGB", (100, 80), (10, 10, 10))
        direita = Image.new("RGB", (200, 120), (20, 20, 20))
        combinada = combinar_imagens_horizontal(
            [esquerda, direita],
            espaco=20,
            alinhar_topo=True,
        )

        self.assertEqual(combinada.getpixel((50, 10)), (10, 10, 10))
        self.assertEqual(combinada.getpixel((200, 10)), (20, 20, 20))


if __name__ == "__main__":
    unittest.main()
