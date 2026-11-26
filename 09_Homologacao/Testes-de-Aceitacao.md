# Testes de Aceitação

**Data da execução:** 23/11/2026 (reavaliados contra a ERS v1.1 em 26/11/2026)
**Ambiente:** aplicação Flask executada pelo cliente de teste HTTP
**Versão:** ramo `folha-de-pagamento`, código de `a5f4f8a` (sem mudança de código até `73b2f6f`)
**Escopo:** cadastro, consulta e listagem, exclusão e respostas de validação

## Cenários testados

| ID | Cenário | Resultado esperado | Resultado obtido | Situação |
|---|---|---|---|---|
| TA-01 | Acessar a página inicial `/` | Status 200 e página HTML | Status 200; HTML | Aprovado |
| TA-02 | Consultar colaboradores cadastrados | Status 200 e lista JSON | Status 200; lista JSON | Aprovado |
| TA-03 | Cadastrar colaborador padrão `AT-001`, `Ana Aceitacao`, salário base 2.600 | Status 201 e mensagem de sucesso | Status 201; cadastro realizado | Aprovado |
| TA-04 | Cadastrar de novo a matrícula `AT-001` | Status 400 e erro RN001 | Status 400; RN001 | Aprovado |
| TA-05 | Cadastrar comissionado com salário 2.000, vendas 10.000 e comissão 5% | Status 201; bruto 2.500, INSS 250, IRRF 0, líquido 2.250 | Os mesmos valores | Aprovado |
| TA-06 | Cadastrar colaborador por produção | Pela ERS v1.1 (RF004 e CT R01), o sistema pede salário base, quantidade e valor por unidade; com 1.500 + 500 × 10, bruto R$ 6.500,00 | O sistema não pede salário base; com 120 unidades a R$ 15,00 calculou bruto 1.800 | **Reprovado (D01)** |
| TA-07 | Consultar a lista após os cadastros | Status 200 com matrícula, tipo, bruto e líquido | Status 200; registros listados | Aprovado |
| TA-08 | Cadastrar com nome só de espaços | Status 400 e erro RN002 | Status 400; RN002 | Aprovado |
| TA-09 | Cadastrar padrão com salário base negativo | Status 400 e erro RN003 | Status 400; RN003 | Aprovado |
| TA-10 | Enviar quantidade produzida não numérica | Status 400 e mensagem de campo numérico inválido | Status 400; mensagem correta | Aprovado |
| TA-11 | Excluir `AT-001` | Status 200 e mensagem de exclusão | Status 200; removido | Aprovado |
| TA-12 | Excluir matrícula inexistente | Status 404 e "colaborador não encontrado" | Status 404 | Aprovado |
| TA-13 | Cadastrar com tipo inválido | Status 400 e "tipo inválido" | Status 400 | Aprovado |
| TA-14 | Consultar os dados consolidados | Lista disponível para o total líquido | Total observado R$ 42.498,00 antes da limpeza | Aprovado, com ressalva: o total inclui o valor de produção calculado sem salário base (D01) |

## Cenários que faltam (pela ERS v1.1)

| ID | Cenário | Por que falta |
|---|---|---|
| TA-15 | Alterar o cadastro de um colaborador (CT "P01 alterado": salário 3.000 → 3.500, líquido R$ 2.913,75) | A alteração não existe no sistema (D02) |
| TA-16 | Gerar a folha individual de R01 e conferir bruto 6.500, INSS 650, IRRF 438,75, líquido 5.411,25 | Depende da correção de D01 |

## Resultado

| Indicador | Valor |
|---|---:|
| Cenários executados | 14 |
| Aprovados | 13 |
| Reprovados | 1 (TA-06) |
| Cenários pendentes | 2 (TA-15 e TA-16) |

O sistema **não está apto para homologação** enquanto D01 e D02 estiverem abertos. Depois das correções, executar de novo TA-06, TA-14, TA-15 e TA-16.

Os cadastros temporários dos testes foram removidos da base depois da execução; os colaboradores originais foram preservados.
