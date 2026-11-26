from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from folhadepagamento import (
    ColaboradorComissionado,
    ColaboradorPadrao,
    ColaboradorProducao,
    BANCO_PADRAO,
    JSON_ANTIGO,
    SistemaFolha,
    ValidacaoError,
)


app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
sistema = SistemaFolha(BANCO_PADRAO, importar_json=JSON_ANTIGO)


def serializar(colaborador):
    """Dados do colaborador com os valores calculados (RF006, RF010)."""
    dados = colaborador.to_dict()
    dados.update(
        {
            "bruto": colaborador.calcular_salario_bruto(),
            "inss": colaborador.calcular_inss(),
            "irrf": colaborador.calcular_irrf(),
            "liquido": colaborador.calcular_salario_liquido(),
        }
    )
    return dados


def montar_colaborador(dados, matricula):
    """Cria o colaborador do tipo pedido a partir do JSON recebido (RF002 a RF004)."""
    nome = dados.get("nome")
    if not isinstance(matricula, str) or not isinstance(nome, str):
        raise ValidacaoError("Matrícula e nome são obrigatórios.")

    tipo = dados.get("tipo")
    if tipo == "Padrao":
        return ColaboradorPadrao(matricula, nome, float(dados.get("salario_base", 0)))
    if tipo == "Comissionado":
        return ColaboradorComissionado(
            matricula,
            nome,
            float(dados.get("salario_base", 0)),
            float(dados.get("vendas", 0)),
            float(dados.get("comissao_pct", 0)),
        )
    if tipo == "Producao":
        return ColaboradorProducao(
            matricula,
            nome,
            float(dados.get("salario_base", 0)),
            int(dados.get("qtd_produzida", 0)),
            float(dados.get("valor_unidade", 0)),
        )
    raise ValidacaoError("Tipo de colaborador inválido.")


def ler_json():
    dados = request.get_json(silent=True)
    return dados if isinstance(dados, dict) else None


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/api/colaboradores")
def listar_colaboradores():
    """RF005 e RF008: lista com os valores da folha de cada colaborador."""
    return jsonify([serializar(c) for c in sistema.colaboradores.values()])


@app.get("/api/colaboradores/<matricula>")
def consultar_colaborador(matricula):
    """RF005 e RF007: consulta e folha individual."""
    colaborador = sistema.consultar(matricula)
    if not colaborador:
        return jsonify({"erro": "Colaborador não encontrado."}), 404
    return jsonify(serializar(colaborador))


@app.post("/api/colaboradores")
def cadastrar_colaborador():
    dados = ler_json()
    if dados is None:
        return jsonify({"erro": "Envie os dados do colaborador em formato JSON."}), 400
    try:
        sistema.cadastrar(montar_colaborador(dados, dados.get("matricula")))
    except (TypeError, ValueError):
        return jsonify({"erro": "Os campos numéricos devem conter valores válidos."}), 400
    except ValidacaoError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify({"mensagem": "Colaborador cadastrado com sucesso."}), 201


@app.put("/api/colaboradores/<matricula>")
def alterar_colaborador(matricula):
    """RF009: alteração de cadastro. A matrícula vem da URL e não muda."""
    dados = ler_json()
    if dados is None:
        return jsonify({"erro": "Envie os dados do colaborador em formato JSON."}), 400
    if not sistema.consultar(matricula):
        return jsonify({"erro": "Colaborador não encontrado."}), 404
    try:
        sistema.alterar(montar_colaborador(dados, matricula))
    except (TypeError, ValueError):
        return jsonify({"erro": "Os campos numéricos devem conter valores válidos."}), 400
    except ValidacaoError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify({"mensagem": "Colaborador alterado com sucesso."})


@app.delete("/api/colaboradores/<matricula>")
def excluir_colaborador(matricula):
    try:
        sistema.excluir(matricula)
    except ValidacaoError as erro:
        return jsonify({"erro": str(erro)}), 404
    return jsonify({"mensagem": "Colaborador excluído com sucesso."})


if __name__ == "__main__":
    app.run(debug=True)
