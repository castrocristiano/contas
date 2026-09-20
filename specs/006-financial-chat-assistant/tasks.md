# Tasks: Assistente Financeiro por Chat (006-financial-chat-assistant)

- [ ] 1. Spec & Planejamento
  - [x] 1.1 Criar `specs/006-financial-chat-assistant/spec.md`
  - [x] 1.2 Criar `specs/006-financial-chat-assistant/plan.md`
  - [x] 1.3 Criar `specs/006-financial-chat-assistant/tasks.md`
  - [x] 1.4 Criar branch `feature/006-financial-chat`

- [ ] 2. UIService — Método Faltante
  - [ ] 2.1 Adicionar `UIService.get_financial_summary(month, year)` em `src/contas/ui/services.py`

- [ ] 3. Serviço de Chat
  - [ ] 3.1 Criar `src/contas/services/financial_chat.py`
    - [ ] 3.1.1 Definir `_TOOLS` (schemas JSON das 6 ferramentas)
    - [ ] 3.1.2 Implementar `@dataclass PendingAction`
    - [ ] 3.1.3 Implementar `_execute_read_tool()`
    - [ ] 3.1.4 Implementar `execute_pending_action()`
    - [ ] 3.1.5 Implementar `chat_with_financial_assistant()` com loop agentic
    - [ ] 3.1.6 Implementar `_build_action_summary()`

- [ ] 4. Testes Unitários (mocks only)
  - [ ] 4.1 Criar `tests/unit/test_financial_chat.py`
    - [ ] 4.1.1 `test_simple_reply_no_tools`
    - [ ] 4.1.2 `test_tool_call_list_accounts`
    - [ ] 4.1.3 `test_write_tool_returns_pending_action`
    - [ ] 4.1.4 `test_execute_pending_action_success`
    - [ ] 4.1.5 `test_build_action_summary`

- [ ] 5. Interface Streamlit
  - [ ] 5.1 Adicionar `"💬 Assistente Financeiro"` no `st.sidebar.radio` em `app.py`
  - [ ] 5.2 Implementar seção do chat (histórico, input, spinner)
  - [ ] 5.3 Implementar bloco de confirmação (PendingAction → botões Confirmar/Cancelar)
  - [ ] 5.4 Adicionar botão "Limpar Conversa" no sidebar

- [ ] 6. Validação e Entrega
  - [ ] 6.1 `uv run ruff check . && uv run ruff format --check .`
  - [ ] 6.2 `uv run pytest -v` (todos os testes passando)
  - [ ] 6.3 Commit e push para `feature/006-financial-chat`
