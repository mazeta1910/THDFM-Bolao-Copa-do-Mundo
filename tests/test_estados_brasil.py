import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from src.bandeiras import bandeira_time, iso_time, sigla_time
from src.estados_brasil import times_estados, ufs_registradas
from src.flag_cache import baixar_bandeira, codigos_bandeira_necessarios


class TestLoteInicialEstados(unittest.TestCase):
    def test_nomes_canonicos_parana_e_rs(self):
        nomes = times_estados()
        self.assertIn("Time do Paraná", nomes)
        self.assertIn("Time do RS", nomes)
        self.assertTrue({"PR", "RS"}.issubset(ufs_registradas()))

    def test_iso_e_sigla_time_do_parana(self):
        self.assertEqual(iso_time("Time do Paraná"), "BR-PR")
        self.assertEqual(iso_time("Paraná"), "BR-PR")
        self.assertEqual(iso_time("Time do PR"), "BR-PR")
        self.assertEqual(sigla_time("Time do Paraná"), "PR")

    def test_iso_e_sigla_time_do_rs(self):
        self.assertEqual(iso_time("Time do RS"), "BR-RS")
        self.assertEqual(iso_time("Rio Grande do Sul"), "BR-RS")
        self.assertEqual(iso_time("RS"), "BR-RS")
        self.assertEqual(sigla_time("Time do RS"), "RS")

    def test_bandeira_texto_usa_brasil(self):
        self.assertEqual(bandeira_time("Time do Paraná"), bandeira_time("Brasil"))
        self.assertEqual(bandeira_time("Time do RS"), bandeira_time("Brasil"))

    def test_codigos_necessarios_incluem_estados_do_lote(self):
        codigos = codigos_bandeira_necessarios()
        self.assertIn("BR-PR", codigos)
        self.assertIn("BR-RS", codigos)

    def test_gera_bandeira_estado_localmente(self):
        with tempfile.TemporaryDirectory() as tmp:
            flag_dir = Path(tmp)
            with patch("src.flag_cache.FLAG_DIR", flag_dir):
                caminho = baixar_bandeira("BR-PR", forcar=True)
                self.assertEqual(caminho, flag_dir / "BR-PR.png")
                self.assertTrue(caminho.is_file())
                with Image.open(caminho) as img:
                    self.assertEqual(img.size, (80, 56))

    def test_nao_colide_com_paises_existentes(self):
        # Panama/Espanha seguem com ISO de pais; estados usam prefixo BR-.
        self.assertEqual(iso_time("Panamá"), "PA")
        self.assertEqual(iso_time("Espanha"), "ES")
        self.assertEqual(iso_time("Time do ES"), "BR-ES")
        self.assertTrue(iso_time("Time do Paraná").startswith("BR-"))


class TestLoteSudesteSulDF(unittest.TestCase):
    def test_nomes_canonicos_lote2(self):
        self.assertEqual(
            {
                "Time de SP",
                "Time do RJ",
                "Time de MG",
                "Time de SC",
                "Time do ES",
                "Time do DF",
            },
            set(times_estados())
            & {
                "Time de SP",
                "Time do RJ",
                "Time de MG",
                "Time de SC",
                "Time do ES",
                "Time do DF",
            },
        )

    def test_aliases_e_codigos_lote2(self):
        casos = [
            ("Time de SP", "BR-SP", "SP"),
            ("São Paulo", "BR-SP", "SP"),
            ("Time do RJ", "BR-RJ", "RJ"),
            ("Rio de Janeiro", "BR-RJ", "RJ"),
            ("Time de MG", "BR-MG", "MG"),
            ("Minas Gerais", "BR-MG", "MG"),
            ("Time de SC", "BR-SC", "SC"),
            ("Time do ES", "BR-ES", "ES"),
            ("Espírito Santo", "BR-ES", "ES"),
            ("Time do DF", "BR-DF", "DF"),
            ("Distrito Federal", "BR-DF", "DF"),
        ]
        for nome, codigo, uf in casos:
            with self.subTest(nome=nome):
                self.assertEqual(iso_time(nome), codigo)
                self.assertEqual(sigla_time(nome), uf)


if __name__ == "__main__":
    unittest.main()
