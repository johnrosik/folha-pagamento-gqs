import pytest

from folhadepagamento import ColaboradorComissionado, ColaboradorPadrao, SistemaFolha

pytest_plugins = ["nicegui.testing.user_plugin"]


@pytest.fixture(autouse=True)
def dados_temporarios(tmp_path, monkeypatch):
    """As telas sempre usam um banco SQLite temporário; o financy.db real nunca é tocado."""
    banco = tmp_path / "financy.db"
    sistema = SistemaFolha(str(banco))
    sistema.cadastrar(ColaboradorPadrao("P01", "Paula Souza", 3000.0))
    sistema.cadastrar(ColaboradorComissionado("C01", "Caio Martins", 2000.0, 10000.0, 5.0))
    monkeypatch.setenv("FINANCY_DADOS", str(banco))
    return banco
