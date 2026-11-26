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

ui.add_head_html(
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">',
    shared=True,
)
ui.add_css("""
body.body--dark  { --fundo:#0b0d12; --superficie:#12151c; --superficie-2:#171b24; --borda:#232836;
                   --texto:#e7e9ef; --suave:#8a91a5; --destaque:#7c7ff5; --destaque-fundo:rgba(124,127,245,.12);
                   --positivo:#34d399; --negativo:#f87171; --zebra:rgba(255,255,255,.018); }
body.body--light { --fundo:#f6f7f9; --superficie:#ffffff; --superficie-2:#f9fafb; --borda:#e4e7ec;
                   --texto:#101828; --suave:#667085; --destaque:#5558e8; --destaque-fundo:rgba(85,88,232,.08);
                   --positivo:#079455; --negativo:#d92d20; --zebra:rgba(16,24,40,.025); }
body, .q-field__native, .q-btn { font-family: 'Inter', system-ui, sans-serif; letter-spacing: -0.005em; }
body { background: var(--fundo) !important; color: var(--texto); }
.numero { font-variant-numeric: tabular-nums; }
.suave { color: var(--suave); }
.q-card { background: var(--superficie) !important; border: 1px solid var(--borda); border-radius: 12px !important; box-shadow: none !important; }
.q-field--outlined .q-field__control { border-radius: 8px; }
.q-field--outlined .q-field__control:before { border-color: var(--borda); }
.q-btn { border-radius: 8px; text-transform: none; font-weight: 600; }

/* menu lateral */
.menu { background: var(--superficie) !important; border-right: 1px solid var(--borda); }
.marca { width: 34px; height: 34px; border-radius: 9px; background: var(--destaque); color: #fff;
         display: flex; align-items: center; justify-content: center; font-weight: 700; }
.rotulo-secao { font-size: 11px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: var(--suave); }
.item-menu { border-radius: 8px; color: var(--suave); min-height: 38px; font-weight: 500; }
.item-menu:hover { background: var(--superficie-2); color: var(--texto); }
.item-menu.ativo { background: var(--destaque-fundo); color: var(--destaque); }
.item-menu .q-item__section--avatar { min-width: 34px; }
.rodape-menu { border-top: 1px solid var(--borda); }

/* cabeçalho da página */
.trilha { font-size: 13px; color: var(--suave); }
.titulo-pagina { font-size: 22px; font-weight: 700; letter-spacing: -0.02em; }

/* indicadores */
.indicador .valor { font-size: 22px; font-weight: 650; letter-spacing: -0.02em; }
.indicador .icone { width: 32px; height: 32px; border-radius: 8px; background: var(--destaque-fundo); color: var(--destaque);
                    display: flex; align-items: center; justify-content: center; }

/* tabela */
.tabela { background: var(--superficie) !important; border: 1px solid var(--borda); border-radius: 12px; }
.tabela-fixa { max-height: calc(100vh - 360px); }
.tabela thead tr th { position: sticky; top: 0; z-index: 2; background: var(--superficie-2) !important;
                      font-size: 11px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--suave);
                      border-bottom: 1px solid var(--borda); }
.tabela tbody td { border-color: var(--borda) !important; height: 52px; }
.tabela tbody tr:nth-child(even) { background: var(--zebra); }
.tabela tbody tr:hover { background: var(--destaque-fundo) !important; }
.tabela .acoes .q-btn { opacity: .55; } .tabela tbody tr:hover .acoes .q-btn { opacity: 1; }
.avatar { width: 30px; height: 30px; border-radius: 50%; background: var(--destaque-fundo); color: var(--destaque);
          font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; justify-content: center; }
.chip { display: inline-flex; align-items: center; gap: 6px; padding: 2px 10px; border-radius: 999px; font-size: 12px; font-weight: 500;
        border: 1px solid var(--borda); background: var(--superficie-2); }
.chip i { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
.cor-Padrao { background: #60a5fa; } .cor-Comissionado { background: #c084fc; } .cor-Producao { background: #2dd4bf; }

/* formulário e holerite */
.titulo-bloco { font-size: 14px; font-weight: 600; }
.linha-valor { padding: 8px 0; border-bottom: 1px dashed var(--borda); }
.total { background: var(--destaque-fundo); border-radius: 10px; padding: 14px 16px; }
.total .valor { color: var(--positivo); font-size: 22px; font-weight: 700; }
.barra { height: 6px; border-radius: 999px; background: var(--superficie-2); overflow: hidden; }
.barra > div { height: 100%; border-radius: 999px; }
""", shared=True)


