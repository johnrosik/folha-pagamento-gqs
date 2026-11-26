import json
import os
import sqlite3
from abc import ABC, abstractmethod
from contextlib import closing


# ==========================================
# EXCEÇÕES PERSONALIZADAS DE VALIDAÇÃO
# ==========================================

class ValidacaoError(Exception):
    """Exceção lançada quando dados de entrada violam as Regras de Negócio."""
    pass


# ==========================================
# MODELO DE DOMÍNIO (Open/Closed Principle - RNF004)
# ==========================================

class Colaborador(ABC):
    """Classe base abstrata para todos os tipos de colaborador."""

    def __init__(self, matricula: str, nome: str):
        # RN002: Nome é obrigatório
        if not nome or not nome.strip():
            raise ValidacaoError("RN002: O nome do colaborador é obrigatório.")

        self.matricula = matricula.strip()
        self.nome = nome.strip()

    @abstractmethod
    def calcular_salario_bruto(self) -> float:
        """RN008: Cálculo do salário final feito automaticamente."""
        pass

    def calcular_inss(self) -> float:
        """Cálculo simplificado do INSS para fins acadêmicos."""
        return self.calcular_salario_bruto() * 0.10

    def calcular_irrf(self) -> float:
        """Cálculo simplificado do IRRF para fins acadêmicos."""
        base = self.calcular_salario_bruto() - self.calcular_inss()
        return base * 0.075 if base > 2259.20 else 0.0

    def calcular_salario_liquido(self) -> float:
        """RN008: Retorna o salário líquido final."""
        return self.calcular_salario_bruto() - self.calcular_inss() - self.calcular_irrf()

    @abstractmethod
    def to_dict(self) -> dict:
        """Converte objeto em dicionário (persistência e API)."""
        pass


# RF002 – Cadastro de Colaborador Padrão (Mensalista)
class ColaboradorPadrao(Colaborador):
    def __init__(self, matricula: str, nome: str, salario_base: float):
        super().__init__(matricula, nome)
        # RN003: Salário base não pode ser negativo
        if salario_base < 0:
            raise ValidacaoError("RN003: O salário base não pode ser negativo.")
        self.salario_base = salario_base

    def calcular_salario_bruto(self) -> float:
        return self.salario_base

    def to_dict(self) -> dict:
        return {
            "tipo": "Padrao",
            "matricula": self.matricula,
            "nome": self.nome,
            "salario_base": self.salario_base
        }


# RF003 – Cadastro de Colaborador Comissionado
class ColaboradorComissionado(Colaborador):
    def __init__(self, matricula: str, nome: str, salario_base: float, vendas: float, comissao_pct: float):
        super().__init__(matricula, nome)
        # RN003, RN004, RN005
        if salario_base < 0:
            raise ValidacaoError("RN003: O salário base não pode ser negativo.")
        if vendas < 0:
            raise ValidacaoError("RN004: O valor de vendas não pode ser negativo.")
        if comissao_pct < 0:
            raise ValidacaoError("RN005: O percentual de comissão não pode ser negativo.")

        self.salario_base = salario_base
        self.vendas = vendas
        self.comissao_pct = comissao_pct

    def calcular_salario_bruto(self) -> float:
        return self.salario_base + (self.vendas * (self.comissao_pct / 100.0))

    def to_dict(self) -> dict:
        return {
            "tipo": "Comissionado",
            "matricula": self.matricula,
            "nome": self.nome,
            "salario_base": self.salario_base,
            "vendas": self.vendas,
            "comissao_pct": self.comissao_pct
        }


# RF004 – Cadastro de Colaborador por Produção
class ColaboradorProducao(Colaborador):
    def __init__(self, matricula: str, nome: str, salario_base: float, qtd_produzida: int, valor_unidade: float):
        super().__init__(matricula, nome)
        # RN003, RN006, RN007
        if salario_base < 0:
            raise ValidacaoError("RN003: O salário base não pode ser negativo.")
        if qtd_produzida < 0:
            raise ValidacaoError("RN006: A quantidade produzida não pode ser negativa.")
        if valor_unidade < 0:
            raise ValidacaoError("RN007: O valor pago por unidade produzida não pode ser negativo.")

        self.salario_base = salario_base
        self.qtd_produzida = qtd_produzida
        self.valor_unidade = valor_unidade

    def calcular_salario_bruto(self) -> float:
        # ERS v1.1: salário base + quantidade produzida × valor por unidade
        return self.salario_base + (self.qtd_produzida * self.valor_unidade)

    def to_dict(self) -> dict:
        return {
            "tipo": "Producao",
            "matricula": self.matricula,
            "nome": self.nome,
            "salario_base": self.salario_base,
            "qtd_produzida": self.qtd_produzida,
            "valor_unidade": self.valor_unidade
        }


