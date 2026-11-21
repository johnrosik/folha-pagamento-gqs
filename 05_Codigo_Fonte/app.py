from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from folhadepagamento import (
    ColaboradorComissionado,
    ColaboradorPadrao,
    ColaboradorProducao,
    SistemaFolha,
    ValidacaoError,
)


app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = Path(__file__).resolve().parent / "colaboradores.json"
sistema = SistemaFolha(str(DATA_FILE))


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/api/colaboradores")
def listar_colaboradores():
    colaboradores = []
    for colaborador in sistema.colaboradores.values():
        bruto = colaborador.calcular_salario_bruto()
        colaboradores.append(
            {
                "matricula": colaborador.matricula,
                "nome": colaborador.nome,
                "tipo": colaborador.to_dict()["tipo"],
                "bruto": bruto,
                "inss": colaborador.calcular_inss(),
                "irrf": colaborador.calcular_irrf(),
                "liquido": colaborador.calcular_salario_liquido(),
            }
        )
    return jsonify(colaboradores)


@app.post("/api/colaboradores")
def cadastrar_colaborador():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return jsonify({"erro": "Envie os dados do colaborador em formato JSON."}), 400

    matricula = dados.get("matricula")
    nome = dados.get("nome")
    if not isinstance(matricula, str) or not isinstance(nome, str):
        return jsonify({"erro": "Matrícula e nome são obrigatórios."}), 400

    try:
        tipo = dados.get("tipo")
        if tipo == "Padrao":
            colaborador = ColaboradorPadrao(
                matricula, nome, float(dados.get("salario_base", 0))
            )
        elif tipo == "Comissionado":
            colaborador = ColaboradorComissionado(
                matricula,
                nome,
                float(dados.get("salario_base", 0)),
                float(dados.get("vendas", 0)),
                float(dados.get("comissao_pct", 0)),
            )
        elif tipo == "Producao":
            colaborador = ColaboradorProducao(
                matricula,
                nome,
                int(dados.get("qtd_produzida", 0)),
                float(dados.get("valor_unidade", 0)),
            )
        else:
            return jsonify({"erro": "Tipo de colaborador inválido."}), 400

        sistema.cadastrar(colaborador)
    except (TypeError, ValueError):
        return jsonify({"erro": "Os campos numéricos devem conter valores válidos."}), 400
    except ValidacaoError as erro:
        return jsonify({"erro": str(erro)}), 400

    return jsonify({"mensagem": "Colaborador cadastrado com sucesso."}), 201


@app.delete("/api/colaboradores/<matricula>")
def excluir_colaborador(matricula):
    try:
        sistema.excluir(matricula)
    except ValidacaoError as erro:
        return jsonify({"erro": str(erro)}), 404
    return jsonify({"mensagem": "Colaborador excluído com sucesso."})


if __name__ == "__main__":
    app.run(debug=True)
