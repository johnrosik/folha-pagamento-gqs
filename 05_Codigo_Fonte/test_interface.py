"""Testes das regras da interface NiceGUI (validação, formatação e resumo).

As telas em si são montadas pelo NiceGUI; aqui testamos as funções puras que elas usam.
"""
import tempfile
import unittest
from pathlib import Path

import interface
from folhadepagamento import ColaboradorComissionado, ColaboradorPadrao, ColaboradorProducao, SistemaFolha, ValidacaoError


class TestRegrasDaInterface(unittest.TestCase):
    def setUp(self):
        self.diretorio = tempfile.TemporaryDirectory()
        self.original = interface.sistema
        interface.sistema = SistemaFolha(str(Path(self.diretorio.name) / "financy.db"))

    def tearDown(self):
        interface.sistema = self.original
        self.diretorio.cleanup()

    def test_formata_moeda_brasileira(self):
        self.assertEqual(interface.brl(5411.25), "R$ 5.411,25")
        self.assertEqual(interface.brl(0), "R$ 0,00")
        self.assertEqual(interface.brl(None), "R$ 0,00")
        self.assertEqual(interface.brl(1234567.891), "R$ 1.234.567,89")

    def test_matricula_obrigatoria_e_unica(self):
        interface.sistema.cadastrar(ColaboradorPadrao("P01", "Paula", 3000))

        self.assertEqual(interface.validar_matricula("   "), "Matrícula é obrigatória")
        self.assertIn("RN001", interface.validar_matricula("P01"))
        self.assertIn("RN001", interface.validar_matricula("  P01 "))
        self.assertIsNone(interface.validar_matricula("P02"))
        self.assertIsNone(interface.validar_matricula("P01", editando="P01"))

    def test_nome_obrigatorio(self):
        self.assertIn("RN002", interface.validar_nome("   "))
        self.assertIn("RN002", interface.validar_nome(None))
        self.assertIsNone(interface.validar_nome("Ana"))

    def test_numero_obrigatorio_e_nao_negativo(self):
        self.assertEqual(interface.validar_nao_negativo(None, "RN003", "Salário base"), "Salário base é obrigatório")
        self.assertIn("RN006", interface.validar_nao_negativo(-1, "RN006", "Quantidade produzida"))
        self.assertIsNone(interface.validar_nao_negativo(0, "RN003", "Salário base"))

    def test_monta_os_tres_tipos_com_os_valores_da_ers(self):
        padrao = interface.montar_colaborador({"tipo": "Padrao", "matricula": " P01 ", "nome": "Paula", "salario_base": 3000})
        comissionado = interface.montar_colaborador({"tipo": "Comissionado", "matricula": "C01", "nome": "Caio",
                                                     "salario_base": 2000, "vendas": 10000, "comissao_pct": 5})
        producao = interface.montar_colaborador({"tipo": "Producao", "matricula": "R01", "nome": "Rita",
                                                 "salario_base": 1500, "qtd_produzida": 500, "valor_unidade": 10})

        self.assertIsInstance(padrao, ColaboradorPadrao)
        self.assertEqual(padrao.matricula, "P01")
        self.assertAlmostEqual(padrao.calcular_salario_liquido(), 2497.50)
        self.assertIsInstance(comissionado, ColaboradorComissionado)
        self.assertAlmostEqual(comissionado.calcular_salario_liquido(), 2250)
        self.assertIsInstance(producao, ColaboradorProducao)
        self.assertAlmostEqual(producao.calcular_salario_liquido(), 5411.25)

    def test_montar_respeita_as_regras_do_dominio(self):
        with self.assertRaises(ValidacaoError):
            interface.montar_colaborador({"tipo": "Producao", "matricula": "R9", "nome": "Rui",
                                          "salario_base": -1, "qtd_produzida": 1, "valor_unidade": 1})

    def test_resumo_da_folha_por_tipo(self):
        for c in (ColaboradorPadrao("P01", "Paula", 3000), ColaboradorComissionado("C01", "Caio", 2000, 10000, 5),
                  ColaboradorProducao("R01", "Rita", 1500, 500, 10)):
            interface.sistema.cadastrar(c)

        r = interface.resumo_da_folha()

        self.assertEqual(r["quantidade"], 3)
        self.assertAlmostEqual(r["bruto"], 12000)
        self.assertAlmostEqual(r["inss"], 1200)
        self.assertAlmostEqual(r["irrf"], 641.25)
        self.assertAlmostEqual(r["liquido"], 10158.75)
        self.assertEqual(r["por_tipo"]["Producao"]["quantidade"], 1)
        self.assertAlmostEqual(r["por_tipo"]["Producao"]["liquido"], 5411.25)

    def test_total_e_a_soma_das_linhas_em_centavos(self):
        # Líquido de cada um é R$ 4.070,925: cada holerite paga R$ 4.070,93, então a folha soma R$ 8.141,86
        # (somar sem arredondar daria R$ 8.141,85, um centavo diferente da soma das linhas na tela).
        for matricula in ("R1", "R2"):
            interface.sistema.cadastrar(ColaboradorProducao(matricula, "Diego", 1200, 820, 4.5))

        linhas = [interface.linha_da_tabela(c) for c in interface.sistema.colaboradores.values()]
        r = interface.resumo_da_folha()

        self.assertEqual(linhas[0]["liquido"], 4070.93)
        self.assertEqual(linhas[0]["irrf"], 330.08)
        self.assertEqual(r["liquido"], 8141.86)
        self.assertEqual(interface.brl(r["liquido"]), "R$ 8.141,86")

    def test_linha_da_tabela_traz_tipo_e_valores(self):
        linha = interface.linha_da_tabela(ColaboradorProducao("R01", "Rita", 1500, 500, 10))

        self.assertEqual(linha["tipo"], "Producao")
        self.assertEqual(linha["tipo_nome"], "Produção")
        self.assertAlmostEqual(linha["bruto"], 6500)


if __name__ == "__main__":
    unittest.main()
