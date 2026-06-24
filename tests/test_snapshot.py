import unittest

from src.snapshot import calcular_mudancas_posicao, calcular_variacoes, formatar_variacao
from src.models import ClassificacaoLinha


class TestSnapshot(unittest.TestCase):
    def test_formatar_variacao(self):
        self.assertEqual(formatar_variacao(6), "+6")
        self.assertEqual(formatar_variacao(0), "0")
        self.assertEqual(formatar_variacao(-2), "-2")
        self.assertEqual(formatar_variacao(None), "-")

    def test_calcular_mudancas_posicao(self):
        atual = [
            ClassificacaoLinha(2, "Ana", 3, 10, 2, 2, 50),
            ClassificacaoLinha(5, "Bob", 1, 8, 1, 1, 40),
        ]
        anterior = {"Ana": {"soma": 44, "posicao": 3}, "Bob": {"soma": 40, "posicao": 4}}
        mudancas = calcular_mudancas_posicao(atual, anterior)
        self.assertEqual(mudancas["Ana"], 1)
        self.assertEqual(mudancas["Bob"], -1)

    def test_formatar_mudanca_posicao(self):
        from src.snapshot import formatar_mudanca_posicao, formatar_posicao_com_mudanca

        self.assertEqual(formatar_mudanca_posicao(2), "↑2")
        self.assertEqual(formatar_mudanca_posicao(-3), "↓3")
        self.assertEqual(formatar_mudanca_posicao(0), "")
        self.assertEqual(formatar_posicao_com_mudanca(3, 2), "3 ↑2")

    def test_calcular_variacoes(self):
        atual = [
            ClassificacaoLinha(1, "Ana", 3, 10, 2, 2, 50),
            ClassificacaoLinha(2, "Bob", 1, 8, 1, 1, 40),
        ]
        anterior = {"Ana": {"soma": 44, "posicao": 1}, "Bob": {"soma": 40, "posicao": 2}}
        variacoes = calcular_variacoes(atual, anterior)
        self.assertEqual(variacoes["Ana"], 6)
        self.assertEqual(variacoes["Bob"], 0)


if __name__ == "__main__":
    unittest.main()
