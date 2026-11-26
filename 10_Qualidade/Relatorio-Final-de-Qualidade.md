# Relatório Final de Qualidade

**Projeto:** Financy, Sistema de Folha de Pagamento
**Versão avaliada:** ramo `a3/correcoes-e-front`
**Data:** 26/11/2026
**Referência de requisitos:** Documento de Visão e ERS da A1, versão 1.1

## 1. Resumo

| Indicador | Primeira validação (26/11, versão `73b2f6f`) | Depois das correções (26/11) |
|---|---|---|
| Testes automatizados | 16 de 16 | 48 de 48 (+15 subtestes) |
| Cobertura (linhas e ramos) | 98% no domínio, 0% na API | 98% no domínio, na API e na interface |
| Requisitos atendidos | 16 de 22 | 21 de 22 (RNF003 atendido com desvio documental, D03) |
| Defeitos abertos | 4 | 1 (D03, decisão do grupo) |
| Testes de aceitação | 13 de 14 | 18 de 18 |

## 2. O que foi corrigido

| Defeito | Correção |
|---|---|
| D01 produção sem salário base | Salário base no domínio, no menu, na API, na interface e no arquivo de dados |
| D02 sem alteração de cadastro | Alteração no domínio, no menu (opção 8), na API (`PUT`) e na interface |
| D04 teste com valor errado | Teste conferindo o CT R01 completo |

Detalhes e verificação: `10_Qualidade/Registro-de-Defeitos.md`.

## 3. O que foi acrescentado

| Item | Onde |
|---|---|
| Interface web em Python puro (NiceGUI), estilo ERP: menu lateral, telas de Colaboradores, Novo colaborador, Folha individual e Resumo; tabela com cabeçalho fixo e busca; validação ao digitar; prévia do cálculo feita pelo próprio domínio; tema escuro | `05_Codigo_Fonte/interface.py` |
| Testes de integração da API | `05_Codigo_Fonte/test_integracao.py` |
| Testes das regras e das telas da interface | `05_Codigo_Fonte/test_interface.py`, `05_Codigo_Fonte/test_telas.py` |
| Scripts de execução | `07_Executavel/` |
| Relatório de execução e cobertura | `04_Testes/Relatorio-de-Execucao-e-Cobertura.md` |

## 4. Situação dos requisitos (ERS v1.1)

| Requisito | Implementação | Situação |
|---|---|---|
| RF001 Cadastro de colaborador | `SistemaFolha.cadastrar`, API `POST`, tela Novo colaborador | Atendido |
| RF002 Colaborador padrão | `ColaboradorPadrao` | Atendido |
| RF003 Colaborador comissionado | `ColaboradorComissionado` | Atendido |
| RF004 Colaborador por produção | `ColaboradorProducao` com salário base | Atendido |
| RF005 Consulta e listagem | `consultar`, API `GET`, tela Colaboradores com busca | Atendido |
| RF006 Cálculo de salário | `calcular_salario_bruto` em cada tipo | Atendido |
| RF007 Folha individual | `gerar_folha_individual`, API `GET /<matrícula>`, tela Folha individual | Atendido |
| RF008 Resumo da folha | `emitir_resumo_folha`, tela Resumo da folha | Atendido |
| RF009 Alteração e exclusão | `alterar`, `excluir`, API `PUT` e `DELETE`, telas | Atendido |
| RF010 Descontos e salário líquido | INSS 10%, IRRF 7,5% acima de 2.259,20 | Atendido |
| RN001 a RN007 | Validação no domínio, repetida na tela ao digitar | Atendidas |
| RN008 Cálculo automático | Métodos de cálculo; a prévia da tela usa o próprio domínio | Atendido |
| RNF001 Interface amigável | Menu de terminal e interface NiceGUI | Atendido |
| RNF002 Validação antes do cálculo | Domínio, API e interface | Atendido |
| RNF003 Persistência | Arquivo JSON | Atendido com desvio (D03) |
| RNF004 Novos tipos sem alterar cálculos | Classe abstrata `Colaborador` | Atendido por implementação |

## 5. Conclusão

O sistema atende aos requisitos funcionais e às regras de negócio da ERS v1.1, com 48 testes automatizados aprovados e 98% de cobertura. Antes da entrega, o grupo precisa decidir o D03: migrar para SQLite ou corrigir a arquitetura para JSON.