def colaborador_de_registro(item) -> Colaborador:
    """Recria o colaborador a partir de um registro (linha do SQLite ou item do JSON antigo)."""
    tipo = item["tipo"]
    if tipo == "Padrao":
        return ColaboradorPadrao(item["matricula"], item["nome"], item["salario_base"])
    if tipo == "Comissionado":
        return ColaboradorComissionado(item["matricula"], item["nome"], item["salario_base"], item["vendas"], item["comissao_pct"])
    if tipo == "Producao":
        # Registros gravados antes da correção D01 não têm salário base: valem 0.
        salario_base = item["salario_base"] if "salario_base" in item.keys() else 0
        return ColaboradorProducao(item["matricula"], item["nome"], salario_base or 0, item["qtd_produzida"], item["valor_unidade"])
    raise ValidacaoError(f"Tipo de colaborador desconhecido: {tipo}")


# ==========================================
# GERENCIADOR DA FOLHA E PERSISTÊNCIA EM SQLITE (RNF003)
# ==========================================

# As restrições repetem as regras de negócio no próprio banco: mesmo um INSERT feito
# fora do sistema não grava matrícula repetida, nome vazio nem valor negativo.
ESQUEMA = """
CREATE TABLE IF NOT EXISTS colaboradores (
    matricula     TEXT PRIMARY KEY,
    tipo          TEXT NOT NULL CHECK (tipo IN ('Padrao', 'Comissionado', 'Producao')),
    nome          TEXT NOT NULL CHECK (length(trim(nome)) > 0),
    salario_base  REAL NOT NULL DEFAULT 0 CHECK (salario_base >= 0),
    vendas        REAL CHECK (vendas >= 0),
    comissao_pct  REAL CHECK (comissao_pct >= 0),
    qtd_produzida INTEGER CHECK (qtd_produzida >= 0),
    valor_unidade REAL CHECK (valor_unidade >= 0)
)
"""

PASTA = os.path.dirname(os.path.abspath(__file__))
BANCO_PADRAO = os.path.join(PASTA, "financy.db")
JSON_ANTIGO = os.path.join(PASTA, "colaboradores.json")

COLUNAS = ("matricula", "tipo", "nome", "salario_base", "vendas", "comissao_pct", "qtd_produzida", "valor_unidade")


