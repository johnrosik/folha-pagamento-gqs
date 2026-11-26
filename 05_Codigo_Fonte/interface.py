"""Interface web do Financy, escrita só em Python com NiceGUI (RNF001).

Usa o mesmo domínio da folha (folhadepagamento.py) e o mesmo banco SQLite (financy.db).
Execução: python interface.py  →  http://localhost:8080
"""
import os
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
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
    ("Colaboradores", "/"),
    ("Novo colaborador", "/novo"),
    ("Folha individual", "/folha"),
    ("Resumo da folha", "/resumo"),
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


def centavos(valor: float) -> float:
    """Arredonda para centavos, meio centavo para cima: é o valor que de fato se paga."""
    return float(Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def linha_da_tabela(c) -> dict:
    """Um colaborador como linha da tabela, com os valores da folha (RF006, RF010).

    Cada valor já sai em centavos, para que a soma das linhas seja igual ao total exibido.
    """
    tipo = c.to_dict()["tipo"]
    return {
        "matricula": c.matricula,
        "nome": c.nome,
        "tipo": tipo,
        "tipo_nome": TIPOS[tipo],
        "bruto": centavos(c.calcular_salario_bruto()),
        "inss": centavos(c.calcular_inss()),
        "irrf": centavos(c.calcular_irrf()),
        "liquido": centavos(c.calcular_salario_liquido()),
    }


def resumo_da_folha() -> dict:
    """RF008: totais da folha e por tipo."""
    linhas = [linha_da_tabela(c) for c in sistema.colaboradores.values()]
    total = {k: centavos(sum(l[k] for l in linhas)) for k in ("bruto", "inss", "irrf", "liquido")}
    por_tipo = {}
    for tipo in TIPOS:
        do_tipo = [l for l in linhas if l["tipo"] == tipo]
        por_tipo[tipo] = {"quantidade": len(do_tipo), **{k: centavos(sum(l[k] for l in do_tipo)) for k in ("bruto", "inss", "irrf", "liquido")}}
    return {"quantidade": len(linhas), **total, "por_tipo": por_tipo}


def proventos_do(c) -> list[tuple[str, str, float]]:
    """Proventos do holerite: (descrição, referência, valor). A soma é o salário bruto do domínio."""
    d = c.to_dict()
    itens = [("Salário base", "", d["salario_base"])]
    if d["tipo"] == "Comissionado":
        itens.append(("Comissão sobre vendas", f"{d['comissao_pct']:g}% de {brl(d['vendas'])}", d["vendas"] * d["comissao_pct"] / 100.0))
    elif d["tipo"] == "Producao":
        itens.append(("Produção", f"{d['qtd_produzida']} un × {brl(d['valor_unidade'])}", d["qtd_produzida"] * d["valor_unidade"]))
    return itens


def competencia() -> str:
    return date.today().strftime("%m/%Y")


# ==========================================
# MOLDURA: menu lateral, barra de título e barra de status
# ==========================================

ui.add_head_html(
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">',
    shared=True,
)
ui.add_css("""
body.body--dark  { --lateral:#101216; --fundo:#181b20; --barra:#21252c; --cab:#2a2f38; --campo:#313743; --hover:#2c323b;
                   --linha:rgba(255,255,255,.07); --texto:#dfe3e9; --suave:#8f98a6; --destaque:#5aa0e6; --sel:#2b3f57;
                   --positivo:#5cc58a; --negativo:#e8776f; --t-Padrao:#8f98a6; --t-Comissionado:#d9a95c; --t-Producao:#6cc3b8; }
body.body--light { --lateral:#e4e8ed; --fundo:#ffffff; --barra:#eff2f5; --cab:#e1e6ec; --campo:#e9edf2; --hover:#e8edf3;
                   --linha:rgba(20,30,50,.09); --texto:#1c2430; --suave:#5d6877; --destaque:#1f6fbd; --sel:#cfe1f4;
                   --positivo:#17794a; --negativo:#b8342c; --t-Padrao:#5d6877; --t-Comissionado:#9a6a14; --t-Producao:#1b7a70; }
body, .q-field__native, .q-btn { font-family: 'IBM Plex Sans', 'Segoe UI', sans-serif; }
body { background: var(--fundo) !important; color: var(--texto); font-size: 13px; }
.nicegui-content { padding: 0 !important; gap: 0 !important; }
.numero { font-family: 'IBM Plex Mono', Consolas, monospace; font-size: 12.5px; font-variant-numeric: tabular-nums; }
.suave { color: var(--suave); }
.neg { color: var(--negativo); }
.pos { color: var(--positivo); }

/* campos e botões: cantos pequenos, fundo por tom */
.q-field--filled .q-field__control { background: var(--campo) !important; border-radius: 3px !important; }
.q-field--filled .q-field__control:before { border: none !important; }
.q-btn { border-radius: 3px; text-transform: none; font-weight: 500; }
.q-menu { border-radius: 3px !important; background: var(--cab) !important; color: var(--texto); box-shadow: none !important; }
.q-dialog .q-card { border-radius: 3px !important; background: var(--cab) !important; box-shadow: none !important; }
.q-layout__shadow { display: none !important; }
.q-footer, .q-header { box-shadow: none !important; }
.q-notification { border-radius: 3px; box-shadow: none; }

/* menu lateral */
.menu { background: var(--lateral) !important; color: var(--texto); padding: 0 !important; }
.menu .q-item { min-height: 32px; padding: 0 16px 0 20px; border-radius: 0; color: var(--suave); font-size: 13px; }
.menu .q-item:hover { background: var(--hover); color: var(--texto); }
.menu .q-item.ativo { background: var(--sel); color: var(--texto); font-weight: 500; }
.menu .grupo { font-size: 12px; font-weight: 600; color: var(--suave); padding: 18px 20px 4px; }

/* barra de título, barra de ferramentas e de status */
.titulo-barra { background: var(--barra); height: 36px; padding: 0 16px; }
.titulo-barra .nome-tela { font-weight: 600; font-size: 13px; }
.ferramentas { background: var(--cab); min-height: 46px; padding: 6px 16px; gap: 8px; }
.status { background: var(--lateral) !important; color: var(--suave); height: 26px; font-size: 12px; padding: 0 16px; }


/* tabela de ponta a ponta, sem moldura */
.tabela { background: transparent !important; box-shadow: none !important; border-radius: 0 !important; }
.tabela-fixa { height: calc(100vh - 36px - 46px - 26px); }
.tabela thead tr th { position: sticky; top: 0; z-index: 2; background: var(--barra) !important; color: var(--suave);
                      font-size: 12px; font-weight: 600; height: 32px; padding: 0 16px; }
.tabela tbody td { border-bottom: 1px solid var(--linha) !important; height: 34px; padding: 0 16px; }
.tabela tbody tr:hover { background: var(--hover) !important; }
.tabela tbody tr.totais td { position: sticky; bottom: 0; z-index: 2; background: var(--cab) !important; font-weight: 600;
                             height: 36px; border-bottom: none !important; }
.tabela tbody tr.totais:hover { background: transparent !important; }
.tabela .acoes .q-btn { color: var(--suave); } .tabela .acoes .q-btn:hover { color: var(--texto); }
.t-Padrao { color: var(--t-Padrao); } .t-Comissionado { color: var(--t-Comissionado); } .t-Producao { color: var(--t-Producao); }

/* ficha de cadastro e prévia */
.faixa { padding: 0 0 6px; font-weight: 600; font-size: 12px; color: var(--suave); }
.faixa-previa { background: var(--cab); padding: 7px 14px; font-weight: 600; font-size: 12px; color: var(--suave); }
.ficha { background: transparent; }
.previa { background: var(--barra); }
.previa .linha { padding: 7px 14px 5px; }
.previa .final, .holerite .final { background: var(--cab); padding: 9px 14px; font-weight: 600; }

/* holerite e totais por categoria: grade de colunas */
.grade { display: grid; width: 100%; align-items: center; }
.grade > * { padding: 6px 14px; }
.grade .cab { background: var(--cab); color: var(--suave); font-size: 12px; font-weight: 600; }
.grade .cel { border-bottom: 1px solid var(--linha); min-height: 32px; display: flex; align-items: center; }
.grade .dir { justify-content: flex-end; text-align: right; }
.grade .tot { background: var(--cab); font-weight: 600; min-height: 36px; display: flex; align-items: center; }
.holerite { background: var(--barra); }
.holerite .cabeca { background: var(--cab); padding: 10px 14px; }
.holerite .ident { padding: 12px 14px 14px; }
""", shared=True)


def moldura(titulo: str, rota: str):
    ui.colors(primary="#5aa0e6", secondary="#6cc3b8", accent="#d9a95c", positive="#5cc58a", negative="#e8776f")
    escuro = ui.dark_mode(app.storage.user.get("escuro", True))

    def alternar_tema():
        escuro.toggle()
        app.storage.user["escuro"] = escuro.value

    with ui.left_drawer(value=True, fixed=True, bordered=False).props("width=224 :breakpoint=700").classes("menu column no-wrap") as menu:
        ui.label("Financy").classes("text-weight-bold").style("font-size:15px;padding:16px 20px 2px")
        ui.label("Cadastros").classes("grupo")
        with ui.list().classes("w-full"):
            for i, (nome, destino) in enumerate(MENU):
                if i == 2:
                    ui.label("Folha").classes("grupo")
                ativo = destino == rota
                with ui.item(on_click=lambda d=destino: ui.navigate.to(d)).classes("ativo" if ativo else "").mark(f"menu-{nome}"):
                    with ui.item_section():
                        ui.label(nome)
        ui.space()
        ui.label("Equipe GQS").classes("suave").style("font-size:12px;padding:10px 20px")

    with ui.row().classes("titulo-barra w-full items-center no-wrap"):
        ui.button("Menu", on_click=menu.toggle).props("flat dense no-caps size=sm").classes("lt-md suave")
        ui.label(titulo).classes("nome-tela")
        ui.space()
        ui.button("Tema", on_click=alternar_tema).props("flat dense no-caps size=sm").classes("suave").tooltip("Alternar tema")

    with ui.footer(fixed=True).classes("status row items-center no-wrap gap-6"):
        ui.label(f"{len(sistema.colaboradores)} colaboradores")
        ui.label(f"Competência {competencia()}")
        ui.label("Banco de dados: SQLite")


def faixa_ferramentas():
    return ui.row().classes("ferramentas w-full items-center no-wrap")


# ==========================================
# TELA 1: COLABORADORES (RF005, RF009)
# ==========================================

@ui.page("/")
def tela_colaboradores():
    moldura("Colaboradores", "/")
    colunas = [
        {"name": "matricula", "label": "Matrícula", "field": "matricula", "sortable": True, "align": "left"},
        {"name": "nome", "label": "Nome", "field": "nome", "sortable": True, "align": "left"},
        {"name": "tipo", "label": "Categoria", "field": "tipo_nome", "sortable": True, "align": "left"},
        {"name": "bruto", "label": "Bruto", "field": "bruto", "sortable": True, "align": "right"},
        {"name": "inss", "label": "INSS", "field": "inss", "align": "right"},
        {"name": "irrf", "label": "IRRF", "field": "irrf", "align": "right"},
        {"name": "liquido", "label": "Líquido", "field": "liquido", "sortable": True, "align": "right"},
        {"name": "acoes", "label": "", "field": "matricula", "align": "right"},
    ]
    with faixa_ferramentas():
        busca = ui.input(placeholder="Buscar por nome ou matrícula").props("filled dense clearable").classes("w-80").mark("busca")
        ui.space()
        ui.button("Novo colaborador", on_click=lambda: ui.navigate.to("/novo")).props("unelevated dense no-caps color=primary").classes("q-px-md")

    tabela = ui.table(columns=colunas, rows=[], row_key="matricula", pagination=0).classes("w-full tabela tabela-fixa").props("flat square hide-bottom")
    tabela.bind_filter_from(busca, "value")
    moeda = "toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})"
    for campo in ("bruto", "inss", "irrf", "liquido"):
        peso = " text-weight-bold" if campo == "liquido" else ""
        tabela.add_slot(f"body-cell-{campo}", f"""<q-td :props="props" class="numero text-right{peso}">{{{{ props.value.{moeda} }}}}</q-td>""")
    tabela.add_slot("body-cell-matricula", """<q-td :props="props"><span class="numero suave">{{ props.value }}</span></q-td>""")
    tabela.add_slot("body-cell-tipo", """<q-td :props="props"><span :class="'t-' + props.row.tipo">{{ props.value }}</span></q-td>""")
    tabela.add_slot("body-cell-acoes", """
        <q-td :props="props" class="text-right acoes">
          <q-btn flat dense no-caps size="sm" label="Folha" @click="() => $parent.$emit('folha', props.row)"></q-btn>
          <q-btn flat dense no-caps size="sm" label="Alterar" @click="() => $parent.$emit('editar', props.row)"></q-btn>
          <q-btn flat dense no-caps size="sm" label="Excluir" @click="() => $parent.$emit('excluir', props.row)"></q-btn>
        </q-td>""")

    def soma(k):
        return f"(Math.round($parent.filteredSortedRows.reduce((s, r) => s + r.{k}, 0) * 100) / 100).{moeda}"

    tabela.add_slot("bottom-row", f"""
        <q-tr class="totais">
          <q-td></q-td>
          <q-td>Total ({{{{ $parent.filteredSortedRows.length }}}})</q-td>
          <q-td></q-td>
          <q-td class="numero text-right">{{{{ {soma('bruto')} }}}}</q-td>
          <q-td class="numero text-right">{{{{ {soma('inss')} }}}}</q-td>
          <q-td class="numero text-right">{{{{ {soma('irrf')} }}}}</q-td>
          <q-td class="numero text-right">{{{{ {soma('liquido')} }}}}</q-td>
          <q-td></q-td>
        </q-tr>""")
    tabela.add_slot("no-data", '<div class="full-width text-center suave q-pa-xl">Nenhum colaborador cadastrado.</div>')

    def recarregar():
        tabela.rows = [linha_da_tabela(c) for c in sistema.colaboradores.values()]
        tabela.update()

    async def excluir(linha: dict):
        with ui.dialog() as dialogo, ui.card().classes("q-pa-lg").style("min-width:380px"):
            ui.label(f"Excluir {linha['nome']} ({linha['matricula']})?").classes("text-weight-bold").style("font-size:15px")
            ui.label("O registro sai da folha e não pode ser recuperado.").classes("suave")
            with ui.row().classes("w-full justify-end q-mt-md"):
                ui.button("Cancelar", on_click=lambda: dialogo.submit(False)).props("flat dense no-caps")
                ui.button("Excluir", color="negative", on_click=lambda: dialogo.submit(True)).props("unelevated dense no-caps").classes("q-px-md").mark("confirmar-exclusao")
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

    barra = faixa_ferramentas()
    with ui.row().classes("w-full items-start no-wrap").style("padding:20px 16px 16px 20px;gap:40px"):
        with ui.column().classes("col-grow gap-0").style("max-width: 560px"):
            ui.label("Identificação").classes("faixa w-full")
            with ui.column().classes("ficha w-full gap-3"):
                matricula = ui.input(
                    "Matrícula *", value=dados["matricula"],
                    validation=lambda v: validar_matricula(v, editando),
                ).props("filled dense square" + (" readonly" if editando else "")).classes("w-full").mark("matricula")
                matricula.on("blur", lambda: matricula.set_value((matricula.value or "").strip()))
                nome = ui.input("Nome completo *", value=dados["nome"], validation=validar_nome).props("filled dense square").classes("w-full").mark("nome")
                nome.on("blur", lambda: nome.set_value(" ".join((nome.value or "").split())))

            ui.label("Categoria e remuneração").classes("faixa w-full q-mt-lg")
            with ui.column().classes("ficha w-full gap-3"):
                tipo = ui.select(TIPOS, label="Categoria", value=dados["tipo"]).props("filled dense square options-dense").classes("w-full").mark("tipo")
                if editando:
                    tipo.props("disable")

                def numero(rotulo, chave, regra, prefixo="R$", passo=0.01, inteiro=False, marca=""):
                    campo = ui.number(
                        rotulo, value=dados.get(chave), min=0, step=passo, prefix=prefixo, precision=0 if inteiro else 2,
                        validation=lambda v: validar_nao_negativo(v, regra, rotulo.rstrip(" *")),
                    ).props("filled dense square").classes("w-full").mark(marca)
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

        with barra:
            ui.button("Salvar alteração" if editando else "Cadastrar", on_click=salvar).props("unelevated dense no-caps color=primary").classes("q-px-md").mark("salvar")
            ui.button("Cancelar", on_click=lambda: ui.navigate.to("/")).props("flat dense no-caps").classes("suave")
            ui.space()
            ui.label("Campos com * são obrigatórios").classes("suave")

        # Prévia calculada pelo próprio domínio (RN008): o que aparece aqui é o que vai para a folha.
        with ui.column().classes("gap-0").style("width: 320px"):
            ui.label("Prévia da folha").classes("faixa-previa w-full")

            @ui.refreshable
            def previa():
                with ui.column().classes("previa w-full gap-0"):
                    try:
                        c = montar_colaborador({**coletar(), "matricula": "previa", "nome": "previa"})
                        valores = [("Salário bruto", c.calcular_salario_bruto(), ""), ("INSS (10%)", c.calcular_inss(), "neg"),
                                   ("IRRF (7,5%)", c.calcular_irrf(), "neg")]
                    except (ValidacaoError, TypeError, ValueError):
                        ui.label("Preencha os valores para ver o cálculo.").classes("suave q-pa-md")
                        return
                    for rotulo, valor, cor in valores:
                        with ui.row().classes("linha w-full justify-between no-wrap"):
                            ui.label(rotulo).classes("suave")
                            ui.label(brl(valor)).classes(f"numero {cor}")
                    with ui.row().classes("final w-full justify-between no-wrap"):
                        ui.label("Salário líquido")
                        ui.label(brl(c.calcular_salario_liquido())).classes("numero")

            previa()
            for campo in (tipo, salario, vendas, comissao, quantidade, unidade):
                campo.on_value_change(previa.refresh)


@ui.page("/novo")
def tela_novo():
    moldura("Novo colaborador", "/novo")
    formulario()


@ui.page("/editar/{matricula}")
def tela_editar(matricula: str):
    moldura(f"Alterar colaborador {matricula}", "/")
    if not sistema.consultar(matricula):
        ui.label("Colaborador não encontrado.").classes("q-pa-md neg")
        return
    formulario(editando=matricula)


# ==========================================
# TELA 3: FOLHA INDIVIDUAL (RF007)
# ==========================================

def grade(colunas: str):
    return ui.element("div").classes("grade").style(f"grid-template-columns:{colunas}")


@ui.page("/folha")
def tela_folha(matricula: str | None = None):
    moldura("Folha individual", "/folha")
    opcoes = {c.matricula: f"{c.matricula} · {c.nome}" for c in sistema.colaboradores.values()}
    with faixa_ferramentas():
        escolha = ui.select(opcoes, label="Colaborador", value=matricula if matricula in opcoes else None, with_input=True).props(
            "filled dense square options-dense").classes("w-96").mark("escolha")
        ui.space()
        ui.button("Imprimir", on_click=lambda: ui.run_javascript("window.print()")).props("flat dense no-caps").classes("suave")

    @ui.refreshable
    def holerite():
        c = sistema.consultar(escolha.value) if escolha.value else None
        if not c:
            ui.label("Escolha um colaborador para ver a folha.").classes("suave q-pa-md")
            return
        linha = linha_da_tabela(c)
        with ui.column().classes("w-full q-pa-md"), ui.column().classes("holerite gap-0").style("max-width: 860px; width: 100%"):
            with ui.row().classes("cabeca w-full justify-between items-start no-wrap"):
                with ui.column().classes("gap-0"):
                    ui.label("Financy").classes("text-weight-bold").style("font-size:14px")
                    ui.label("Recibo de pagamento de salário").classes("suave")
                with ui.column().classes("gap-0 items-end"):
                    ui.label("Competência").classes("suave")
                    ui.label(competencia()).classes("numero")
            with ui.row().classes("ident w-full gap-8"):
                for rotulo, valor in (("Matrícula", c.matricula), ("Nome", c.nome), ("Categoria", linha["tipo_nome"])):
                    with ui.column().classes("gap-0"):
                        ui.label(rotulo).classes("suave").style("font-size:11px")
                        ui.label(valor).classes("numero" if rotulo == "Matrícula" else "")
            with grade("1fr 250px 150px 150px"):
                for i, t in enumerate(("Descrição", "Referência", "Proventos", "Descontos")):
                    ui.label(t).classes("cab" + (" dir" if i > 1 else ""))
                descontos = [("INSS", "10,00%", linha["inss"]), ("IRRF", "7,50% sobre o excedente da base", linha["irrf"])]
                for desc, ref, valor in proventos_do(c):
                    ui.label(desc).classes("cel")
                    ui.label(ref).classes("cel suave")
                    ui.label(brl(valor)).classes("cel dir numero")
                    ui.label("").classes("cel")
                for desc, ref, valor in descontos:
                    ui.label(desc).classes("cel")
                    ui.label(ref).classes("cel suave")
                    ui.label("").classes("cel")
                    ui.label(brl(valor)).classes("cel dir numero neg")
                ui.label("Totais").classes("tot")
                ui.label("").classes("tot")
                ui.label(brl(linha["bruto"])).classes("tot dir numero")
                ui.label(brl(linha["inss"] + linha["irrf"])).classes("tot dir numero")
            with ui.row().classes("final w-full justify-between no-wrap"):
                ui.label("(=) Salário líquido")
                ui.label(brl(linha["liquido"])).classes("numero pos").style("font-size:15px")

    holerite()
    escolha.on_value_change(holerite.refresh)


# ==========================================
# TELA 4: RESUMO DA FOLHA (RF008)
# ==========================================

@ui.page("/resumo")
def tela_resumo():
    moldura("Resumo da folha", "/resumo")
    r = resumo_da_folha()
    with faixa_ferramentas():
        ui.label(f"Competência {competencia()}").classes("suave")
    with ui.column().classes("w-full q-pa-md").style("max-width: 1000px"):
        with grade("1fr 110px repeat(4, 150px)"):
            for i, t in enumerate(("Categoria", "Colaboradores", "Bruto", "INSS", "IRRF", "Total líquido")):
                ui.label(t).classes("cab" + (" dir" if i else ""))
            for tipo, v in r["por_tipo"].items():
                ui.label(TIPOS[tipo]).classes("cel")
                ui.label(str(v["quantidade"])).classes("cel dir numero")
                for k in ("bruto", "inss", "irrf", "liquido"):
                    ui.label(brl(v[k])).classes("cel dir numero")
            ui.label("Total geral").classes("tot")
            ui.label(str(r["quantidade"])).classes("tot dir numero")
            for k in ("bruto", "inss", "irrf", "liquido"):
                ui.label(brl(r[k])).classes("tot dir numero")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Financy", language="pt-BR", dark=True, storage_secret="financy-gqs",
           favicon='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" fill="#5aa0e6"/>'
                   '<path d="M10 8h13v4h-8v3h7v4h-7v5h-5z" fill="#101216"/></svg>')
