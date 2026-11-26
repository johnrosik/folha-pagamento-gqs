# Relatório Final de Qualidade

**Projeto:** Sistema de Folha de Pagamento
**Data da validação:** 23/11/2026
**Arquivos analisados:** `folhadepagamento.py`, `app.py`, `test_folhadepagamento.py`, `colaboradores.json`

## Relatório Final de Qualidade

O sistema foi executado e submetido a uma suíte automatizada, uma compilação sintática dos módulos Python e testes de fumaça das rotas HTTP. Os resultados demonstram que a implementação atende às regras funcionais e de validação identificadas no código.

Não foram encontrados defeitos nos cenários executados. A suíte apresentou 16 testes aprovados em 16, equivalente a 100% de aprovação. A sintaxe dos três módulos verificados foi aceita pelo compilador Python e todas as rotas HTTP exercitadas responderam conforme o esperado.

## Situação dos requisitos

| Grupo | Situação geral |
|---|---|
| RF001-RF009 | Atendidos pela implementação e cobertos por testes unitários, do menu ou das rotas HTTP |
| RN001-RN008 | Atendidos; validações negativas, unicidade e cálculos têm evidências de execução |
| RNF001-RNF003 | Atendidos e validados por interface ou persistência |
| RNF004 | Estrutura atendida por abstração e especializações, sem teste automatizado específico de substituição/extensão |

**Resumo:** 21 requisitos foram identificados por meio das marcações existentes no código: 9 requisitos funcionais, 8 regras de negócio e 4 requisitos não funcionais. Não houve falha de requisito nos cenários testados.

## Matriz de rastreabilidade

| Requisito | Evidência de implementação | Evidência de teste | Situação |
|---|---|---|---|
| RF001 - Cadastro | `SistemaFolha.cadastrar` em `folhadepagamento.py` | Cadastro e consulta em `test_cadastra_consulta_e_impede_matricula_duplicada` | Atendido |
| RF002 - Colaborador padrão | `ColaboradorPadrao` | Cálculo padrão e execução do menu | Atendido |
| RF003 - Colaborador comissionado | `ColaboradorComissionado` | Cálculo de comissão e cadastro no menu | Atendido |
| RF004 - Colaborador por produção | `ColaboradorProducao` | Cálculo por quantidade/unidade e cadastro no menu | Atendido |
| RF005 - Consulta | `SistemaFolha.consultar` | Consulta existente e matrícula inexistente | Atendido |
| RF006 - Folha individual | `gerar_folha_individual` | Relatório individual contém identificação e valores | Atendido |
| RF007 - Folha individual | `gerar_folha_individual` | Relatório individual e colaborador inexistente | Atendido |
| RF008 - Resumo consolidado | `emitir_resumo_folha` | Totais por quantidade de colaboradores | Atendido |
| RF009 - Exclusão | `SistemaFolha.excluir` | Exclusão válida e rejeição de matrícula inexistente | Atendido |
| RN001 - Matrícula única | Verificação em `cadastrar` | Teste de matrícula duplicada | Atendido |
| RN002 - Nome obrigatório | Validação em `Colaborador` | Teste de nome vazio | Atendido |
| RN003 - Salário não negativo | Validação em tipos mensalista/comissionado | Casos negativos em `test_valores_negativos_sao_rejeitados` | Atendido |
| RN004 - Vendas não negativas | Validação em `ColaboradorComissionado` | Caso negativo no teste parametrizado | Atendido |
| RN005 - Comissão não negativa | Validação em `ColaboradorComissionado` | Caso negativo no teste parametrizado | Atendido |
| RN006 - Quantidade não negativa | Validação em `ColaboradorProducao` | Caso negativo no teste parametrizado | Atendido |
| RN007 - Valor unitário não negativo | Validação em `ColaboradorProducao` | Caso negativo no teste parametrizado | Atendido |
| RN008 - Cálculo automático | Métodos bruto, INSS, IRRF e líquido | Testes de cálculo, limite do IRRF e relatórios | Atendido |
| RNF001 - Interface CLI | Função `menu` | Execução das opções pelo teste do menu | Atendido |
| RNF002 - Tratamento de entrada | `ler_float` e `ler_int` | Reentrada após valores inválidos | Atendido |
| RNF003 - Persistência JSON | `salvar_dados` e `carregar_dados` | Salvamento e recarga dos três tipos; JSON inválido | Atendido |
| RNF004 - Open/Closed | Classe abstrata `Colaborador` e especializações | Estrutura verificada por revisão; sem caso dedicado | Atendido por implementação |

## Resultados dos testes

### Suíte unitária

Comando executado:

```text
python -m unittest -v
```

Resultado:

```text
Ran 16 tests in 0.148s
OK
```

Todos os 16 testes passaram. Os testes cobrem cálculos, validações, persistência, relatórios, tratamento de erros, funcionamento do menu e leitura de entradas.