def moldura(titulo: str, rota: str, subtitulo: str = ""):
    ui.colors(primary="#7c7ff5", secondary="#2dd4bf", accent="#c084fc", positive="#34d399", negative="#f87171")
    escuro = ui.dark_mode(app.storage.user.get("escuro", True))

    def alternar_tema():
        escuro.toggle()
        app.storage.user["escuro"] = escuro.value

    with ui.left_drawer(value=True, fixed=True, bordered=False).props("width=248 :breakpoint=700").classes("menu q-pa-md column no-wrap") as menu:
        with ui.row().classes("items-center no-wrap gap-3 q-px-xs q-mb-lg"):
            ui.html('<div class="marca">F</div>')
            with ui.column().classes("gap-0"):
                ui.label("Financy").classes("text-weight-bold").style("font-size:15px")
                ui.label("Folha de pagamento").classes("suave").style("font-size:12px")
        ui.label("Menu").classes("rotulo-secao q-px-sm q-mb-xs")
        with ui.list().classes("w-full"):
            for nome, icone, destino in MENU:
                ativo = destino == rota
                with ui.item(on_click=lambda d=destino: ui.navigate.to(d)).classes(
                    "item-menu q-mb-xs" + (" ativo" if ativo else "")
                ).mark(f"menu-{nome}"):
                    with ui.item_section().props("avatar"):
                        ui.icon(icone, size="20px")
                    with ui.item_section():
                        ui.label(nome)
        ui.space()
        with ui.row().classes("rodape-menu w-full items-center no-wrap q-pt-md q-px-xs"):
            ui.html('<div class="avatar">GQ</div>')
            with ui.column().classes("gap-0"):
                ui.label("Equipe GQS").style("font-size:13px;font-weight:600")
                ui.label(f"{len(sistema.colaboradores)} colaboradores").classes("suave").style("font-size:12px")

    with ui.row().classes("w-full items-center no-wrap q-px-xl q-pt-lg q-pb-md"):
        ui.button(icon="menu", on_click=menu.toggle).props("flat round").classes("lt-md suave")
        with ui.column().classes("gap-0"):
            ui.label(f"Financy  /  {titulo}").classes("trilha")
            ui.label(titulo).classes("titulo-pagina")
            if subtitulo:
                ui.label(subtitulo).classes("suave").style("font-size:13px")
        ui.space()
        ui.button(icon="dark_mode", on_click=alternar_tema).props("flat round").classes("suave").tooltip("Alternar tema")


def card_valor(rotulo: str, valor: str, icone: str, cor: str = ""):
    with ui.card().classes("indicador q-pa-md col").style("min-width:170px"):
        with ui.row().classes("w-full items-center no-wrap"):
            ui.label(rotulo).classes("suave").style("font-size:13px;font-weight:500")
            ui.space()
            with ui.element("div").classes("icone"):
                ui.icon(icone, size="18px")
        ui.label(valor).classes(f"valor numero q-mt-sm {cor}")


# ==========================================
# TELA 1: COLABORADORES (RF005, RF009)
# ==========================================

