import contextlib
import io
import sqlite3
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
        # CT R01 (ERS v1.1): salário base 1.500 + 500 unidades x R$ 10,00
        colaborador = ColaboradorProducao("004", "Dora", 1500, 500, 10)

        self.assertEqual(colaborador.calcular_salario_bruto(), 6500)
        self.assertAlmostEqual(colaborador.calcular_inss(), 650)
        self.assertAlmostEqual(colaborador.calcular_irrf(), 438.75)
        self.assertAlmostEqual(colaborador.calcular_salario_liquido(), 5411.25)

    def test_nome_vazio_e_rejeitado(self):
        with self.assertRaises(ValidacaoError):
            ColaboradorPadrao("005", "   ", 1000)

    def test_valores_negativos_sao_rejeitados(self):
        casos = (
            lambda: ColaboradorPadrao("006", "Eva", -1),
            lambda: ColaboradorComissionado("007", "Fábio", -1, 0, 0),
            lambda: ColaboradorComissionado("008", "Gabi", 0, -1, 0),
            lambda: ColaboradorComissionado("009", "Hugo", 0, 0, -1),
            lambda: ColaboradorProducao("010", "Iara", 0, -1, 0),
            lambda: ColaboradorProducao("011", "João", 0, 0, -1),
            lambda: ColaboradorProducao("012", "Kátia", -1, 0, 0),
        )

        for criar_colaborador in casos:
            with self.subTest(criar_colaborador=criar_colaborador):
                with self.assertRaises(ValidacaoError):
                    criar_colaborador()


