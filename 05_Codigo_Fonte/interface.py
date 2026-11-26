"""Interface web do Financy, escrita só em Python com NiceGUI (RNF001).

Usa o mesmo domínio da folha (folhadepagamento.py) e o mesmo banco SQLite (financy.db).
Execução: python interface.py  →  http://localhost:8080
"""
import os
from pathlib import Path

from nicegui import app, ui

from folhadepagamento import (
    ColaboradorComissionado,
    ColaboradorPadrao,
    ColaboradorProducao,
    BANCO_PADRAO,
    JSON_ANTIGO,
    SistemaFolha,
    ValidacaoError,
)

# FINANCY_DADOS aponta para outro banco (os testes de tela usam um temporário, sem migração).
if os.environ.get("FINANCY_DADOS"):
    sistema = SistemaFolha(os.environ["FINANCY_DADOS"])
else:
    sistema = SistemaFolha(BANCO_PADRAO, importar_json=JSON_ANTIGO)

TIPOS = {"Padrao": "Padrão", "Comissionado": "Comissionado", "Producao": "Produção"}
CORES_TIPO = {"Padrao": "blue", "Comissionado": "purple", "Producao": "teal"}
MENU = (
    ("Colaboradores", "groups", "/"),
    ("Novo colaborador", "person_add", "/novo"),
    ("Folha individual", "receipt_long", "/folha"),
    ("Resumo da folha", "insights", "/resumo"),
)


# ==========================================
# REGRAS DA TELA (funções puras, testadas em test_interface.py)
# ==========================================

def brl(valor: float) -> str:
    """Formata em reais no padrão brasileiro: 1234.5 → 'R$ 1.234,50'."""
    texto = f"{float(valor or 0):,.2f}"
    return "R$ " + texto.replace(",", "_").replace(".", ",").replace("_", ".")


def validar_matricula(valor: str, editando: str | None = None) -> str | None:
    """RN001: obrigatória e única. Na alteração, a própria matrícula é aceita."""
    valor = (valor or "").strip()
    if not valor:
        return "Matrícula é obrigatória"
    if valor != editando and sistema.consultar(valor):
        return "RN001: essa matrícula já existe"
    return None


def validar_nome(valor: str) -> str | None:
    """RN002: nome obrigatório."""
    return None if (valor or "").strip() else "RN002: nome é obrigatório"


def validar_nao_negativo(valor, regra: str, campo: str) -> str | None:
    """RN003 a RN007: campo numérico obrigatório e não negativo."""
    if valor is None:
        return f"{campo} é obrigatório"
    if valor < 0:
        return f"{regra}: {campo.lower()} não pode ser negativo"
    return None


def montar_colaborador(dados: dict):
    """Cria o colaborador do tipo escolhido; as regras de negócio ficam no domínio."""
    matricula, nome = (dados.get("matricula") or "").strip(), dados.get("nome") or ""
    base = float(dados.get("salario_base") or 0)
    if dados["tipo"] == "Comissionado":
        return ColaboradorComissionado(matricula, nome, base, float(dados.get("vendas") or 0), float(dados.get("comissao_pct") or 0))
    if dados["tipo"] == "Producao":
        return ColaboradorProducao(matricula, nome, base, int(dados.get("qtd_produzida") or 0), float(dados.get("valor_unidade") or 0))
    return ColaboradorPadrao(matricula, nome, base)


def linha_da_tabela(c) -> dict:
    """Um colaborador como linha da tabela, com os valores da folha (RF006, RF010)."""
    tipo = c.to_dict()["tipo"]
    return {
        "matricula": c.matricula,
        "nome": c.nome,
        "tipo": tipo,
        "tipo_nome": TIPOS[tipo],
        "bruto": c.calcular_salario_bruto(),
        "inss": c.calcular_inss(),
        "irrf": c.calcular_irrf(),
        "liquido": c.calcular_salario_liquido(),
    }