@ui.page("/")
def tela_colaboradores():
    moldura("Colaboradores", "/", "Cadastro e folha de cada colaborador")
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
    with ui.column().classes("w-full q-px-xl gap-4"):
        @ui.refreshable
        def indicadores():
            r = resumo_da_folha()
            with ui.row().classes("w-full gap-4 no-wrap"):
                card_valor("Colaboradores", str(r["quantidade"]), "groups")
                card_valor("Folha bruta", brl(r["bruto"]), "payments")
                card_valor("Descontos", brl(r["inss"] + r["irrf"]), "remove_circle_outline")
                card_valor("Folha líquida", brl(r["liquido"]), "account_balance_wallet", "text-positive")

        indicadores()

        with ui.row().classes("w-full items-center"):
            busca = ui.input(placeholder="Buscar por nome ou matrícula").props("outlined dense clearable").classes("w-80").mark("busca")
            with busca.add_slot("prepend"):
                ui.icon("search", size="18px").classes("suave")
            ui.space()
            ui.button("Novo colaborador", icon="add", on_click=lambda: ui.navigate.to("/novo")).props("unelevated color=primary")

        tabela = ui.table(columns=colunas, rows=[], row_key="matricula", pagination=0).classes("w-full tabela tabela-fixa").props("flat virtual-scroll")
        tabela.bind_filter_from(busca, "value")
        for campo in ("bruto", "inss", "irrf", "liquido"):
            destaque = " text-weight-bold" if campo == "liquido" else ""
            tabela.add_slot(f"body-cell-{campo}", f"""
                <q-td :props="props" class="numero text-right{destaque}">
                  {{{{ props.value.toLocaleString('pt-BR', {{style: 'currency', currency: 'BRL'}}) }}}}
                </q-td>""")
        tabela.add_slot("body-cell-matricula", """
            <q-td :props="props"><span class="suave numero">{{ props.value }}</span></q-td>""")
        tabela.add_slot("body-cell-nome", """
            <q-td :props="props">
              <div class="row items-center no-wrap" style="gap:10px">
                <span class="avatar">{{ props.value.split(' ').map(p => p[0]).slice(0, 2).join('').toUpperCase() }}</span>
                <span style="font-weight:500">{{ props.value }}</span>
              </div>
            </q-td>""")
        tabela.add_slot("body-cell-tipo", """
            <q-td :props="props"><span class="chip"><i :class="'cor-' + props.row.tipo"></i>{{ props.value }}</span></q-td>""")
        tabela.add_slot("body-cell-acoes", """
            <q-td :props="props" class="text-right acoes">
              <q-btn flat dense round size="sm" icon="receipt_long" @click="() => $parent.$emit('folha', props.row)"><q-tooltip>Folha individual</q-tooltip></q-btn>
              <q-btn flat dense round size="sm" icon="edit" @click="() => $parent.$emit('editar', props.row)"><q-tooltip>Alterar</q-tooltip></q-btn>
              <q-btn flat dense round size="sm" icon="delete_outline" color="negative" @click="() => $parent.$emit('excluir', props.row)"><q-tooltip>Excluir</q-tooltip></q-btn>
            </q-td>""")
        tabela.add_slot("no-data", '<div class="full-width text-center suave q-pa-xl">Nenhum colaborador por aqui. Cadastre o primeiro em "Novo colaborador".</div>')

        def recarregar():
            tabela.rows = [linha_da_tabela(c) for c in sistema.colaboradores.values()]
            tabela.update()
            indicadores.refresh()

        async def excluir(linha: dict):
            with ui.dialog() as dialogo, ui.card().classes("q-pa-lg").style("min-width:380px"):
                ui.label(f"Excluir {linha['nome']} ({linha['matricula']})?").classes("text-weight-bold").style("font-size:16px")
                ui.label("O registro sai da folha e não pode ser recuperado.").classes("suave")
                with ui.row().classes("w-full justify-end q-mt-md"):
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

    with ui.row().classes("w-full q-px-xl gap-6 items-start no-wrap"):
        with ui.card().classes("q-pa-lg col-grow gap-3").style("max-width: 640px"):
            ui.label("Identificação").classes("titulo-bloco")
            matricula = ui.input(
                "Matrícula *", value=dados["matricula"],
                validation=lambda v: validar_matricula(v, editando),
            ).props("outlined" + (" readonly" if editando else "")).classes("w-full").mark("matricula")
            matricula.on("blur", lambda: matricula.set_value((matricula.value or "").strip()))
            nome = ui.input("Nome completo *", value=dados["nome"], validation=validar_nome).props("outlined").classes("w-full").mark("nome")
            nome.on("blur", lambda: nome.set_value(" ".join((nome.value or "").split())))

            ui.separator().classes("q-my-sm")
            ui.label("Categoria e remuneração").classes("titulo-bloco")
            tipo = ui.toggle(TIPOS, value=dados["tipo"]).props("unelevated spread no-caps toggle-color=primary").classes("w-full").style(
                "border:1px solid var(--borda);border-radius:8px").mark("tipo")
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

            with ui.row().classes("w-full justify-end q-mt-md gap-2"):
                ui.button("Cancelar", on_click=lambda: ui.navigate.to("/")).props("flat color=grey-6")
                ui.button("Salvar alteração" if editando else "Cadastrar", icon="check", on_click=salvar).props("unelevated color=primary").mark("salvar")

        # Prévia calculada pelo próprio domínio (RN008): o que aparece aqui é o que vai para a folha.
        with ui.card().classes("q-pa-lg").style("width: 320px; position: sticky; top: 16px"):
            with ui.row().classes("w-full items-center no-wrap"):
                ui.label("Prévia da folha").classes("titulo-bloco")
                ui.space()
                ui.label("ao vivo").classes("chip").style("font-size:11px")

            @ui.refreshable
            def previa():
                try:
                    c = montar_colaborador({**coletar(), "matricula": "previa", "nome": "previa"})
                    valores = [("Salário bruto", c.calcular_salario_bruto(), ""), ("INSS (10%)", c.calcular_inss(), "text-negative"),
                               ("IRRF (7,5%)", c.calcular_irrf(), "text-negative")]
                except (ValidacaoError, TypeError, ValueError):
                    ui.label("Preencha os valores para ver o cálculo.").classes("suave q-mt-md")
                    return
                with ui.column().classes("w-full gap-0 q-mt-sm"):
                    for rotulo, valor, cor in valores:
                        with ui.row().classes("w-full justify-between linha-valor"):
                            ui.label(rotulo).classes("suave")
                            ui.label(brl(valor)).classes(f"numero {cor}")
                with ui.column().classes("w-full total gap-0 q-mt-md"):
                    ui.label("Salário líquido").classes("suave").style("font-size:12px")
                    ui.label(brl(c.calcular_salario_liquido())).classes("valor numero")

            previa()
            for campo in (tipo, salario, vendas, comissao, quantidade, unidade):
                campo.on_value_change(previa.refresh)


