-- Financy: criação do banco SQLite (RNF003).
-- O sistema executa este mesmo comando na primeira vez que abre o arquivo financy.db
-- (constante ESQUEMA em 05_Codigo_Fonte/folhadepagamento.py). As restrições repetem as
-- regras de negócio no próprio banco: RN001 (matrícula única), RN002 (nome obrigatório)
-- e RN003 a RN007 (valores não negativos).

CREATE TABLE IF NOT EXISTS colaboradores (
    matricula     TEXT PRIMARY KEY,
    tipo          TEXT NOT NULL CHECK (tipo IN ('Padrao', 'Comissionado', 'Producao')),
    nome          TEXT NOT NULL CHECK (length(trim(nome)) > 0),
    salario_base  REAL NOT NULL DEFAULT 0 CHECK (salario_base >= 0),
    vendas        REAL CHECK (vendas >= 0),
    comissao_pct  REAL CHECK (comissao_pct >= 0),
    qtd_produzida INTEGER CHECK (qtd_produzida >= 0),
    valor_unidade REAL CHECK (valor_unidade >= 0)
);
