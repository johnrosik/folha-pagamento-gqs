# Relatório Final de Qualidade

**Projeto:** Financy, Sistema de Folha de Pagamento
**Versão avaliada:** ramo `folha-de-pagamento`, commit `73b2f6f`
**Execuções:** 23/11/2026 (suíte, fumaça da API e aceitação) e 26/11/2026 (suíte e cobertura, refeitas)
**Arquivos analisados:** `folhadepagamento.py`, `app.py`, `test_folhadepagamento.py`, `index.html`
**Referência de requisitos:** Documento de Visão e ERS da A1, versão 1.1

## 1. Resumo

A suíte automatizada passa inteira (16 de 16) e cobre 98% do módulo de domínio. A validação contra a ERS v1.1, porém, encontrou três defeitos e uma lacuna de teste:

| ID | Defeito | Requisito | Severidade |
|---|---|---|---|
| D01 | Colaborador por produção calcula o bruto sem o salário base (só quantidade × valor por unidade) | RF004, RN008, CT R01 | Alta |
| D02 | Não existe alteração de cadastro; só a exclusão | RF009 | Alta |
| D03 | Persistência em arquivo JSON; a arquitetura da A1 prevê banco SQLite e o repositório `RepositorioSQLite` | RNF003, Arquitetura, diagramas 3.2 e 3.3 | Média |
| D04 | O teste de produção confere o valor sem salário base (1.800) e passa com o defeito D01 | RF004 | Alta |

Conclusão: o sistema ainda **não está pronto para homologação**. Os defeitos estão no Registro de Defeitos (`10_Qualidade/Registro-de-Defeitos.md`) e devem ser corrigidos antes de uma nova rodada.

## 2. Situação dos requisitos (ERS v1.1)

| Requisito | Evidência de implementação | Evidência de teste | Situação |
|---|---|---|---|
| RF001 Cadastro de colaborador | `SistemaFolha.cadastrar` | `test_cadastra_consulta_e_impede_matricula_duplicada` | Atendido |
| RF002 Cadastro de colaborador padrão | `ColaboradorPadrao` | Cálculo padrão e menu | Atendido |
| RF003 Cadastro de colaborador comissionado | `ColaboradorComissionado` | Cálculo de comissão e menu | Atendido |
| RF004 Cadastro de colaborador por produção | `ColaboradorProducao` não recebe salário base | O teste confere o valor errado (D04) | **Não atendido (D01)** |
| RF005 Consulta e listagem | `SistemaFolha.consultar`, `GET /api/colaboradores` | Consulta existente e inexistente | Atendido |
| RF006 Cálculo de salário | `calcular_salario_bruto` em cada tipo | Testes de cálculo | **Parcial**: correto para padrão e comissionado; errado para produção (D01) |
| RF007 Folha de pagamento individual | `gerar_folha_individual` | Relatório individual e inexistente | Atendido |
| RF008 Emissão de resumo da folha | `emitir_resumo_folha` | Totais do resumo | Atendido (os totais herdam o erro de D01 quando há colaborador de produção) |
| RF009 Alteração e exclusão de cadastros | Só `SistemaFolha.excluir` | Só exclusão | **Parcial (D02)** |
| RF010 Descontos e salário líquido | `calcular_inss`, `calcular_irrf`, `calcular_salario_liquido` | Testes de INSS, IRRF e limite | Atendido |
| RN001 Matrícula única | `cadastrar` | Matrícula duplicada | Atendido |
| RN002 Nome obrigatório | `Colaborador.__init__` | Nome vazio | Atendido |
| RN003 Salário base não negativo | Padrão e comissionado | Casos negativos | Atendido |
| RN004 Vendas não negativas | `ColaboradorComissionado` | Caso negativo | Atendido |
| RN005 Comissão não negativa | `ColaboradorComissionado` | Caso negativo | Atendido |
| RN006 Quantidade produzida não negativa | `ColaboradorProducao` | Caso negativo | Atendido |
| RN007 Valor por unidade não negativo | `ColaboradorProducao` | Caso negativo | Atendido |
| RN008 Cálculo automático do salário final | Métodos de cálculo | Testes de cálculo | **Parcial (D01)** |
| RNF001 Interface amigável e intuitiva | Menu de terminal e página web | Menu testado; página só por fumaça | Atendido |
| RNF002 Validação antes do cálculo | Validações no construtor, `ler_float`, `ler_int`, API | Reentrada e entradas inválidas | Atendido |
| RNF003 Persistência | `salvar_dados` e `carregar_dados` em JSON | Salvar, recarregar e JSON inválido | **Atendido com desvio (D03)** |
| RNF004 Novos tipos sem alterar cálculos | Classe abstrata `Colaborador` e subclasses | Sem teste dedicado; verificado por revisão | Atendido por implementação |

Totais: 22 requisitos (10 RF, 8 RN, 4 RNF). 16 atendidos, 1 atendido com desvio, 4 parciais, 1 não atendido.

## 3. Resultados dos testes

### 3.1 Suíte unitária

| Execução | Comando | Resultado |
|---|---|---|
| 23/11/2026 | `python -m unittest -v` | 16 de 16 aprovados |
| 26/11/2026 | `python -m unittest` | 16 de 16 aprovados |

Atenção: aprovado não significa correto. O teste `test_colaborador_producao_calcula_salario_bruto` espera 1.800 para 120 unidades a R$ 15,00, valor que ignora o salário base exigido pela ERS (D04).

### 3.2 Testes de fumaça da API (23/11/2026)

Feitos em memória com o cliente de teste do Flask: `GET /` (200), `GET /api/colaboradores` (200), `POST /api/colaboradores` (201), `DELETE /api/colaboradores/QA-REPORT` (200). Essas chamadas **não estão no repositório**, então não podem ser repetidas por outra pessoa. Não contam como testes de integração do artefato 12.

### 3.3 Testes de integração

Não há testes de integração automatizados no repositório (API, persistência e fluxo cadastro → folha → resumo). Lacuna do artefato 12.

## 4. Métricas

| Métrica | Resultado | Data |
|---|---:|---|
| Testes unitários executados | 16 | 26/11 |
| Testes unitários aprovados | 16 | 26/11 |
| Cobertura de `folhadepagamento.py` (linhas e ramos) | 98% (223 instruções, 3 não cobertas; 54 ramos, 2 parciais) | 26/11 |
| Cobertura de `app.py` | 0% (nenhum teste importa a API) | 26/11 |
| Testes de aceitação executados | 14 | 23/11 |
| Testes de aceitação aprovados | 13 (TA-06 reprovado, ver `09_Homologacao`) | 23/11, reavaliado em 26/11 |
| Requisitos atendidos | 16 de 22 | 26/11 |
| Defeitos abertos | 4 (D01 a D04) | 26/11 |

A cobertura foi medida só sobre o código do sistema, com `python -m coverage run --branch --source=folhadepagamento,app -m unittest` e `python -m coverage report`. O arquivo de testes não entra na conta, porque cobrir o próprio teste não diz nada sobre o sistema.

## 5. Conclusões e próximos passos

1. Corrigir D01 e D04 juntos: produção passa a receber salário base, e o teste passa a esperar o valor da ERS (CT R01: 1.500 + 500 × 10 = R$ 6.500,00).
2. Corrigir D02: alteração de cadastro no terminal, na API e na página.
3. Decidir D03 em grupo: migrar para SQLite (com script em `06_Banco_Dados`) ou corrigir a arquitetura e os diagramas para JSON.
4. Escrever os testes de integração (artefato 12) e incluir `app.py` na cobertura.
5. Refazer suíte, cobertura e aceitação e atualizar este relatório.