@ui.page("/novo")
def tela_novo():
    moldura("Novo colaborador", "/novo", "Campos com * são obrigatórios")
    formulario()


@ui.page("/editar/{matricula}")
def tela_editar(matricula: str):
    moldura(f"Alterar {matricula}", "/", "A matrícula identifica o registro e não muda")
    if not sistema.consultar(matricula):
        ui.label("Colaborador não encontrado.").classes("q-px-xl text-negative")
        return
    formulario(editando=matricula)


# ==========================================
# TELA 3: FOLHA INDIVIDUAL (RF007)
# ==========================================

@ui.page("/folha")
def tela_folha(matricula: str | None = None):
    moldura("Folha individual", "/folha", "Holerite com os descontos da competência")
    opcoes = {c.matricula: f"{c.matricula} · {c.nome}" for c in sistema.colaboradores.values()}
    with ui.column().classes("w-full q-px-xl gap-4").style("max-width: 820px"):
        escolha = ui.select(opcoes, label="Colaborador", value=matricula if matricula in opcoes else None, with_input=True).props("outlined dense").classes("w-full").mark("escolha")

        @ui.refreshable
        def holerite():
            c = sistema.consultar(escolha.value) if escolha.value else None
            if not c:
                with ui.card().classes("w-full q-pa-xl items-center"):
                    ui.icon("receipt_long", size="40px").classes("suave")
                    ui.label("Escolha um colaborador para ver a folha.").classes("suave")
                return
            linha = linha_da_tabela(c)
            iniciais = "".join(p[0] for p in c.nome.split()[:2]).upper()
            with ui.card().classes("w-full q-pa-none"):
                with ui.row().classes("w-full items-center no-wrap q-pa-lg gap-3").style("border-bottom:1px solid var(--borda)"):
                    ui.html(f'<div class="avatar" style="width:44px;height:44px;font-size:15px">{iniciais}</div>')
                    with ui.column().classes("gap-0"):
                        ui.label(c.nome).classes("text-weight-bold").style("font-size:17px")
                        ui.label(f"Matrícula {c.matricula}").classes("suave").style("font-size:13px")
                    ui.space()
                    ui.html(f'<span class="chip"><i class="cor-{linha["tipo"]}"></i>{linha["tipo_nome"]}</span>')
                with ui.column().classes("w-full q-px-lg q-pt-md q-pb-lg gap-0"):
                    itens = [("(+) Salário bruto", "Proventos", linha["bruto"], ""),
                             ("(−) INSS", "10% sobre o bruto", linha["inss"], "text-negative"),
                             ("(−) IRRF", "7,5% acima de R$ 2.259,20", linha["irrf"], "text-negative")]
                    for rotulo, detalhe, valor, cor in itens:
                        with ui.row().classes("w-full items-center linha-valor"):
                            with ui.column().classes("gap-0"):
                                ui.label(rotulo).style("font-weight:500")
                                ui.label(detalhe).classes("suave").style("font-size:12px")
                            ui.space()
                            ui.label(brl(valor)).classes(f"numero {cor}")
                    with ui.row().classes("w-full items-center total q-mt-lg"):
                        ui.label("(=) Salário líquido").style("font-weight:600")
                        ui.space()
                        ui.label(brl(linha["liquido"])).classes("valor numero")

        holerite()
        escolha.on_value_change(holerite.refresh)


