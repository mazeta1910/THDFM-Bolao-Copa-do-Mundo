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


class TestLoteNordeste(unittest.TestCase):
    def test_nomes_canonicos_nordeste(self):
        esperados = {
            "Time da Bahia",
            "Time de Pernambuco",
            "Time do Ceará",
            "Time do Maranhão",
            "Time da Paraíba",
            "Time de Alagoas",
            "Time de Sergipe",
            "Time do RN",
            "Time do Piauí",
        }
        self.assertTrue(esperados.issubset(set(times_estados())))

    def test_aliases_e_codigos_nordeste(self):
        casos = [
            ("Time da Bahia", "BR-BA", "BA"),
            ("Bahia", "BR-BA", "BA"),
            ("Time de Pernambuco", "BR-PE", "PE"),
            ("Time do Ceará", "BR-CE", "CE"),
            ("Ceará", "BR-CE", "CE"),
            ("Time do Maranhão", "BR-MA", "MA"),
            ("Time da Paraíba", "BR-PB", "PB"),
            ("Time de Alagoas", "BR-AL", "AL"),
            ("Time de Sergipe", "BR-SE", "SE"),
            ("Time do RN", "BR-RN", "RN"),
            ("Rio Grande do Norte", "BR-RN", "RN"),
            ("Time do Piauí", "BR-PI", "PI"),
        ]
        for nome, codigo, uf in casos:
            with self.subTest(nome=nome):
                self.assertEqual(iso_time(nome), codigo)
                self.assertEqual(sigla_time(nome), uf)

    def test_bahia_nao_sobrescreve_bosnia(self):
        self.assertEqual(iso_time("Bósnia e Herzegovina"), "BA")
        self.assertEqual(iso_time("Time da Bahia"), "BR-BA")


class TestLoteNorteCentroOeste(unittest.TestCase):
    def test_nomes_canonicos_norte_centro_oeste(self):
        esperados = {
            "Time do Acre",
            "Time do Amapá",
            "Time do Amazonas",
            "Time do Pará",
            "Time de Rondônia",
            "Time de Roraima",
            "Time do Tocantins",
            "Time de Goiás",
            "Time do MT",
            "Time do MS",
        }
        self.assertTrue(esperados.issubset(set(times_estados())))

    def test_aliases_e_codigos_norte_centro_oeste(self):
        casos = [
            ("Time do Acre", "BR-AC", "AC"),
            ("Acre", "BR-AC", "AC"),
            ("Time do Amapá", "BR-AP", "AP"),
            ("Time do Amazonas", "BR-AM", "AM"),
            ("Time do Pará", "BR-PA", "PA"),
            ("Pará", "BR-PA", "PA"),
            ("Time de Rondônia", "BR-RO", "RO"),
            ("Time de Roraima", "BR-RR", "RR"),
            ("Time do Tocantins", "BR-TO", "TO"),
            ("Time de Goiás", "BR-GO", "GO"),
            ("Goiás", "BR-GO", "GO"),
            ("Time do MT", "BR-MT", "MT"),
            ("Mato Grosso", "BR-MT", "MT"),
            ("Time do MS", "BR-MS", "MS"),
            ("Mato Grosso do Sul", "BR-MS", "MS"),
        ]
        for nome, codigo, uf in casos:
            with self.subTest(nome=nome):
                self.assertEqual(iso_time(nome), codigo)
                self.assertEqual(sigla_time(nome), uf)

    def test_para_nao_sobrescreve_panama(self):
        self.assertEqual(iso_time("Panamá"), "PA")
        self.assertEqual(iso_time("Time do Pará"), "BR-PA")


class TestGridCompletoEstados(unittest.TestCase):
    def test_todas_as_27_ufs(self):
        ufs = ufs_registradas()
        self.assertEqual(len(ufs), 27)
        self.assertEqual(len(times_estados()), 27)
        self.assertEqual(
            ufs,
            {
                "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
                "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
                "RS", "RO", "RR", "SC", "SP", "SE", "TO",
            },
        )

    def test_todos_codigos_com_prefixo_br(self):
        for nome in times_estados():
            with self.subTest(nome=nome):
                codigo = iso_time(nome)
                self.assertIsNotNone(codigo)
                self.assertTrue(codigo.startswith("BR-"))
                self.assertEqual(len(codigo), 5)


if __name__ == "__main__":
    unittest.main()
