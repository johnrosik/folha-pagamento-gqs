"""Testes de integração (artefato 12): API Flask + domínio + persistência em arquivo.

Cada teste usa um arquivo JSON temporário; o colaboradores.json real nunca é tocado.
Valores esperados vêm dos casos de teste da A1 (P01, C01, R01 e CT019).
"""
import tempfile
import unittest
from pathlib import Path

import app as aplicacao
from folhadepagamento import SistemaFolha

P01 = {"matricula": "P01", "nome": "Paula", "tipo": "Padrao", "salario_base": 3000}
C01 = {"matricula": "C01", "nome": "Caio", "tipo": "Comissionado", "salario_base": 2000, "vendas": 10000, "comissao_pct": 5}
R01 = {"matricula": "R01", "nome": "Rita", "tipo": "Producao", "salario_base": 1500, "qtd_produzida": 500, "valor_unidade": 10}


class TestApiFolha(unittest.TestCase):
    def setUp(self):
        self.diretorio = tempfile.TemporaryDirectory()
        self.arquivo = Path(self.diretorio.name) / "colaboradores.json"
        self.sistema_original = aplicacao.sistema
        aplicacao.sistema = SistemaFolha(str(self.arquivo))
        self.cliente = aplicacao.app.test_client()

    def tearDown(self):
        aplicacao.sistema = self.sistema_original
        self.diretorio.cleanup()

    def cadastrar(self, dados):
        return self.cliente.post("/api/colaboradores", json=dados)

    def test_pagina_inicial_e_servida(self):
        resposta = self.cliente.get("/")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"<html", resposta.data)

    def test_cadastro_dos_tres_tipos_calcula_a_folha(self):
        for dados in (P01, C01, R01):
            self.assertEqual(self.cadastrar(dados).status_code, 201)

        lista = {c["matricula"]: c for c in self.cliente.get("/api/colaboradores").get_json()}

        self.assertAlmostEqual(lista["P01"]["liquido"], 2497.50)
        self.assertAlmostEqual(lista["C01"]["bruto"], 2500)
        self.assertAlmostEqual(lista["C01"]["liquido"], 2250)
        self.assertAlmostEqual(lista["R01"]["bruto"], 6500)
        self.assertAlmostEqual(lista["R01"]["irrf"], 438.75)
        self.assertAlmostEqual(lista["R01"]["liquido"], 5411.25)

    def test_resumo_consolidado_bate_com_os_casos_de_teste(self):
        for dados in (P01, C01, R01):
            self.cadastrar(dados)

        lista = self.cliente.get("/api/colaboradores").get_json()

        self.assertAlmostEqual(sum(c["bruto"] for c in lista), 12000)
        self.assertAlmostEqual(sum(c["inss"] for c in lista), 1200)
        self.assertAlmostEqual(sum(c["irrf"] for c in lista), 641.25)
        self.assertAlmostEqual(sum(c["liquido"] for c in lista), 10158.75)

    def test_consulta_individual(self):
        self.cadastrar(R01)

        resposta = self.cliente.get("/api/colaboradores/R01")

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json()["salario_base"], 1500)
        self.assertEqual(self.cliente.get("/api/colaboradores/NAO").status_code, 404)

    def test_alteracao_recalcula_e_persiste(self):
        self.cadastrar(P01)

        resposta = self.cliente.put("/api/colaboradores/P01", json={**P01, "salario_base": 3500})

        self.assertEqual(resposta.status_code, 200)
        self.assertAlmostEqual(self.cliente.get("/api/colaboradores/P01").get_json()["liquido"], 2913.75)
        self.assertEqual(SistemaFolha(str(self.arquivo)).consultar("P01").calcular_salario_bruto(), 3500)

    def test_alteracao_ignora_matricula_do_corpo(self):
        self.cadastrar(P01)

        self.cliente.put("/api/colaboradores/P01", json={**P01, "matricula": "OUTRA", "salario_base": 3500})

        self.assertIsNone(aplicacao.sistema.consultar("OUTRA"))
        self.assertEqual(aplicacao.sistema.consultar("P01").calcular_salario_bruto(), 3500)

    def test_erros_de_validacao_respondem_400(self):
        self.cadastrar(P01)
        casos = (
            (P01, "RN001"),
            ({**P01, "matricula": "X1", "nome": "   "}, "RN002"),
            ({**P01, "matricula": "X2", "salario_base": -1}, "RN003"),
            ({**C01, "matricula": "X3", "vendas": -1}, "RN004"),
            ({**C01, "matricula": "X4", "comissao_pct": -1}, "RN005"),
            ({**R01, "matricula": "X5", "qtd_produzida": -1}, "RN006"),
            ({**R01, "matricula": "X6", "valor_unidade": -1}, "RN007"),
            ({**R01, "matricula": "X7", "salario_base": -1}, "RN003"),
        )
        for dados, regra in casos:
            with self.subTest(regra=regra):
                resposta = self.cadastrar(dados)
                self.assertEqual(resposta.status_code, 400)
                self.assertIn(regra, resposta.get_json()["erro"])

    def test_entradas_malformadas_respondem_400(self):
        self.assertEqual(self.cliente.post("/api/colaboradores", data="nao-e-json").status_code, 400)
        self.assertEqual(self.cadastrar({**P01, "tipo": "Estagiario"}).status_code, 400)
        self.assertEqual(self.cadastrar({**R01, "qtd_produzida": "abc"}).status_code, 400)
        self.assertEqual(self.cadastrar({"tipo": "Padrao"}).status_code, 400)
        self.cadastrar(P01)
        self.assertEqual(self.cliente.put("/api/colaboradores/P01", data="x").status_code, 400)
        self.assertEqual(self.cliente.put("/api/colaboradores/P01", json={**P01, "salario_base": "x"}).status_code, 400)
        self.assertEqual(self.cliente.put("/api/colaboradores/P01", json={**P01, "salario_base": -5}).status_code, 400)

    def test_alterar_e_excluir_inexistente_respondem_404(self):
        self.assertEqual(self.cliente.put("/api/colaboradores/NAO", json=P01).status_code, 404)
        self.assertEqual(self.cliente.delete("/api/colaboradores/NAO").status_code, 404)

    def test_exclusao_remove_e_persiste(self):
        self.cadastrar(P01)

        self.assertEqual(self.cliente.delete("/api/colaboradores/P01").status_code, 200)

        self.assertEqual(self.cliente.get("/api/colaboradores").get_json(), [])
        self.assertIsNone(SistemaFolha(str(self.arquivo)).consultar("P01"))


if __name__ == "__main__":
    unittest.main()
