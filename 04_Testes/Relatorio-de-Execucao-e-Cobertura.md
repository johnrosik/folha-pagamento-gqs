# Relatório de Execução e Cobertura de Testes

**Data da execução:** 26/11/2026 01h56
**Versão:** ramo `a3/correcoes-e-front`
**Ambiente:** Windows 11, Python 3.15.1, pytest 9.2.0, coverage 7.17.5, Flask 3.1.3, NiceGUI 4.1.0
**Evidências brutas:** `04_Testes/evidencias/execucao-2026-11-26.txt` e `04_Testes/evidencias/cobertura-2026-11-26.txt`

## Comandos

Dentro de `05_Codigo_Fonte`:

```
pip install -r requirements.txt -r requirements-dev.txt
python -m coverage run --branch --source=folhadepagamento,app,interface -m pytest -v
python -m coverage report -m
```

## Resultado da execução

| Conjunto | Arquivo | Tipo | Testes | Aprovados |
|---|---|---|---:|---:|
| Domínio, persistência, menu e leitura de entradas | `test_folhadepagamento.py` | Unitário | 19 | 19 |
| API REST com arquivo temporário | `test_integracao.py` | Integração | 10 | 10 |
| Regras da interface (validação, formatação, resumo) | `test_interface.py` | Unitário | 8 | 8 |
| Telas com usuário simulado | `test_telas.py` | Integração de interface | 11 | 11 |
| **Total** | | | **48** | **48** |

Mais 15 subtestes (casos negativos das regras RN001 a RN007), todos aprovados. Tempo total: 2,83 s.

## Cobertura (linhas e ramos)

| Módulo | Instruções | Não cobertas | Ramos | Ramos parciais | Cobertura |
|---|---:|---:|---:|---:|---:|
| `folhadepagamento.py` | 248 | 4 | 66 | 3 | 98% |
| `app.py` | 73 | 1 | 18 | 1 | 98% |
| `interface.py` | 234 | 5 | 36 | 1 | 98% |
| **Total** | **555** | **10** | **120** | **5** | **98%** |

Meta do plano de testes: 80%. Atingida.

Os arquivos de teste não entram na conta. As linhas não cobertas são os corpos vazios dos métodos abstratos, os blocos `if __name__ == "__main__"` e o aviso de colaborador não encontrado na folha individual por matrícula digitada à mão.

## Controle negativo

Cada correção foi quebrada de propósito para provar que os testes a vigiam:

| Quebra feita de propósito | Testes que ficaram vermelhos |
|---|---|
| Produção sem o salário base no cálculo (D01) | 4: produção do domínio, menu, cadastro dos três tipos pela API, resumo consolidado |
| `alterar` sem trocar o registro (D02) | 4: alteração no domínio, menu, alteração pela API, matrícula ignorada no corpo |
| Validação de nome obrigatório desligada na interface | 2: regra do nome e tela de cadastro vazio |

Depois de cada quebra o código foi restaurado e a suíte voltou a 48 de 48.

## Rastreabilidade com os casos de teste da A1

| Caso de teste | Valores esperados | Testes que conferem |
|---|---|---|
| P01 padrão 3.000 | líquido 2.497,50 | integração, interface, telas |
| C01 comissionado 2.000 + 5% de 10.000 | bruto 2.500, líquido 2.250 | integração, interface, telas |
| R01 produção 1.500 + 500 × 10 | bruto 6.500, IRRF 438,75, líquido 5.411,25 | domínio, integração, interface, telas |
| P01 alterado para 3.500 | líquido 2.913,75 | domínio, integração, telas |
| CT019 resumo (P01, C01, R01) | bruto 12.000, INSS 1.200, IRRF 641,25, líquido 10.158,75 | integração, interface |