### Verificação sintática

Comando executado:

```text
python -m py_compile folhadepagamento.py app.py test_folhadepagamento.py
```

Resultado: nenhum erro de sintaxe encontrado nos três arquivos.

### Testes de fumaça da API

As chamadas foram realizadas em memória com o cliente de teste do Flask:

- `GET /`: status 200 e conteúdo HTML.
- `GET /api/colaboradores`: status 200, resposta JSON e três colaboradores existentes.
- `POST /api/colaboradores`: status 201 e mensagem de sucesso.
- `DELETE /api/colaboradores/QA-REPORT`: status 200 e mensagem de exclusão.

O registro temporário criado pelo teste foi excluído e o arquivo `colaboradores.json` permaneceu com seus três registros originais.

## Métricas

| Métrica | Resultado |
|---|---:|
| Testes executados | 16 |
| Testes aprovados | 16 |
| Testes reprovados | 0 |
| Taxa de aprovação | 100% |
| Requisitos rastreados | 21 |
| Requisitos identificados como atendidos | 21 |
| Módulos com sintaxe validada | 3 |
| Chamadas HTTP de fumaça | 4 |
| Chamadas HTTP aprovadas | 4 |
| Defeitos encontrados nesta execução | 0 |
| Cobertura percentual instrumentada | Não medida |

## Evidências

- Resultado da suíte: 16 testes executados e aprovados em 0,148 segundos.
- Resultado da compilação: três módulos Python aceitos sem erro.
- Evidência da API: respostas HTTP 200/200/201/200 nas operações de leitura, cadastro e exclusão.
- Implementação rastreável em `folhadepagamento.py` e `app.py`.
- Casos automatizados rastreáveis em `test_folhadepagamento.py`.
- Base de dados atual preservada em `colaboradores.json`.

Não houve cálculo automático de cobertura de linhas; a métrica de 100% refere-se ao resultado dos testes executados, não à cobertura estrutural.

## Conclusões

O Sistema de Folha de Pagamento apresenta execução estável nos cenários automatizados e de fumaça avaliados. Os cálculos de salário, descontos, validações negativas, cadastro, consulta, exclusão, persistência JSON e interface de menu demonstraram comportamento correto.

A API web também respondeu adequadamente para consulta, cadastro e exclusão. A estrutura orientada a abstrações utilizada no domínio está coerente com o princípio de extensão previsto em RNF004.

Como limitação de validação, não foi medido percentual de cobertura de código e não existe, nesta execução, um teste específico que demonstre a extensão da hierarquia com uma nova classe sem alterar o código existente. Recomenda-se, em uma próxima rodada, adicionar a métrica de cobertura e um teste dirigido ao princípio de Open/Closed.

# Testes de Aceitação

**Data da execução:** 23/11/2026
**Ambiente:** aplicação Flask executada pelo cliente de teste HTTP
**Escopo:** cadastro, consulta/listagem, exclusão e respostas de validação

## Cenários testados

| ID | Cenário testado | Resultado esperado | Resultado obtido | Situação final |
|---|---|---|---|---|
| TA-01 | Acessar a página inicial `/` | Status HTTP 200 e página HTML | Status 200; conteúdo HTML | Aprovado |
| TA-02 | Consultar colaboradores cadastrados | Status 200 e lista JSON dos colaboradores | Status 200; JSON com os colaboradores existentes | Aprovado |
| TA-03 | Cadastrar colaborador padrão com matrícula `AT-001`, nome `Ana Aceitacao` e salário base `2600` | Status 201 e mensagem de sucesso | Status 201; mensagem de cadastro realizado | Aprovado |
| TA-04 | Tentar cadastrar novamente a matrícula `AT-001` | Status 400 e erro RN001 de matrícula única | Status 400; RN001 foi informado | Aprovado |
| TA-05 | Cadastrar colaborador comissionado com salário `2000`, vendas `10000` e comissão `5%` | Status 201, bruto `2500` e cadastro persistido | Status 201; bruto calculado como `2500`, INSS `250`, IRRF `0` e líquido `2250` | Aprovado |
| TA-06 | Cadastrar colaborador por produção com quantidade `120` e valor unitário `15` | Status 201, bruto `1800` e cadastro persistido | Status 201; bruto calculado como `1800`, INSS `180`, IRRF `0` e líquido `1620` | Aprovado |
| TA-07 | Consultar a lista após os cadastros | Status 200 com matrícula, tipo, salário bruto e líquido dos registros | Status 200; os três registros de teste apareceram com seus valores calculados | Aprovado |
| TA-08 | Cadastrar colaborador com nome composto somente por espaços | Status 400 e mensagem RN002 | Status 400; erro RN002 informado | Aprovado |
| TA-09 | Cadastrar colaborador padrão com salário base negativo | Status 400 e mensagem RN003 | Status 400; erro RN003 informado | Aprovado |
| TA-10 | Enviar quantidade produzida não numérica | Status 400 e mensagem indicando campos numéricos inválidos | Status 400; mensagem de campos numéricos inválidos | Aprovado |
| TA-11 | Excluir colaborador existente `AT-001` | Status 200 e mensagem de exclusão | Status 200; registro removido com sucesso | Aprovado |
| TA-12 | Excluir matrícula inexistente | Status 404 e mensagem de colaborador não encontrado | Status 404; colaborador não encontrado | Aprovado |
| TA-13 | Cadastrar colaborador com tipo inválido | Status 400 e mensagem de tipo inválido | Status 400; tipo inválido informado | Aprovado |
| TA-14 | Consultar dados consolidados após a execução | Lista disponível para cálculo do total líquido da folha | Foram obtidos os valores líquidos dos registros da base e dos registros temporários; total observado `42498.00` antes da limpeza | Aprovado |

