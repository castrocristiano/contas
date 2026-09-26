# Tasks: Selecionar Tudo e Ordenação de Colunas em Tabelas (010-table-select-all-and-sort)

- [x] 1. Spec & Planejamento SDD
  - [x] 1.1 Criar `specs/010-table-select-all-and-sort/spec.md`
  - [x] 1.2 Criar `specs/010-table-select-all-and-sort/plan.md`
  - [x] 1.3 Criar `specs/010-table-select-all-and-sort/tasks.md`
  - [x] 1.4 Criar branch `feature/010-table-select-all-and-sort`

- [x] 2. Tabela de Extrato de Movimentações (Dashboard)
  - [x] 2.1 Adicionar controles "Selecionar Tudo" / "Desmarcar Tudo" para o extrato
  - [x] 2.2 Migrar visualização de `st.dataframe` para `st.data_editor` com ordenação por coluna e tipos numéricos
  - [x] 2.3 Permitir exclusão em lote de transações selecionadas

- [x] 3. Tabela de Importação de Fatura PDF
  - [x] 3.1 Adicionar controles "Selecionar Tudo" / "Desmarcar Tudo" antes da tabela de despesas
  - [x] 3.2 Garantir ordenação numérica por coluna de valor e ordenação por data/descrição

- [x] 4. Tabela de Gerenciamento de Contas (Configurações)
  - [x] 4.1 Adicionar controles "Selecionar Tudo" / "Desmarcar Tudo"
  - [x] 4.2 Garantir ordenação por qualquer coluna com consistência de tipos

- [x] 5. Testes e Validação
  - [x] 5.1 Atualizar suíte de testes unitários (test_ui_service_bulk_delete_transactions)
  - [x] 5.2 Executar `uv run ruff check . && uv run ruff format .`
  - [x] 5.3 Executar `uv run pytest -v` (84 testes passando)
  - [x] 5.4 Commit e push da branch