def resumo_da_folha() -> dict:
    """RF008: totais da folha e por tipo."""
    linhas = [linha_da_tabela(c) for c in sistema.colaboradores.values()]
    total = {k: sum(l[k] for l in linhas) for k in ("bruto", "inss", "irrf", "liquido")}
    por_tipo = {}
    for tipo in TIPOS:
        do_tipo = [l for l in linhas if l["tipo"] == tipo]
        por_tipo[tipo] = {"quantidade": len(do_tipo), **{k: sum(l[k] for l in do_tipo) for k in ("bruto", "liquido")}}
    return {"quantidade": len(linhas), **total, "por_tipo": por_tipo}


# ==========================================
# MOLDURA: menu lateral flutuante e cabeçalho
# ==========================================

ui.add_css("""
.menu-flutuante { margin: 12px; border-radius: 16px; }
.tabela-fixa { height: calc(100vh - 230px); }
.tabela-fixa thead tr th { position: sticky; top: 0; z-index: 2; }
.tabela-fixa thead tr:first-child th { background: var(--q-dark-page, #121212); }
body.body--light .tabela-fixa thead tr:first-child th { background: #f1f3f7; }
.numero { font-variant-numeric: tabular-nums; }
""", shared=True)


def moldura(titulo: str, rota: str):
    ui.colors(primary="#4f8cff", secondary="#2ec4b6", accent="#b07cff", positive="#3ccf91", negative="#ff6b6b")
    escuro = ui.dark_mode(app.storage.user.get("escuro", True))

    def alternar_tema():
        escuro.toggle()
        app.storage.user["escuro"] = escuro.value

    with ui.left_drawer(value=True, fixed=True, bordered=False).props("width=240 :breakpoint=700").classes("menu-flutuante bg-grey-10 q-pa-md") as menu:
        with ui.row().classes("items-center q-mb-lg no-wrap"):
            ui.label("F").classes("text-h6 text-white bg-primary rounded-borders q-px-md q-py-xs")
            with ui.column().classes("gap-0"):
                ui.label("Financy").classes("text-subtitle1 text-weight-bold text-white")
                ui.label("Folha de pagamento").classes("text-caption text-grey-5")
        with ui.list().classes("w-full"):
            for nome, icone, destino in MENU:
                ativo = destino == rota
                with ui.item(on_click=lambda d=destino: ui.navigate.to(d)).classes(
                    "rounded-borders q-mb-xs " + ("bg-primary text-white" if ativo else "text-grey-4")
                ).mark(f"menu-{nome}"):
                    with ui.item_section().props("avatar"):
                        ui.icon(icone)
                    with ui.item_section():
                        ui.label(nome)

    with ui.row().classes("w-full items-center q-px-lg q-pt-md q-pb-sm"):
        ui.button(icon="menu", on_click=menu.toggle).props("flat round").classes("lt-md text-grey-5")
        ui.label(titulo).classes("text-h5 text-weight-bold")
        ui.space()
        ui.button(icon="dark_mode", on_click=alternar_tema).props("flat round").classes("text-grey-5").tooltip("Alternar tema")


def card_valor(rotulo: str, valor: str, cor: str = ""):
    with ui.card().classes("q-pa-md col"):
        ui.label(rotulo).classes("text-caption text-grey-6 text-uppercase")
        ui.label(valor).classes(f"text-h6 numero {cor}")


# ==========================================
# TELA 1: COLABORADORES (RF005, RF009)
# ==========================================

