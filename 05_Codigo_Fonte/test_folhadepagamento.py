import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from folhadepagamento import (
    ColaboradorComissionado,
    ColaboradorPadrao,
    ColaboradorProducao,
    SistemaFolha,
    ValidacaoError,
    ler_float,
    ler_int,
    menu,
)


class TestColaboradores(unittest.TestCase):
    def test_colaborador_padrao_calcula_salario_e_descontos(self):
        colaborador = ColaboradorPadrao("  001  ", "  Ana  ", 2600)

        self.assertEqual(colaborador.matricula, "001")
        self.assertEqual(colaborador.nome, "Ana")
        self.assertEqual(colaborador.calcular_salario_bruto(), 2600)
        self.assertAlmostEqual(colaborador.calcular_inss(), 260)
        self.assertAlmostEqual(colaborador.calcular_irrf(), 175.5)
        self.assertAlmostEqual(colaborador.calcular_salario_liquido(), 2164.5)

    def test_nao_calcula_irrf_abaixo_do_limite(self):
        colaborador = ColaboradorPadrao("002", "Bruno", 2500)

        self.assertEqual(colaborador.calcular_irrf(), 0)
        self.assertAlmostEqual(colaborador.calcular_salario_liquido(), 2250)

    def test_colaborador_comissionado_calcula_salario_bruto(self):
        colaborador = ColaboradorComissionado("003", "Caio", 2000, 10000, 5)

        self.assertEqual(colaborador.calcular_salario_bruto(), 2500)

    def test_colaborador_producao_calcula_salario_bruto(self):
        colaborador = ColaboradorProducao("004", "Dora", 120, 15)

        self.assertEqual(colaborador.calcular_salario_bruto(), 1800)

    def test_nome_vazio_e_rejeitado(self):
        with self.assertRaises(ValidacaoError):
            ColaboradorPadrao("005", "   ", 1000)

    def test_valores_negativos_sao_rejeitados(self):
        casos = (
            lambda: ColaboradorPadrao("006", "Eva", -1),
            lambda: ColaboradorComissionado("007", "Fábio", -1, 0, 0),
            lambda: ColaboradorComissionado("008", "Gabi", 0, -1, 0),
            lambda: ColaboradorComissionado("009", "Hugo", 0, 0, -1),
            lambda: ColaboradorProducao("010", "Iara", -1, 0),
            lambda: ColaboradorProducao("011", "João", 0, -1),
        )

        for criar_colaborador in casos:
            with self.subTest(criar_colaborador=criar_colaborador):
                with self.assertRaises(ValidacaoError):
                    criar_colaborador()


