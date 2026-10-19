# Sistema de Folha de Pagamento

Cadastro de colaboradores padrão, comissionados e por produção, com cálculo automático da remuneração, folha individual e resumo consolidado da folha.

Trabalho Integrador (A1 e A3) da unidade curricular Garantia da Qualidade de Software.

## Equipe

| Nome | GitHub | Papel |
|---|---|---|
| João Rosiak | [@johnrosik](https://github.com/johnrosik) | Desenvolvimento: arquitetura, código, testes automatizados, manual técnico |
| Mariana Hammel | [@iraMlemmaH](https://github.com/iraMlemmaH) | Requisitos, UML, casos de teste, manual do usuário, relatórios |
| Iago | [@IFTnomai](https://github.com/IFTnomai) | Gestão: planejamento, PGQ, plano de testes, defeitos, métricas, atas |
| Ana Clara Gomes | [@anaclaraSFG](https://github.com/anaclaraSFG) | Visão, casos de teste, testes de aceitação, homologação, apresentação |

## Como o trabalho está organizado

| O quê | Onde |
|---|---|
| Documentos (Visão, ERS, Arquitetura, PGQ, Plano de Testes, Casos de Teste, manuais, relatórios) | Google Doc do grupo, com uma guia para a A1 e outra para a A3. Na entrega, cada documento vira PDF na pasta correspondente |
| Tarefas, responsáveis e prazos | [Issues](https://github.com/johnrosik/folha-pagamento-gqs/issues), uma por artefato, com a etiqueta `dono:` |
| Quadro e cronograma | [GitHub Projects](https://github.com/users/johnrosik/projects/3) |
| Defeitos | Issues com a etiqueta `bug`, severidade e prioridade |
| Código | Este repositório, por Pull Request revisado por outro integrante |

## Estrutura de pastas

| Pasta | Conteúdo |
|---|---|
| `01_Requisitos` | Documento de Visão, ERS, matriz de rastreabilidade |
| `02_Analise` | Diagramas UML (PlantUML e imagens) |
| `03_Projeto` | Documento de Arquitetura |
| `04_Testes` | Plano de Testes, casos de teste, relatórios de execução e cobertura |
| `05_Codigo_Fonte` | Código do sistema |
| `06_Banco_Dados` | Script de criação do banco SQLite |
| `07_Executavel` | Instruções e script para executar o sistema |
| `08_Manuais` | Manual do Usuário e Manual Técnico |
| `09_Homologacao` | Testes de aceitação e Termo de Homologação |
| `10_Qualidade` | PGQ, registro de defeitos, métricas, atas e Relatório Final de Qualidade |
| `11_Apresentacao` | Planejamento do projeto e slides |

## Requisitos de ambiente

- Python 3.12 ou superior
- Navegador atual (Chrome ou Edge), para a interface web

## Como executar

Situação atual (código herdado do T1): só o menu de terminal funciona.

```bash
python 05_Codigo_Fonte/folhadepagamento.py
```

Os dados são gravados em `colaboradores.json`, na pasta de onde o comando foi executado.

Na A3, a persistência passa para SQLite e a página `index.html` passa a ser servida por uma API Flask. As instruções completas de instalação e execução entram aqui quando essa versão estiver no `main`.

## Como rodar os testes

Os testes automatizados (pytest, com cobertura medida por pytest-cov) fazem parte da A3. O comando entra aqui junto com o primeiro teste.

## Como contribuir

1. Pegue a sua issue no quadro e mova para "Fazendo".
2. Crie um ramo a partir do `main`: `feat/<número-da-issue>-descricao`, `fix/...` ou `docs/...`.
3. Faça commits em português, no imperativo, citando a issue: `Valida matrícula duplicada no banco (#12)`.
4. Abra um Pull Request que cite a issue e peça a revisão de outro integrante.
5. Depois da aprovação, mescle sem squash, para o histórico mostrar o trabalho de cada um.

## Entregas

| Avaliação | Data | Conteúdo |
|---|---|---|
| A1 | 20/10/2026, às 19h | Visão, ERS, UML, Arquitetura, PGQ, Plano de Testes, Casos de Teste, Planejamento, Repositório |
| A3 | 01/12/2026 | Sistema, código, testes unitários, de integração e de aceitação, defeitos, métricas, manuais, homologação, relatórios finais |
