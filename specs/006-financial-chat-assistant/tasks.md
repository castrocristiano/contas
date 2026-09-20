# Tasks: Assistente Financeiro por Chat (006-financial-chat-assistant)

- [x] 1. Spec & Planejamento
  - [x] 1.1 Criar `specs/006-financial-chat-assistant/spec.md`
  - [x] 1.2 Criar `specs/006-financial-chat-assistant/plan.md`
  - [x] 1.3 Criar `specs/006-financial-chat-assistant/tasks.md`
  - [x] 1.4 Criar branch `feature/006-financial-chat`

- [x] 2. UIService — Método Faltante
  - [x] 2.1 Adicionar `UIService.get_financial_summary(month, year)` em `src/contas/ui/services.py`

- [x] 3. Serviço de Chat
  - [x] 3.1 Criar `src/contas/services/financial_chat.py`
    - [x] 3.1.1 Definir `_TOOLS` (schemas JSON das 7 ferramentas: leitura + `record_transaction` + `create_account`)
    - [x] 3.1.2 Implementar `@dataclass PendingAction`
    - [x] 3.1.3 Implementar `_execute_read_tool()`
    - [x] 3.1.4 Implementar `execute_pending_action()` com suporte a `record_transaction` e `create_account`
    - [x] 3.1.5 Implementar `chat_with_financial_assistant()` com loop agentic (máx. 6 iterações)
    - [x] 3.1.6 Implementar `_build_action_summary()` para `record_transaction` e `create_account`

- [x] 4. Testes Unitários (mocks only)
  - [x] 4.1 Criar `tests/unit/test_financial_chat.py`
    - [x] 4.1.1 `test_simple_reply_no_tools`
    - [x] 4.1.2 `test_tool_call_list_accounts_returns_final_reply`
    - [x] 4.1.3 `test_write_tool_returns_pending_action_without_executing`
    - [x] 4.1.4 `test_execute_pending_action_calls_record_transaction`
    - [x] 4.1.5 `test_build_action_summary_expense`
    - [x] 4.1.6 `test_execute_read_tool_list_accounts`
    - [x] 4.1.7 `test_execute_read_tool_get_statement_defaults`
    - [x] 4.1.8 `test_chat_raises_without_api_key`

- [x] 5. Interface Streamlit
  - [x] 5.1 Adicionar `"💬 Assistente Financeiro"` no `st.sidebar.radio` em `app.py`
  - [x] 5.2 Implementar seção do chat (histórico, input, spinner)
  - [x] 5.3 Implementar bloco de confirmação (PendingAction → botões ✅ Confirmar / ❌ Cancelar)
  - [x] 5.4 Adicionar botão "🗑️ Limpar Conversa" no sidebar

- [x] 6. Extensão: Criação de Conta via Chat
  - [x] 6.1 Adicionar ferramenta `create_account` em `_TOOLS` (schema JSON com `name`, `account_type`, `initial_balance`)
  - [x] 6.2 Adicionar `create_account` em `_WRITE_TOOLS` (exige confirmação)
  - [x] 6.3 Implementar execução em `execute_pending_action()`
  - [x] 6.4 Implementar resumo legível em `_build_action_summary()`
  - [x] 6.5 Atualizar `SYSTEM_PROMPT` para mencionar `create_account`

- [x] 7. Validação e Entrega
  - [x] 7.1 `uv run ruff check . && uv run ruff format .` — sem erros
  - [x] 7.2 `uv run pytest -v` — 72 testes passando
  - [x] 7.3 Commit e push para `feature/006-financial-chat`