class TestSistemaFolha(unittest.TestCase):
    def setUp(self):
        self.diretorio_temporario = tempfile.TemporaryDirectory()
        self.arquivo_db = Path(self.diretorio_temporario.name) / "colaboradores.json"
        self.sistema = SistemaFolha(str(self.arquivo_db))

    def tearDown(self):
        self.diretorio_temporario.cleanup()

    def test_cadastra_consulta_e_impede_matricula_duplicada(self):
        colaborador = ColaboradorPadrao("001", "Ana", 2000)
        self.sistema.cadastrar(colaborador)

        self.assertIs(self.sistema.consultar("001"), colaborador)
        with self.assertRaises(ValidacaoError):
            self.sistema.cadastrar(ColaboradorPadrao("001", "Outra pessoa", 1800))
        self.assertIsNone(self.sistema.consultar("999"))

    def test_exclui_colaborador_e_rejeita_matricula_inexistente(self):
        self.sistema.cadastrar(ColaboradorPadrao("001", "Ana", 2000))

        self.sistema.excluir("001")
        self.assertIsNone(self.sistema.consultar("001"))
        with self.assertRaises(ValidacaoError):
            self.sistema.excluir("999")

    def test_salva_e_recarrega_todos_os_tipos_de_colaborador(self):
        colaboradores = (
            ColaboradorPadrao("001", "Ana", 2000),
            ColaboradorComissionado("002", "Beto", 1500, 5000, 4),
            ColaboradorProducao("003", "Cris", 100, 12),
        )
        for colaborador in colaboradores:
            self.sistema.cadastrar(colaborador)

        sistema_recarregado = SistemaFolha(str(self.arquivo_db))

        self.assertEqual(len(sistema_recarregado.colaboradores), 3)
        self.assertIsInstance(sistema_recarregado.consultar("001"), ColaboradorPadrao)
        self.assertIsInstance(sistema_recarregado.consultar("002"), ColaboradorComissionado)
        self.assertIsInstance(sistema_recarregado.consultar("003"), ColaboradorProducao)

    def test_relatorio_individual_contem_salario_e_identificacao(self):
        self.sistema.cadastrar(ColaboradorPadrao("001", "Ana", 2600))
        saida = io.StringIO()

        with contextlib.redirect_stdout(saida):
            self.sistema.gerar_folha_individual("001")

        relatorio = saida.getvalue()
        self.assertIn("Matrícula: 001", relatorio)
        self.assertIn("Nome     : Ana", relatorio)
        self.assertIn("R$      2600.00", relatorio)
        self.assertIn("R$      2164.50", relatorio)

    def test_resumo_indica_total_de_colaboradores(self):
        self.sistema.cadastrar(ColaboradorPadrao("001", "Ana", 2000))
        self.sistema.cadastrar(ColaboradorProducao("002", "Beto", 100, 10))
        saida = io.StringIO()

        with contextlib.redirect_stdout(saida):
            self.sistema.emitir_resumo_folha()

        self.assertIn("TOTAL GERAL DE COLABORADORES: 2", saida.getvalue())

    def test_relatorios_informam_quando_nao_ha_colaborador(self):
        saida = io.StringIO()

        with contextlib.redirect_stdout(saida):
            self.sistema.gerar_folha_individual("999")
            self.sistema.emitir_resumo_folha()

        self.assertIn("[ERRO] Colaborador não encontrado.", saida.getvalue())
        self.assertIn("Nenhum colaborador cadastrado", saida.getvalue())

    def test_arquivo_json_invalido_exibe_aviso(self):
        self.arquivo_db.write_text("{", encoding="utf-8")
        saida = io.StringIO()

        with contextlib.redirect_stdout(saida):
            sistema = SistemaFolha(str(self.arquivo_db))

        self.assertEqual(sistema.colaboradores, {})
        self.assertIn("[AVISO] Não foi possível carregar", saida.getvalue())


class TestMenu(unittest.TestCase):
    def test_menu_executa_opcoes_e_trata_opcao_invalida(self):
        with tempfile.TemporaryDirectory() as diretorio:
            sistema = SistemaFolha(str(Path(diretorio) / "colaboradores.json"))
            entradas = (
                "1", "CLI-1", "Alice", "1000",
                "2", "CLI-2", "Bruno", "1500", "5000", "10",
                "3", "CLI-3", "Carla", "100", "12",
                "4", "CLI-1",
                "4", "NAO-EXISTE",
                "5", "CLI-1",
                "5", "NAO-EXISTE",
                "6",
                "7", "CLI-2",
                "7", "NAO-EXISTE",
                "9",
                "0",
            )
            saida = io.StringIO()

            with (
                patch("folhadepagamento.SistemaFolha", return_value=sistema),
                patch("builtins.input", side_effect=entradas),
                contextlib.redirect_stdout(saida),
            ):
                menu()

            texto = saida.getvalue()
            self.assertIn("[SUCESSO] Colaborador Padrão cadastrado!", texto)
            self.assertIn("[SUCESSO] Colaborador Comissionado cadastrado!", texto)
            self.assertIn("[SUCESSO] Colaborador por Produção cadastrado!", texto)
            self.assertIn("[ENCONTRADO] Nome: Alice", texto)
            self.assertIn("[FALHA DE VALIDAÇÃO]", texto)
            self.assertIn("Opção inválida!", texto)
            self.assertIn("Saindo do sistema.", texto)


class TestLeituraDeEntradas(unittest.TestCase):
    def test_ler_float_tenta_novamente_apos_entrada_invalida(self):
        with patch("builtins.input", side_effect=("inválido", "12.5")):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(ler_float("Valor: "), 12.5)

    def test_ler_int_tenta_novamente_apos_entrada_invalida(self):
        with patch("builtins.input", side_effect=("1.5", "12")):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(ler_int("Quantidade: "), 12)


if __name__ == "__main__":
    unittest.main()