@ui.page("/")
def tela_colaboradores():
    moldura("Colaboradores", "/")
    colunas = [
        {"name": "matricula", "label": "Matrícula", "field": "matricula", "sortable": True, "align": "left"},
        {"name": "nome", "label": "Nome", "field": "nome", "sortable": True, "align": "left"},
        {"name": "tipo", "label": "Tipo", "field": "tipo_nome", "sortable": True, "align": "left"},
        {"name": "bruto", "label": "Bruto", "field": "bruto", "sortable": True},
        {"name": "inss", "label": "INSS", "field": "inss"},
        {"name": "irrf", "label": "IRRF", "field": "irrf"},
        {"name": "liquido", "label": "Líquido", "field": "liquido", "sortable": True},
        {"name": "acoes", "label": "", "field": "matricula"},
    ]
    with ui.column().classes("w-full q-px-lg gap-3"):
        with ui.row().classes("w-full items-center"):
            busca = ui.input(placeholder="Buscar por nome ou matrícula").props("outlined dense clearable").classes("w-72").mark("busca")
            ui.space()
            ui.button("Novo colaborador", icon="person_add", on_click=lambda: ui.navigate.to("/novo")).props("unelevated")

        tabela = ui.table(columns=colunas, rows=[], row_key="matricula", pagination=0).classes("w-full tabela-fixa").props("flat bordered virtual-scroll")
        tabela.bind_filter_from(busca, "value")
        for campo in ("bruto", "inss", "irrf", "liquido"):
            tabela.add_slot(f"body-cell-{campo}", f"""
                <q-td :props="props" class="numero text-right">
                  {{{{ props.value.toLocaleString('pt-BR', {{style: 'currency', currency: 'BRL'}}) }}}}
                </q-td>""")
        tabela.add_slot("body-cell-tipo", """
            <q-td :props="props">
              <q-badge :color="{Padrao: 'blue', Comissionado: 'purple', Producao: 'teal'}[props.row.tipo]" :label="props.value" />
            </q-td>""")
        tabela.add_slot("body-cell-acoes", """
            <q-td :props="props" class="text-right">
              <q-btn flat dense round icon="receipt_long" @click="() => $parent.$emit('folha', props.row)"><q-tooltip>Folha individual</q-tooltip></q-btn>
              <q-btn flat dense round icon="edit" @click="() => $parent.$emit('editar', props.row)"><q-tooltip>Alterar</q-tooltip></q-btn>
              <q-btn flat dense round icon="delete" color="negative" @click="() => $parent.$emit('excluir', props.row)"><q-tooltip>Excluir</q-tooltip></q-btn>
            </q-td>""")
        tabela.add_slot("no-data", '<div class="full-width text-center text-grey-6 q-pa-lg">Nenhum colaborador por aqui. Cadastre o primeiro em "Novo colaborador".</div>')

        def recarregar():
            tabela.rows = [linha_da_tabela(c) for c in sistema.colaboradores.values()]
            tabela.update()

        async def excluir(linha: dict):
            with ui.dialog() as dialogo, ui.card():
                ui.label(f"Excluir {linha['nome']} ({linha['matricula']})?").classes("text-subtitle1")
                ui.label("O registro sai da folha e não pode ser recuperado.").classes("text-grey-6")
                with ui.row().classes("w-full justify-end"):
                    ui.button("Cancelar", on_click=lambda: dialogo.submit(False)).props("flat")
                    ui.button("Excluir", color="negative", on_click=lambda: dialogo.submit(True)).props("unelevated").mark("confirmar-exclusao")
            if await dialogo:
                sistema.excluir(linha["matricula"])
                ui.notify("Colaborador excluído", type="positive")
                recarregar()

        tabela.on("editar", lambda e: ui.navigate.to(f"/editar/{e.args['matricula']}"))
        tabela.on("folha", lambda e: ui.navigate.to(f"/folha?matricula={e.args['matricula']}"))
        tabela.on("excluir", lambda e: excluir(e.args))
        recarregar()


# ==========================================
# TELA 2: NOVO COLABORADOR E ALTERAÇÃO (RF001 a RF004, RF009)
# ==========================================

