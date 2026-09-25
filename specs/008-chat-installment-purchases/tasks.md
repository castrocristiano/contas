# Tasks: Registro e Gestão de Compras Parceladas via Chat (008-chat-installment-purchases)

- [x] 1. Spec & Planejamento SDD
  - [x] 1.1 Criar `specs/008-chat-installment-purchases/spec.md`
  - [x] 1.2 Criar `specs/008-chat-installment-purchases/plan.md`
  - [x] 1.3 Criar `specs/008-chat-installment-purchases/tasks.md`
  - [x] 1.4 Criar branch `feature/008-chat-installment-purchases`

- [x] 2. Schema de Ferramentas e Prompt
  - [x] 2.1 Adicionar `total_installments` e `total_amount` ao schema `record_transaction` em `financial_chat.py`
  - [x] 2.2 Atualizar diretrizes de compras parceladas no `SYSTEM_PROMPT` de `financial_chat.py`

- [x] 3. Lógica de Execução e Resumo
  - [x] 3.1 Atualizar `execute_pending_action` para repassar `total_installments` e `total_amount` para `UIService.record_transaction`
  - [x] 3.2 Atualizar `_build_action_summary` para exibir compra parcelada com detalhes de parcelas e total

- [x] 4. Testes Unitários
  - [x] 4.1 Adicionar teste para `execute_pending_action` com compra parcelada
  - [x] 4.2 Adicionar teste para `_build_action_summary` com compra parcelada
  - [x] 4.3 Executar `uv run pytest -v` (todos os testes passando com mocks)

- [x] 5. Validação e Entrega
  - [x] 5.1 Executar `uv run ruff check . && uv run ruff format .`
  - [x] 5.2 Executar `uv run pytest -v` (80 testes passando)
  - [x] 5.3 Atualizar tasks.md e documentação SDD
  - [x] 5.4 Commit e push na branch `feature/008-chat-installment-purchases`
