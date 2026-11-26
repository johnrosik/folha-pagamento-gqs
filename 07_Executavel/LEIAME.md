# Como executar o Financy

Requisito: Python 3.11 ou mais novo.

| Sistema | Comando | O que abre |
|---|---|---|
| Windows | dar dois cliques em `executar.bat` | Interface web em http://localhost:8080 |
| Linux ou macOS | `sh executar.sh` | Interface web em http://localhost:8080 |

Na primeira execução o script cria um ambiente virtual em `05_Codigo_Fonte/.venv` e instala as dependências de `requirements.txt`.

## Outras formas de usar

| Modo | Comando, dentro de `05_Codigo_Fonte` |
|---|---|
| Menu de terminal | `python folhadepagamento.py` |
| API REST (Flask) | `python app.py` (http://127.0.0.1:5000) |

## Testes

```
pip install -r requirements.txt -r requirements-dev.txt
python -m coverage run --branch --source=folhadepagamento,app,interface -m pytest
python -m coverage report -m
```