class TestSistemaFolha(unittest.TestCase):
    def setUp(self):
        self.diretorio_temporario = tempfile.TemporaryDirectory()
        self.arquivo_db = Path(self.diretorio_temporario.name) / "financy.db"
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

    def test_altera_cadastro_e_recalcula_folha(self):
        # CT "P01 alterado": salário de 3.000 para 3.500
        self.sistema.cadastrar(ColaboradorPadrao("P01", "Paula", 3000))

        self.sistema.alterar(ColaboradorPadrao("P01", "Paula Souza", 3500))

        alterado = self.sistema.consultar("P01")
        self.assertEqual(alterado.nome, "Paula Souza")
        self.assertEqual(alterado.calcular_salario_bruto(), 3500)
        self.assertAlmostEqual(alterado.calcular_salario_liquido(), 2913.75)
        self.assertEqual(SistemaFolha(str(self.arquivo_db)).consultar("P01").calcular_salario_bruto(), 3500)

    def test_alterar_matricula_inexistente_e_rejeitado(self):
        with self.assertRaises(ValidacaoError):
            self.sistema.alterar(ColaboradorPadrao("999", "Ninguém", 1000))

    def test_migra_json_antigo_uma_vez_e_producao_sem_salario_base_vale_zero(self):
        arquivo_json = Path(self.diretorio_temporario.name) / "colaboradores.json"
        arquivo_json.write_text(
            '[{"tipo": "Padrao", "matricula": "P9", "nome": "Pia", "salario_base": 2000},'
            ' {"tipo": "Producao", "matricula": "R9", "nome": "Rui", "qtd_produzida": 10, "valor_unidade": 5}]',
            encoding="utf-8",
        )
        banco = Path(self.diretorio_temporario.name) / "migrado.db"

        sistema = SistemaFolha(str(banco), importar_json=str(arquivo_json))
        self.assertEqual(sistema.consultar("R9").calcular_salario_bruto(), 50)

        sistema.excluir("P9")
        reaberto = SistemaFolha(str(banco), importar_json=str(arquivo_json))
        self.assertEqual(list(reaberto.colaboradores), ["R9"])  # não reimporta por cima do banco

    def test_json_antigo_invalido_exibe_aviso_e_nao_importa(self):
        arquivo_json = Path(self.diretorio_temporario.name) / "colaboradores.json"
        arquivo_json.write_text("{", encoding="utf-8")
        saida = io.StringIO()

        with contextlib.redirect_stdout(saida):
            sistema = SistemaFolha(str(Path(self.diretorio_temporario.name) / "outro.db"), importar_json=str(arquivo_json))

        self.assertEqual(sistema.colaboradores, {})
        self.assertIn("[AVISO] Não foi possível importar", saida.getvalue())

    def test_banco_recusa_dado_invalido_gravado_por_fora_do_sistema(self):
        self.sistema.cadastrar(ColaboradorPadrao("001", "Ana", 2000))
        conexao = sqlite3.connect(self.arquivo_db)
        try:
            casos = (
                "INSERT INTO colaboradores (matricula, tipo, nome, salario_base) VALUES ('001', 'Padrao', 'Dup', 1)",
                "INSERT INTO colaboradores (matricula, tipo, nome, salario_base) VALUES ('X', 'Padrao', 'Neg', -1)",
                "INSERT INTO colaboradores (matricula, tipo, nome, salario_base) VALUES ('Y', 'Padrao', '  ', 1)",
                "INSERT INTO colaboradores (matricula, tipo, nome, salario_base) VALUES ('Z', 'Outro', 'Tipo', 1)",
            )
            for comando in casos:
                with self.subTest(comando=comando):
                    with self.assertRaises(sqlite3.IntegrityError):
                        conexao.execute(comando)
        finally:
            conexao.close()

    def test_alteracao_mantem_a_ordem_de_cadastro(self):
        for matricula in ("A", "B", "C"):
            self.sistema.cadastrar(ColaboradorPadrao(matricula, f"Pessoa {matricula}", 1000))
        self.sistema.alterar(ColaboradorComissionado("A", "Pessoa A", 1000, 100, 10))

        reaberto = SistemaFolha(str(self.arquivo_db))

        self.assertEqual(list(reaberto.colaboradores), ["A", "B", "C"])
        self.assertIsInstance(reaberto.consultar("A"), ColaboradorComissionado)

    def test_salva_e_recarrega_todos_os_tipos_de_colaborador(self):
        colaboradores = (
            ColaboradorPadrao("001", "Ana", 2000),
            ColaboradorComissionado("002", "Beto", 1500, 5000, 4),
            ColaboradorProducao("003", "Cris", 1000, 100, 12),
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
        self.sistema.cadastrar(ColaboradorProducao("002", "Beto", 1000, 100, 10))
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

    def test_banco_corrompido_exibe_aviso(self):
        self.arquivo_db.write_text("isto não é um banco SQLite" * 100, encoding="utf-8")
        saida = io.StringIO()

        with contextlib.redirect_stdout(saida):
            sistema = SistemaFolha(str(self.arquivo_db))

        self.assertEqual(sistema.colaboradores, {})
        self.assertIn("[AVISO] Não foi possível carregar", saida.getvalue())


class TestMenu(unittest.TestCase):
    def test_menu_executa_opcoes_e_trata_opcao_invalida(self):
        with tempfile.TemporaryDirectory() as diretorio:
            sistema = SistemaFolha(str(Path(diretorio) / "financy.db"))
            entradas = (
                "1", "CLI-1", "Alice", "1000",
                "2", "CLI-2", "Bruno", "1500", "5000", "10",
                "3", "CLI-3", "Carla", "1000", "100", "12",
                "4", "CLI-1",
                "4", "NAO-EXISTE",
                "5", "CLI-1",
                "5", "NAO-EXISTE",
                "6",
                "7", "CLI-2",
                "7", "NAO-EXISTE",
                "8", "CLI-1", "Alice Lima", "1200",
                "8", "CLI-3", "Carla", "1500", "100", "12",
                "8", "NAO-EXISTE",
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
            self.assertIn("[SUCESSO] Cadastro alterado!", texto)
            self.assertEqual(sistema.consultar("CLI-1").calcular_salario_bruto(), 1200)
            self.assertEqual(sistema.consultar("CLI-3").calcular_salario_bruto(), 2700)
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