class SistemaFolha:
    def __init__(self, arquivo_db="financy.db", importar_json=None):
        self.arquivo_db = arquivo_db
        self.colaboradores: dict[str, Colaborador] = {}
        self.carregar_dados()
        if importar_json and not self.colaboradores:
            self.importar_json(importar_json)

    def _conectar(self):
        conexao = sqlite3.connect(self.arquivo_db)
        conexao.row_factory = sqlite3.Row
        return closing(conexao)

    @staticmethod
    def _valores(colab: Colaborador) -> tuple:
        dados = colab.to_dict()
        return tuple(dados.get(coluna) for coluna in COLUNAS)

    def cadastrar(self, colab: Colaborador):
        """RF001 & RN001: Cadastro garantindo matrícula única."""
        mensagem = f"RN001: Toda matrícula deverá ser única. A matrícula '{colab.matricula}' já existe."
        if colab.matricula in self.colaboradores:
            raise ValidacaoError(mensagem)
        try:
            with self._conectar() as conexao, conexao:
                conexao.execute(
                    f"INSERT INTO colaboradores ({', '.join(COLUNAS)}) VALUES ({', '.join('?' * len(COLUNAS))})",
                    self._valores(colab),
                )
        except sqlite3.IntegrityError as erro:
            raise ValidacaoError(mensagem) from erro
        self.colaboradores[colab.matricula] = colab

    def excluir(self, matricula: str):
        """RF009: Manutenção de Cadastros (Remoção)."""
        if matricula not in self.colaboradores:
            raise ValidacaoError("Colaborador não encontrado.")
        with self._conectar() as conexao, conexao:
            conexao.execute("DELETE FROM colaboradores WHERE matricula = ?", (matricula,))
        del self.colaboradores[matricula]

    def alterar(self, colab: Colaborador):
        """RF009: Manutenção de Cadastros (Alteração). A matrícula identifica o registro e não muda."""
        if colab.matricula not in self.colaboradores:
            raise ValidacaoError("Colaborador não encontrado.")
        campos = COLUNAS[1:]
        with self._conectar() as conexao, conexao:
            conexao.execute(
                f"UPDATE colaboradores SET {', '.join(f'{c} = ?' for c in campos)} WHERE matricula = ?",
                self._valores(colab)[1:] + (colab.matricula,),
            )
        self.colaboradores[colab.matricula] = colab

    def consultar(self, matricula: str) -> Colaborador:
        """RF005: Consulta de Colaboradores."""
        return self.colaboradores.get(matricula)

    def gerar_folha_individual(self, matricula: str):
        """RF006, RF007: Relatório de Folha de Pagamento Individual."""
        c = self.consultar(matricula)
        if not c:
            print("\n[ERRO] Colaborador não encontrado.")
            return

        bruto = c.calcular_salario_bruto()
        inss = c.calcular_inss()
        irrf = c.calcular_irrf()
        liquido = c.calcular_salario_liquido()

        print("\n" + "=" * 50)
        print("         RELATÓRIO DE FOLHA DE PAGAMENTO INDIVIDUAL")
        print("=" * 50)
        print(f"Matrícula: {c.matricula}")
        print(f"Nome     : {c.nome}")
        print(f"Categoria: {c.__class__.__name__.replace('Colaborador', '')}")
        print("-" * 50)
        print(f"(+) Salário Bruto:   R$ {bruto:12.2f}")
        print(f"(-) Desconto INSS:   R$ {inss:12.2f}")
        print(f"(-) Desconto IRRF:   R$ {irrf:12.2f}")
        print("-" * 50)
        print(f"(=) Salário Líquido: R$ {liquido:12.2f}")
        print("=" * 50)

    def emitir_resumo_folha(self):
        """RF008: Relatório Resumido / Consolidado da Folha de Pagamento."""
        if not self.colaboradores:
            print("\nNenhum colaborador cadastrado para gerar resumo.")
            return

        tot_bruto = tot_inss = tot_irrf = tot_liquido = 0.0

        print("\n" + "#" * 65)
        print("          RELATÓRIO RESUMIDO E CONSOLIDADO DA FOLHA")
        print("#" * 65)
        print(f"{'MATRÍCULA':<10} | {'NOME':<20} | {'BRUTO (R$)':<12} | {'LÍQUIDO (R$)':<12}")
        print("-" * 65)

        for c in self.colaboradores.values():
            b = c.calcular_salario_bruto()
            i = c.calcular_inss()
            ir = c.calcular_irrf()
            l = c.calcular_salario_liquido()

            tot_bruto += b
            tot_inss += i
            tot_irrf += ir
            tot_liquido += l

            print(f"{c.matricula:<10} | {c.nome:<20.20} | {b:12.2f} | {l:12.2f}")

        print("-" * 65)
        print(f"TOTAL GERAL DE COLABORADORES: {len(self.colaboradores)}")
        print(f"TOTAL SALÁRIOS BRUTOS:        R$ {tot_bruto:14.2f}")
        print(f"TOTAL INSS RETIDO:            R$ {tot_inss:14.2f}")
        print(f"TOTAL IRRF RETIDO:            R$ {tot_irrf:14.2f}")
        print(f"TOTAL GERAL DA FOLHA (LÍQ):   R$ {tot_liquido:14.2f}")
        print("#" * 65)

    def carregar_dados(self):
        """RNF003: Cria a tabela na primeira execução e restaura os dados gravados."""
        try:
            with self._conectar() as conexao, conexao:
                conexao.execute(ESQUEMA)
                linhas = conexao.execute("SELECT * FROM colaboradores ORDER BY rowid").fetchall()
            for linha in linhas:
                c = colaborador_de_registro(linha)
                self.colaboradores[c.matricula] = c
        except (sqlite3.DatabaseError, ValidacaoError):
            print("[AVISO] Não foi possível carregar os registros do arquivo de banco de dados.")

    def importar_json(self, arquivo_json):
        """Migra uma única vez os dados da versão anterior (colaboradores.json) para o SQLite."""
        if not os.path.exists(arquivo_json):
            return 0
        try:
            with open(arquivo_json, "r", encoding="utf-8") as f:
                registros = [colaborador_de_registro(item) for item in json.load(f)]
        except (OSError, ValueError, KeyError, TypeError, ValidacaoError):
            print("[AVISO] Não foi possível importar o arquivo JSON da versão anterior.")
            return 0
        for colab in registros:
            if colab.matricula not in self.colaboradores:
                self.cadastrar(colab)
        return len(registros)


# ==========================================
# INTERFACE CLI / MENU INTERATIVO (RNF001)
# ==========================================

