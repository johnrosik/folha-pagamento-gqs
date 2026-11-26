# Testes de Aceitação

**1ª execução:** 23/11/2026, pela API Flask (cliente de teste HTTP), versão `a5f4f8a`
**2ª execução:** 26/11/2026, depois das correções de D01 e D02, ramo `a3/correcoes-e-front`, pela API e pela interface NiceGUI
**Escopo:** cadastro, consulta e listagem, alteração, exclusão, folha individual, resumo e validações

## Cenários

| ID | Cenário | Resultado esperado | 1ª execução (23/11) | 2ª execução (26/11) |
|---|---|---|---|---|
| TA-01 | Abrir a página inicial | Página carrega | Aprovado | Aprovado (API e interface) |
| TA-02 | Consultar colaboradores cadastrados | Lista com os valores da folha | Aprovado | Aprovado |
| TA-03 | Cadastrar padrão com salário base 2.600 | Cadastro realizado | Aprovado | Aprovado |
| TA-04 | Cadastrar matrícula repetida | Recusa com RN001 | Aprovado | Aprovado; a interface avisa enquanto a matrícula é digitada |
| TA-05 | Comissionado 2.000, vendas 10.000, 5% | Bruto 2.500, líquido 2.250 | Aprovado | Aprovado |
| TA-06 | Produção com salário base 1.500, 500 unidades a R$ 10,00 (CT R01) | Bruto 6.500, INSS 650, IRRF 438,75, líquido 5.411,25 | Reprovado (D01: sem salário base) | **Aprovado** |
| TA-07 | Lista após os cadastros | Registros com tipo, bruto e líquido | Aprovado | Aprovado |
| TA-08 | Nome só com espaços | Recusa com RN002 | Aprovado | Aprovado; a interface marca o campo |
| TA-09 | Salário base negativo | Recusa com RN003 | Aprovado | Aprovado, também para produção |
| TA-10 | Quantidade não numérica | Recusa por campo numérico inválido | Aprovado | Aprovado |
| TA-11 | Excluir colaborador existente | Registro removido | Aprovado | Aprovado; a interface pede confirmação |
| TA-12 | Excluir matrícula inexistente | "Colaborador não encontrado" | Aprovado | Aprovado |
| TA-13 | Tipo inválido | Recusa por tipo inválido | Aprovado | Aprovado |
| TA-14 | Resumo consolidado com P01, C01 e R01 (CT019) | Bruto 12.000, INSS 1.200, IRRF 641,25, líquido 10.158,75 | Aprovado com ressalva (produção sem base) | **Aprovado** |
| TA-15 | Alterar P01 de 3.000 para 3.500 | Líquido 2.913,75, gravado no arquivo | Não executável (D02) | **Aprovado** |
| TA-16 | Folha individual de R01 | Bruto 6.500, líquido 5.411,25 | Não executável (D01) | **Aprovado** |
| TA-17 | Cadastro vazio na interface | Matrícula, nome e salário base marcados como obrigatórios ao mesmo tempo | Não existia | **Aprovado** |
| TA-18 | Autocorreção de digitação | Espaços nas pontas da matrícula e espaços repetidos no nome são removidos ao sair do campo | Não existia | **Aprovado** (verificado no navegador) |

## Resultado

| Indicador | 23/11 | 26/11 |
|---|---:|---:|
| Cenários executados | 14 | 18 |
| Aprovados | 13 | 18 |
| Reprovados | 1 | 0 |

Os cenários TA-01 a TA-17 são cobertos pelos testes automatizados de `test_integracao.py` e `test_telas.py` (mesmas regras e valores). O TA-18 foi conferido no navegador em 26/11/2026.

O sistema está apto para homologação. O D03 foi fechado: os dados ficam no banco SQLite `financy.db`.
