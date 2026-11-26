# Registro de Defeitos

**Versão avaliada:** ramo `folha-de-pagamento`, commit `73b2f6f`
**Data do registro:** 26/11/2026
**Referência:** ERS v1.1 da A1 e casos de teste CT001 a CT024

| ID | Descrição | Como reproduzir | Esperado | Obtido | Requisito | Severidade | Prioridade | Responsável | Estado |
|---|---|---|---|---|---|---|---|---|---|
| D01 | Colaborador por produção sem salário base | Cadastrar colaborador por produção pelo menu, pela API ou pela página | O sistema pede salário base e calcula bruto = salário base + quantidade × valor por unidade (CT R01: 1.500 + 500 × 10 = 6.500) | Não pede salário base; bruto = quantidade × valor (`folhadepagamento.py:106-119`) | RF004, RF006, RN008 | Alta | Alta | Desenvolvimento | Aberto |
| D02 | Alteração de cadastro inexistente | Procurar a opção de alterar no menu, na API e na página | Alterar os dados de um colaborador e recalcular a folha (CT "P01 alterado": salário 3.500, líquido 2.913,75) | Só existe exclusão | RF009 | Alta | Alta | Desenvolvimento | Aberto |
| D03 | Persistência diverge da arquitetura | Comparar o código com a Arquitetura da A1 e os diagramas 3.2 e 3.3 | Banco SQLite por `RepositorioSQLite`, com script em `06_Banco_Dados` | Arquivo `colaboradores.json`; `06_Banco_Dados` vazio | RNF003 | Média | Média | Grupo decide: código ou documento | Aberto |
| D04 | Teste de produção confere valor errado | Ler `test_folhadepagamento.py:42-45` | Esperar o bruto com salário base, como na ERS | Espera 1.800 (120 × 15), sem base; passa com D01 presente | RF004 | Alta | Alta | Desenvolvimento | Aberto |

## Como fechar cada defeito

| ID | Fecha quando |
|---|---|
| D01 | Produção recebe salário base no domínio, na API, na página e no JSON, e o CT R01 dá R$ 6.500,00 |
| D02 | A alteração existe no terminal, na API e na página, e o CT "P01 alterado" dá líquido R$ 2.913,75 |
| D03 | O código grava em SQLite com script em `06_Banco_Dados`, ou a Arquitetura e os diagramas passam a dizer JSON |
| D04 | O teste espera o valor da ERS e fica vermelho se o salário base for removido do cálculo |
