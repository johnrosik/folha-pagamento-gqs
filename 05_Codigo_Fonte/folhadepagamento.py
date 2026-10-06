import json
import os
from abc import ABC, abstractmethod


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
        """Converte objeto em dicionário para persistência em JSON (RNF003)."""
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
    def __init__(self, matricula: str, nome: str, qtd_produzida: int, valor_unidade: float):
        super().__init__(matricula, nome)
        # RN006, RN007
        if qtd_produzida < 0:
            raise ValidacaoError("RN006: A quantidade produzida não pode ser negativa.")
        if valor_unidade < 0:
            raise ValidacaoError("RN007: O valor pago por unidade produzida não pode ser negativo.")

        self.qtd_produzida = qtd_produzida
        self.valor_unidade = valor_unidade

    def calcular_salario_bruto(self) -> float:
        return self.qtd_produzida * self.valor_unidade

    def to_dict(self) -> dict:
        return {
            "tipo": "Producao",
            "matricula": self.matricula,
            "nome": self.nome,
            "qtd_produzida": self.qtd_produzida,
            "valor_unidade": self.valor_unidade
        }


# ==========================================
# GERENCIADOR DA FOLHA E PERSISTÊNCIA (RNF003)
# ==========================================

class SistemaFolha:
    def __init__(self, arquivo_db="colaboradores.json"):
        self.arquivo_db = arquivo_db
        self.colaboradores: dict[str, Colaborador] = {}
        self.carregar_dados()

    def cadastrar(self, colab: Colaborador):
        """RF001 & RN001: Cadastro garantindo matrícula única."""
        if colab.matricula in self.colaboradores:
            raise ValidacaoError(f"RN001: Toda matrícula deverá ser única. A matrícula '{colab.matricula}' já existe.")
        self.colaboradores[colab.matricula] = colab
        self.salvar_dados()

    def excluir(self, matricula: str):
        """RF009: Manutenção de Cadastros (Remoção)."""
        if matricula not in self.colaboradores:
            raise ValidacaoError("Colaborador não encontrado.")
        del self.colaboradores[matricula]
        self.salvar_dados()

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

    def salvar_dados(self):
        """RNF003: Persistência de Dados em arquivo JSON."""
        dados = [c.to_dict() for c in self.colaboradores.values()]
        with open(self.arquivo_db, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

    def carregar_dados(self):
        """RNF003: Restauração automática dos dados."""
        if not os.path.exists(self.arquivo_db):
            return
        try:
            with open(self.arquivo_db, "r", encoding="utf-8") as f:
                dados = json.load(f)
                for item in dados:
                    tipo = item["tipo"]
                    if tipo == "Padrao":
                        c = ColaboradorPadrao(item["matricula"], item["nome"], item["salario_base"])
                    elif tipo == "Comissionado":
                        c = ColaboradorComissionado(item["matricula"], item["nome"], item["salario_base"], item["vendas"], item["comissao_pct"])
                    elif tipo == "Producao":
                        c = ColaboradorProducao(item["matricula"], item["nome"], item["qtd_produzida"], item["valor_unidade"])
                    self.colaboradores[c.matricula] = c
        except Exception:
            print("[AVISO] Não foi possível carregar os registros do arquivo de banco de dados.")


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
    sistema = SistemaFolha()

    while True:
        print("\n=== SISTEMA DE FOLHA DE PAGAMENTO ===")
        print("1. Cadastrar Colaborador Padrao (RF002)")
        print("2. Cadastrar Colaborador Comissionado (RF003)")
        print("3. Cadastrar Colaborador por Producao (RF004)")
        print("4. Consultar Colaborador (RF005)")
        print("5. Gerar Folha Individual (RF007)")
        print("6. Emitir Resumo Consolidado da Folha (RF008)")
        print("7. Excluir Colaborador (RF009)")
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
                qtd = ler_int("Quantidade Produzida: ")
                valor_u = ler_float("Valor por Unidade (R$): ")
                c = ColaboradorProducao(mat, nome, qtd, valor_u)
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

            elif opcao == "0":
                print("\nSaindo do sistema. Até logo!")
                break
            else:
                print("\nOpção inválida!")

        except ValidacaoError as ve:
            print(f"\n[FALHA DE VALIDAÇÃO] {ve}")


if __name__ == "__main__":
    menu()