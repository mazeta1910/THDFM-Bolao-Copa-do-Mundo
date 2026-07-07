import unittest

from src.participantes_avatars import carregar_mapa_arquivos, resolver_foto_participante


class TestParticipantesAvatars(unittest.TestCase):
    def test_resolve_jose_carlos_com_acento(self) -> None:
        mapa = carregar_mapa_arquivos()
        foto = resolver_foto_participante("José Carlos", mapa=mapa)
        self.assertIsNotNone(foto)
        self.assertEqual(foto.name, "Jose.png")

    def test_resolve_jose_carlos_sem_acento(self) -> None:
        mapa = carregar_mapa_arquivos()
        foto = resolver_foto_participante("Jose Carlos", mapa=mapa)
        self.assertIsNotNone(foto)
        self.assertEqual(foto.name, "Jose.png")


if __name__ == "__main__":
    unittest.main()
