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

- [x] 3. Suporte a Exclusão em Lote via Chat com Confirmação
  - [x] 3.1 Atualizar schema `delete_account` em `financial_chat.py` para aceitar `account_names`
  - [x] 3.2 Atualizar `execute_pending_action` para processar lista de contas com feedback consolidado
  - [x] 3.3 Atualizar `_build_action_summary` para exibir resumo de exclusão em lote com nomes das contas
  - [x] 3.4 Instruir o `SYSTEM_PROMPT` para comandos de exclusão de múltiplas contas

- [x] 4. Feedback Visual e Observabilidade no Chat
  - [x] 4.1 Adicionar `st.spinner` durante processamento do assistente financeiro (`app.py`)
  - [x] 4.2 Adicionar logging estruturado em `financial_chat.py` (iterações, tool calls, pending actions)
  - [x] 4.3 Adicionar logging estruturado em `app.py` (mensagens de chat, confirmações, cancelamentos)
  - [x] 4.4 Adicionar notificações `st.toast` após confirmação, cancelamento ou erro de ações no chat

- [x] 5. Testes Unitários e Validação
  - [x] 5.1 Testar chamadas de exclusão em lote no `UIService`
  - [x] 5.2 Testar `execute_pending_action` e resumo no chat para lote de contas
  - [x] 5.3 Testar logging do fluxo de chat em `tests/unit/test_financial_chat.py` com `caplog`
  - [x] 5.4 Executar `uv run ruff check . && uv run ruff format .`
  - [x] 5.5 Executar `uv run pytest -v` (83 testes passando)

- [x] 6. Entrega
  - [x] 6.1 Atualizar documentação SDD para Implemented (`spec.md`, `plan.md`, `tasks.md`)
  - [x] 6.2 Commit e push para `feature/009-bulk-delete-accounts`