# ==========================================
# TELA 4: RESUMO DA FOLHA (RF008)
# ==========================================

@ui.page("/resumo")
def tela_resumo():
    moldura("Resumo da folha", "/resumo", "Totais consolidados da competência")
    r = resumo_da_folha()
    with ui.column().classes("w-full q-px-xl gap-4"):
        with ui.row().classes("w-full gap-4 no-wrap"):
            card_valor("Colaboradores", str(r["quantidade"]), "groups")
            card_valor("Salários brutos", brl(r["bruto"]), "payments")
            card_valor("INSS retido", brl(r["inss"]), "shield")
            card_valor("IRRF retido", brl(r["irrf"]), "account_balance")
            card_valor("Total líquido", brl(r["liquido"]), "account_balance_wallet", "text-positive")

        cores = {"Padrao": "#60a5fa", "Comissionado": "#c084fc", "Producao": "#2dd4bf"}
        with ui.card().classes("w-full q-pa-lg"):
            ui.label("Distribuição por categoria").classes("titulo-bloco q-mb-md")
            for tipo, v in r["por_tipo"].items():
                parte = (v["liquido"] / r["liquido"] * 100) if r["liquido"] else 0
                with ui.column().classes("w-full gap-1 q-mb-md"):
                    with ui.row().classes("w-full items-center no-wrap"):
                        ui.html(f'<span class="chip"><i class="cor-{tipo}"></i>{TIPOS[tipo]}</span>')
                        ui.label(f"{v['quantidade']} colaborador{'es' if v['quantidade'] != 1 else ''}").classes("suave q-ml-sm").style("font-size:13px")
                        ui.space()
                        ui.label(f"Bruto {brl(v['bruto'])}").classes("suave numero").style("font-size:13px")
                        ui.label(brl(v["liquido"])).classes("numero text-weight-bold q-ml-lg")
                    ui.html(f'<div class="barra"><div style="width:{parte:.1f}%;background:{cores[tipo]}"></div></div>').classes("w-full")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Financy", language="pt-BR", dark=True, storage_secret="financy-gqs", favicon="💼")
