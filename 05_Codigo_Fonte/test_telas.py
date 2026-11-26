"""Testes das telas NiceGUI com o usuário simulado (navegar, digitar, clicar, ver).

Rodam com pytest; os dados vêm de um arquivo temporário (conftest.py).
"""
import json

from nicegui import ui
from nicegui.testing import User


async def test_lista_mostra_colaboradores_e_valores(user: User):
    await user.open("/")
    await user.should_see(marker="busca")
    tabela = user.find(ui.table).elements.pop()
    linhas = {linha["matricula"]: linha for linha in tabela.rows}
    assert linhas["P01"]["liquido"] == 2497.5
    assert linhas["C01"]["liquido"] == 2250


async def test_menu_lateral_navega_entre_as_telas(user: User):
    await user.open("/")
    user.find(marker="menu-Resumo da folha").click()
    await user.should_see("Total líquido")
    user.find(marker="menu-Folha individual").click()
    await user.should_see("Escolha um colaborador para ver a folha.")
    user.find(marker="menu-Novo colaborador").click()
    await user.should_see("Prévia da folha")


async def test_cadastro_vazio_marca_todos_os_campos_obrigatorios(user: User):
    await user.open("/novo")
    user.find(marker="salvar").click()
    await user.should_see("Corrija os campos marcados em vermelho")
    assert user.find(marker="matricula").elements.pop().error == "Matrícula é obrigatória"
    assert "RN002" in user.find(marker="nome").elements.pop().error
    assert user.find(marker="salario").elements.pop().error == "Salário base é obrigatório"


async def test_matricula_repetida_e_recusada_na_hora(user: User):
    await user.open("/novo")
    user.find(marker="matricula").type("P01")
    campo = user.find(marker="matricula").elements.pop()
    assert "RN001" in campo.error


async def test_cadastra_colaborador_por_producao(user: User, dados_temporarios):
    await user.open("/novo")
    user.find(marker="tipo").elements.pop().set_value("Producao")
    user.find(marker="matricula").type("R01")
    user.find(marker="nome").type("Rita Alves")
    user.find(marker="salario").elements.pop().set_value(1500)
    user.find(marker="quantidade").elements.pop().set_value(500)
    user.find(marker="unidade").elements.pop().set_value(10)
    await user.should_see("R$ 5.411,25")  # prévia calculada pelo domínio
    user.find(marker="salvar").click()
    await user.should_see("Colaborador cadastrado")
    gravados = {c["matricula"]: c for c in json.loads(dados_temporarios.read_text(encoding="utf-8"))}
    assert gravados["R01"]["salario_base"] == 1500


async def test_valor_negativo_e_recusado(user: User):
    await user.open("/novo")
    user.find(marker="matricula").type("X1")
    user.find(marker="nome").type("Xavier")
    user.find(marker="salario").elements.pop().set_value(-10)
    user.find(marker="salvar").click()
    await user.should_see("Corrija os campos marcados em vermelho")
    assert "RN003" in user.find(marker="salario").elements.pop().error


async def test_altera_cadastro(user: User, dados_temporarios):
    await user.open("/editar/P01")
    await user.should_see("Salvar alteração")
    assert user.find(marker="matricula").elements.pop().value == "P01"
    user.find(marker="salario").elements.pop().set_value(3500)
    await user.should_see("R$ 2.913,75")
    user.find(marker="salvar").click()
    await user.should_see("Cadastro alterado")
    gravados = {c["matricula"]: c for c in json.loads(dados_temporarios.read_text(encoding="utf-8"))}
    assert gravados["P01"]["salario_base"] == 3500


async def test_editar_matricula_inexistente(user: User):
    await user.open("/editar/NAO")
    await user.should_see("Colaborador não encontrado.")


async def test_folha_individual(user: User):
    await user.open("/folha?matricula=P01")
    await user.should_see("(=) Salário líquido")
    await user.should_see("R$ 2.497,50")
    user.find(marker="escolha").elements.pop().set_value("C01")
    await user.should_see("R$ 2.250,00")


async def test_resumo_da_folha(user: User):
    await user.open("/resumo")
    await user.should_see("R$ 4.747,50")  # 2.497,50 + 2.250,00


async def test_excluir_pela_tabela_com_confirmacao(user: User, dados_temporarios):
    await user.open("/")
    user.find(ui.table).trigger("excluir", {"matricula": "C01", "nome": "Caio Martins"})
    await user.should_see("Excluir Caio Martins (C01)?")
    user.find(marker="confirmar-exclusao").click()
    await user.should_see("Colaborador excluído")
    gravados = [c["matricula"] for c in json.loads(dados_temporarios.read_text(encoding="utf-8"))]
    assert gravados == ["P01"]