def formulario(editando: str | None = None):
    atual = sistema.consultar(editando) if editando else None
    dados = atual.to_dict() if atual else {"tipo": "Padrao", "matricula": "", "nome": "", "salario_base": None}

    with ui.row().classes("w-full q-px-lg gap-6 items-start"):
        with ui.card().classes("q-pa-lg col-grow").style("max-width: 620px"):
            matricula = ui.input(
                "Matrícula *", value=dados["matricula"],
                validation=lambda v: validar_matricula(v, editando),
            ).props("outlined" + (" readonly" if editando else "")).classes("w-full").mark("matricula")
            matricula.on("blur", lambda: matricula.set_value((matricula.value or "").strip()))
            nome = ui.input("Nome completo *", value=dados["nome"], validation=validar_nome).props("outlined").classes("w-full").mark("nome")
            nome.on("blur", lambda: nome.set_value(" ".join((nome.value or "").split())))

            ui.label("Categoria").classes("text-caption text-grey-6 q-mt-sm")
            tipo = ui.toggle(TIPOS, value=dados["tipo"]).props("unelevated spread no-caps").classes("w-full").mark("tipo")
            if editando:
                tipo.props("disable")

            def numero(rotulo, chave, regra, prefixo="R$", passo=0.01, inteiro=False, marca=""):
                campo = ui.number(
                    rotulo, value=dados.get(chave), min=0, step=passo, prefix=prefixo, precision=0 if inteiro else 2,
                    validation=lambda v: validar_nao_negativo(v, regra, rotulo.rstrip(" *")),
                ).props("outlined").classes("w-full").mark(marca)
                campo.on("blur", lambda: campo.set_value(abs(campo.value)) if campo.value is not None and campo.value < 0 else None)
                return campo

            salario = numero("Salário base *", "salario_base", "RN003", marca="salario")
            with ui.row().classes("w-full no-wrap gap-3") as linha_comissao:
                vendas = numero("Total de vendas *", "vendas", "RN004", marca="vendas")
                comissao = numero("Comissão *", "comissao_pct", "RN005", prefixo="%", marca="comissao")
            with ui.row().classes("w-full no-wrap gap-3") as linha_producao:
                quantidade = numero("Quantidade produzida *", "qtd_produzida", "RN006", prefixo="un", passo=1, inteiro=True, marca="quantidade")
                unidade = numero("Valor por unidade *", "valor_unidade", "RN007", marca="unidade")

            linha_comissao.bind_visibility_from(tipo, "value", value="Comissionado")
            linha_producao.bind_visibility_from(tipo, "value", value="Producao")

            def campos_do_tipo():
                extra = {"Comissionado": [vendas, comissao], "Producao": [quantidade, unidade]}.get(tipo.value, [])
                return [matricula, nome, salario, *extra]

            def coletar():
                return {
                    "tipo": tipo.value, "matricula": matricula.value, "nome": nome.value,
                    "salario_base": salario.value, "vendas": vendas.value, "comissao_pct": comissao.value,
                    "qtd_produzida": quantidade.value, "valor_unidade": unidade.value,
                }

            async def salvar():
                resultados = [campo.validate() for campo in campos_do_tipo()]  # valida todos, para marcar todos
                if not all(resultados):
                    ui.notify("Corrija os campos marcados em vermelho", type="warning")
                    return
                try:
                    colaborador = montar_colaborador(coletar())
                    sistema.alterar(colaborador) if editando else sistema.cadastrar(colaborador)
                except ValidacaoError as erro:
                    ui.notify(str(erro), type="negative")
                    return
                ui.notify("Cadastro alterado" if editando else "Colaborador cadastrado", type="positive")
                ui.navigate.to("/")

            with ui.row().classes("w-full justify-end q-mt-md"):
                ui.button("Cancelar", on_click=lambda: ui.navigate.to("/")).props("flat")
                ui.button("Salvar alteração" if editando else "Cadastrar", icon="check", on_click=salvar).props("unelevated").mark("salvar")

        # Prévia calculada pelo próprio domínio (RN008): o que aparece aqui é o que vai para a folha.
        with ui.card().classes("q-pa-lg").style("min-width: 280px"):
            ui.label("Prévia da folha").classes("text-subtitle1 text-weight-bold")

            @ui.refreshable
            def previa():
                try:
                    c = montar_colaborador({**coletar(), "matricula": "previa", "nome": "previa"})
                    valores = [("Salário bruto", c.calcular_salario_bruto()), ("INSS (10%)", c.calcular_inss()),
                               ("IRRF (7,5%)", c.calcular_irrf()), ("Salário líquido", c.calcular_salario_liquido())]
                except (ValidacaoError, TypeError, ValueError):
                    ui.label("Preencha os valores para ver o cálculo.").classes("text-grey-6")
                    return
                for i, (rotulo, valor) in enumerate(valores):
                    ultimo = i == len(valores) - 1
                    with ui.row().classes("w-full justify-between" + (" q-pt-sm border-t text-positive text-weight-bold" if ultimo else "")):
                        ui.label(rotulo)
                        ui.label(brl(valor)).classes("numero")

            previa()
            for campo in (tipo, salario, vendas, comissao, quantidade, unidade):
                campo.on_value_change(previa.refresh)


