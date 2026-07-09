import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.validar_palpites_participantes import (
    _extrair_thdfm,
    carregar_palpites_diretorio,
    validar_palpites,
)
from src.data_paths import DATA_DIR

EXPORT = DATA_DIR / "fontes" / "Export CSV palpites bolao.csv"


class TestValidarPalpitesParticipantes(unittest.TestCase):
    def test_extrai_thdfm_xonha_j1(self) -> None:
        if not EXPORT.exists():
            self.skipTest("export ausente")
        palpites, _ = _extrair_thdfm(EXPORT)
        self.assertEqual(palpites[("xonha", 1)], (2, 0))

    def test_validacao_com_export_bate_baseline_grupos(self) -> None:
        if not EXPORT.exists():
            self.skipTest("export ausente")
        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / "palpites.csv"
            shutil.copy(EXPORT, destino)
            palpites, _, usados = carregar_palpites_diretorio(Path(tmp))
            self.assertEqual(len(usados), 1)
            self.assertGreater(len(palpites), 1000)


if __name__ == "__main__":
    unittest.main()
