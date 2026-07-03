import unittest
from unittest.mock import MagicMock

from src.image_export import _titulo_palpites_jogo


class TestTituloPalpites(unittest.TestCase):
    def test_titulo_jogo_unico(self) -> None:
        jogo = MagicMock(id=88, casa="Austrália", fora="Egito")
        self.assertEqual(
            _titulo_palpites_jogo(jogo),
            "PALPITES - JOGO 88: AUSTRÁLIA X EGITO",
        )


if __name__ == "__main__":
    unittest.main()