@ui.page("/novo")
def tela_novo():
    moldura("Novo colaborador", "/novo")
    formulario()


@ui.page("/editar/{matricula}")
def tela_editar(matricula: str):
    moldura(f"Alterar {matricula}", "/")
    if not sistema.consultar(matricula):
        ui.label("Colaborador não encontrado.").classes("q-px-lg text-negative")
        return
    formulario(editando=matricula)


# ==========================================
# TELA 3: FOLHA INDIVIDUAL (RF007)
# ==========================================

@ui.page("/folha")
def tela_folha(matricula: str | None = None):
    moldura("Folha individual", "/folha")
    opcoes = {c.matricula: f"{c.matricula} · {c.nome}" for c in sistema.colaboradores.values()}
    with ui.column().classes("w-full q-px-lg gap-4").style("max-width: 760px"):
        escolha = ui.select(opcoes, label="Colaborador", value=matricula if matricula in opcoes else None, with_input=True).props("outlined").classes("w-full").mark("escolha")

        @ui.refreshable
        def holerite():
            c = sistema.consultar(escolha.value) if escolha.value else None
            if not c:
                ui.label("Escolha um colaborador para ver a folha.").classes("text-grey-6")
                return
            linha = linha_da_tabela(c)
            with ui.card().classes("w-full q-pa-lg"):
                with ui.row().classes("w-full items-center"):
                    with ui.column().classes("gap-0"):
                        ui.label(c.nome).classes("text-h6")
                        ui.label(f"Matrícula {c.matricula}").classes("text-grey-6")
                    ui.space()
                    ui.badge(linha["tipo_nome"], color=CORES_TIPO[linha["tipo"]])
                ui.separator().classes("q-my-md")
                itens = [("(+) Salário bruto", linha["bruto"], ""), ("(−) INSS", linha["inss"], "text-negative"),
                         ("(−) IRRF", linha["irrf"], "text-negative")]
                for rotulo, valor, cor in itens:
                    with ui.row().classes("w-full justify-between"):
                        ui.label(rotulo)
                        ui.label(brl(valor)).classes(f"numero {cor}")
                ui.separator().classes("q-my-md")
                with ui.row().classes("w-full justify-between text-h6 text-positive"):
                    ui.label("(=) Salário líquido")
                    ui.label(brl(linha["liquido"])).classes("numero")

        holerite()
        escolha.on_value_change(holerite.refresh)


# ==========================================
# TELA 4: RESUMO DA FOLHA (RF008)
# ==========================================

@ui.page("/resumo")
def tela_resumo():
    moldura("Resumo da folha", "/resumo")
    r = resumo_da_folha()
    with ui.column().classes("w-full q-px-lg gap-4"):
        with ui.row().classes("w-full gap-4"):
            card_valor("Colaboradores", str(r["quantidade"]))
            card_valor("Salários brutos", brl(r["bruto"]))
            card_valor("INSS retido", brl(r["inss"]))
            card_valor("IRRF retido", brl(r["irrf"]))
            card_valor("Total líquido", brl(r["liquido"]), "text-positive")
        colunas = [
            {"name": "tipo", "label": "Categoria", "field": "tipo", "align": "left"},
            {"name": "quantidade", "label": "Colaboradores", "field": "quantidade"},
            {"name": "bruto", "label": "Bruto", "field": "bruto"},
            {"name": "liquido", "label": "Líquido", "field": "liquido"},
        ]
        linhas = [{"tipo": TIPOS[t], "quantidade": v["quantidade"], "bruto": brl(v["bruto"]), "liquido": brl(v["liquido"])}
                  for t, v in r["por_tipo"].items()]
        ui.table(columns=colunas, rows=linhas, row_key="tipo").classes("w-full").props("flat bordered")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Financy", language="pt-BR", dark=True, storage_secret="financy-gqs", favicon="💼")