## Resultado dos testes de aceitação

- Cenários executados: 14
- Cenários aprovados: 14
- Cenários reprovados: 0
- Taxa de aprovação: 100%

Os cenários confirmaram o fluxo principal da interface de dados: acesso à página, listagem, cadastro das três categorias, rejeição de dados inválidos, exclusão e cálculo dos valores da folha.

Os testes de cadastro temporários foram removidos da base compartilhada após a execução. Os colaboradores originais foram preservados. A mensagem obtida para matrícula duplicada e os textos com acentuação apresentados pelo terminal podem variar na codificação da saída, mas os códigos HTTP e os erros de regra foram validados corretamente.

# Métricas e Indicadores de Qualidade

**Data da execução:** 23/11/2026
**Comandos executados:** `python -m unittest -v` e `python -m coverage run -m unittest -v`

## Cobertura de testes

| Indicador | Resultado |
|---|---:|
| Testes unitários executados | 16 |
| Testes unitários aprovados | 16 |
| Testes unitários reprovados | 0 |
| Taxa de aprovação unitária | 100% |
| Testes de aceitação executados anteriormente | 14 |
| Testes de aceitação aprovados | 14 |
| Taxa de aprovação de aceitação | 100% |
| Linhas analisadas pela cobertura | 345 |
| Linhas não executadas | 4 |
| Cobertura geral do conjunto analisado | 99% |
| Cobertura de `folhadepagamento.py` | 223 instruções, 3 não cobertas, 99% |
| Cobertura de `test_folhadepagamento.py` | 122 instruções, 1 não coberta, 99% |

As instruções não cobertas foram a execução direta dos dois métodos abstratos, o bloco `if __name__ == "__main__"` da aplicação principal e o bloco equivalente do arquivo de testes. Esses pontos são métodos abstratos ou inicializadores de execução direta, não fluxos incompletos observados durante os testes.

## Defeitos encontrados

Nenhum defeito funcional foi encontrado nos 16 testes unitários e nos 14 testes de aceitação executados.

Também não foram observados defeitos nas verificações realizadas:

- erros de cálculo;
- falha de validação;
- falha de cadastro ou consulta;
- falha de exclusão;
- falha de persistência;
- falha de leitura de entradas;
- falha de resposta nas rotas HTTP verificadas.

## Defeitos corrigidos

Não houve defeitos de software a corrigir nesta rodada. Não foram realizadas alterações no código funcional do sistema.

Foram removidos da base JSON os colaboradores temporários criados pelos testes de aceitação. Essa limpeza não constitui correção de defeito, mas preservação dos dados originais.

## Casos aprovados

- 16 testes unitários aprovados.
- 14 testes de aceitação aprovados.
- 30 casos automatizados aprovados no total entre as duas classificações.
- Taxa geral de aprovação registrada: 100%.
- Nenhum caso unitário ou de aceitação ficou reprovado.

## Requisitos atendidos

| Tipo | Requisitos identificados | Situação |
|---|---:|---|
| Requisitos funcionais RF001-RF009 | 9 | Atendidos |
| Regras de negócio RN001-RN008 | 8 | Atendidos |
| Requisitos não funcionais RNF001-RNF004 | 4 | Atendidos |
| Total | 21 | 21 atendidos |

Os resultados cobrem requisitos de cadastro, consulta, exclusão, relatório, persistência, validações, cálculo da folha, interface, tratamento de entrada e estrutura extensível.

## Conclusão dos indicadores

O sistema apresentou qualidade consistente no conjunto avaliado: 99% de cobertura instrumentada nos módulos medidos, 100% dos testes executados aprovados e nenhum defeito confirmado. O indicador principal a ampliar em ciclos futuros é a cobertura dos pontos de execução direta e da camada web `app.py`, sem alterar o resultado atual dos testes.
