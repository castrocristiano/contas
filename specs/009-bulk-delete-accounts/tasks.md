# Tasks: Exclusão em Lote de Contas em Configurações (009-bulk-delete-accounts)

- [x] 1. Spec & Planejamento SDD
  - [x] 1.1 Criar `specs/009-bulk-delete-accounts/spec.md`
  - [x] 1.2 Criar `specs/009-bulk-delete-accounts/plan.md`
  - [x] 1.3 Criar `specs/009-bulk-delete-accounts/tasks.md`
  - [x] 1.4 Criar branch `feature/009-bulk-delete-accounts`

- [x] 2. Interface de Exclusão em Lote no Streamlit
  - [x] 2.1 Adicionar tabela editável/seleção múltipla de contas em Configurações (`app.py`)
  - [x] 2.2 Adicionar opção de exclusão em cascata (force_cascade)
  - [x] 2.3 Implementar botão de exclusão em lote e loop de execução via `UIService.delete_account`
  - [x] 2.4 Implementar mensagens de resumo (contas apagadas/desativadas com sucesso e eventuais erros)

- [x] 3. Testes Unitários e Validação
  - [x] 3.1 Testar chamadas de exclusão em lote
  - [x] 3.2 Executar `uv run ruff check . && uv run ruff format .`
  - [x] 3.3 Executar `uv run pytest -v` (81 testes passando)

- [x] 4. Entrega
  - [x] 4.1 Atualizar documentação SDD para Implemented
  - [x] 4.2 Commit e push para `feature/009-bulk-delete-accounts`
