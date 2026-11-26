import json

import pytest

pytest_plugins = ["nicegui.testing.user_plugin"]

COLABORADORES = [
    {"tipo": "Padrao", "matricula": "P01", "nome": "Paula Souza", "salario_base": 3000.0},
    {"tipo": "Comissionado", "matricula": "C01", "nome": "Caio Martins", "salario_base": 2000.0, "vendas": 10000.0, "comissao_pct": 5.0},
]


@pytest.fixture(autouse=True)
def dados_temporarios(tmp_path, monkeypatch):
    """As telas sempre usam um arquivo temporário; o colaboradores.json real nunca é tocado."""
    arquivo = tmp_path / "colaboradores.json"
    arquivo.write_text(json.dumps(COLABORADORES), encoding="utf-8")
    monkeypatch.setenv("FINANCY_DADOS", str(arquivo))
    return arquivo
