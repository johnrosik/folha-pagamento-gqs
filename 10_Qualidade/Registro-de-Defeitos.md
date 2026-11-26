# Registro de Defeitos

**Referência:** ERS v1.1 da A1 e casos de teste CT001 a CT024
**Aberto em:** 26/11/2026, na versão `73b2f6f` do ramo `folha-de-pagamento`
**Atualizado em:** 26/11/2026, na versão do ramo `a3/correcoes-e-front`

| ID | Descrição | Requisito | Severidade | Estado | Correção | Como foi verificado |
|---|---|---|---|---|---|---|
| D01 | Colaborador por produção sem salário base (bruto = quantidade × valor) | RF004, RF006, RN008 | Alta | **Fechado** | `ColaboradorProducao` recebe e valida o salário base; bruto = base + quantidade × valor; menu, API, interface e JSON atualizados; registro antigo sem o campo carrega com 0 | CT R01 dá 6.500 / 5.411,25 no domínio, na API e na tela; controle negativo deixou 4 testes vermelhos |
| D02 | Alteração de cadastro inexistente | RF009 | Alta | **Fechado** | `SistemaFolha.alterar`, opção 8 do menu, `PUT /api/colaboradores/<matrícula>`, tela "Alterar" na interface | CT "P01 alterado" dá 2.913,75; controle negativo deixou 4 testes vermelhos |
| D03 | Persistência em JSON; a arquitetura da A1 prevê SQLite | RNF003 | Média | **Aberto: decisão do grupo** | Duas saídas: migrar o código para SQLite com script em `06_Banco_Dados`, ou corrigir a Arquitetura e os diagramas 3.2 e 3.3 para JSON | Pendente |
| D04 | Teste de produção esperava 1.800, sem salário base | RF004 | Alta | **Fechado** | O teste usa o CT R01 e confere bruto, INSS, IRRF e líquido | Fica vermelho quando o salário base sai do cálculo |