def ler_float(mensagem: str) -> float:
    """Valida entrada numérica para evitar falhas no sistema (RNF002)."""
    while True:
        try:
            return float(input(mensagem))
        except ValueError:
            print("[ERRO] Digite um valor numérico válido.")

def ler_int(mensagem: str) -> int:
    while True:
        try:
            return int(input(mensagem))
        except ValueError: 
            print("[ERRO] Digite um número inteiro válido.")

def menu():
    sistema = SistemaFolha(BANCO_PADRAO, importar_json=JSON_ANTIGO)

    while True:
        print("\n=== SISTEMA DE FOLHA DE PAGAMENTO ===")
        print("1. Cadastrar Colaborador Padrao (RF002)")
        print("2. Cadastrar Colaborador Comissionado (RF003)")
        print("3. Cadastrar Colaborador por Producao (RF004)")
        print("4. Consultar Colaborador (RF005)")
        print("5. Gerar Folha Individual (RF007)")
        print("6. Emitir Resumo Consolidado da Folha (RF008)")
        print("7. Excluir Colaborador (RF009)")
        print("8. Alterar Colaborador (RF009)")
        print("0. Sair")

        opcao = input("Escolha uma opcao: ").strip()

        try:
            if opcao == "1":
                mat = input("Matrícula: ")
                nome = input("Nome: ")
                sal_base = ler_float("Salário Base (R$): ")
                c = ColaboradorPadrao(mat, nome, sal_base)
                sistema.cadastrar(c)
                print("[SUCESSO] Colaborador Padrão cadastrado!")

            elif opcao == "2":
                mat = input("Matrícula: ")
                nome = input("Nome: ")
                sal_base = ler_float("Salário Base (R$): ")
                vendas = ler_float("Total de Vendas (R$): ")
                comissao = ler_float("Percentual de Comissão (%): ")
                c = ColaboradorComissionado(mat, nome, sal_base, vendas, comissao)
                sistema.cadastrar(c)
                print("[SUCESSO] Colaborador Comissionado cadastrado!")

            elif opcao == "3":
                mat = input("Matrícula: ")
                nome = input("Nome: ")
                sal_base = ler_float("Salário Base (R$): ")
                qtd = ler_int("Quantidade Produzida: ")
                valor_u = ler_float("Valor por Unidade (R$): ")
                c = ColaboradorProducao(mat, nome, sal_base, qtd, valor_u)
                sistema.cadastrar(c)
                print("[SUCESSO] Colaborador por Produção cadastrado!")

            elif opcao == "4":
                mat = input("Digite a matrícula para consulta: ")
                c = sistema.consultar(mat)
                if c:
                    print(f"\n[ENCONTRADO] Nome: {c.nome} | Tipo: {c.__class__.__name__} | Bruto: R$ {c.calcular_salario_bruto():.2f}")
                else:
                    print("\n[ERRO] Colaborador não encontrado.")

            elif opcao == "5":
                mat = input("Digite a matrícula do colaborador: ")
                sistema.gerar_folha_individual(mat)

            elif opcao == "6":
                sistema.emitir_resumo_folha()

            elif opcao == "7":
                mat = input("Digite a matrícula a remover: ")
                sistema.excluir(mat)
                print("[SUCESSO] Registro removido.")

            elif opcao == "8":
                mat = input("Digite a matrícula a alterar: ").strip()
                atual = sistema.consultar(mat)
                if not atual:
                    print("\n[ERRO] Colaborador não encontrado.")
                    continue
                print(f"Alterando {atual.nome} ({atual.to_dict()['tipo']}). Informe os novos dados.")
                nome = input("Nome: ")
                if isinstance(atual, ColaboradorComissionado):
                    novo = ColaboradorComissionado(mat, nome, ler_float("Salário Base (R$): "),
                                                   ler_float("Total de Vendas (R$): "),
                                                   ler_float("Percentual de Comissão (%): "))
                elif isinstance(atual, ColaboradorProducao):
                    novo = ColaboradorProducao(mat, nome, ler_float("Salário Base (R$): "),
                                               ler_int("Quantidade Produzida: "),
                                               ler_float("Valor por Unidade (R$): "))
                else:
                    novo = ColaboradorPadrao(mat, nome, ler_float("Salário Base (R$): "))
                sistema.alterar(novo)
                print("[SUCESSO] Cadastro alterado!")

            elif opcao == "0":
                print("\nSaindo do sistema. Até logo!")
                break
            else:
                print("\nOpção inválida!")

        except ValidacaoError as ve:
            print(f"\n[FALHA DE VALIDAÇÃO] {ve}")


if __name__ == "__main__":
    menu()