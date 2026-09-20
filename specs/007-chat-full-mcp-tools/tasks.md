# Tasks: Cobertura Completa de Ferramentas MCP no Chat (007-chat-full-mcp-tools)

- [x] 1. Spec e Planejamento SDD
  - [x] 1.1 Criar `specs/007-chat-full-mcp-tools/spec.md`
  - [x] 1.2 Criar `specs/007-chat-full-mcp-tools/plan.md`
  - [x] 1.3 Criar `specs/007-chat-full-mcp-tools/tasks.md`
  - [x] 1.4 Criar branch `feature/007-chat-full-mcp-tools`

- [x] 2. Definição de Schemas das Ferramentas MCP no Chat
  - [x] 2.1 Adicionar schema `get_installment_plan` (leitura)
  - [x] 2.2 Adicionar schema `create_category` (escrita)
  - [x] 2.3 Adicionar schema `set_budget` (escrita)
  - [x] 2.4 Adicionar schema `delete_transaction` (exclusão)
  - [x] 2.5 Adicionar schema `delete_account` (exclusão)

- [x] 3. Implementação da Lógica de Execução e Confirmação
  - [x] 3.1 Atualizar `_WRITE_TOOLS` com as ferramentas de alteração e exclusão
  - [x] 3.2 Implementar execução de `get_installment_plan` em `_execute_read_tool`
  - [x] 3.3 Implementar execuções de escrita/exclusão em `execute_pending_action`
  - [x] 3.4 Implementar resumos human-readable em `_build_action_summary` para as novas operações
  - [x] 3.5 Ajustar `SYSTEM_PROMPT` para guiar a IA na busca de IDs antes de propor exclusões

- [x] 4. Testes Unitários (Mocks Only)
  - [x] 4.1 Testar `get_installment_plan` em leitura
  - [x] 4.2 Testar `create_category` com `PendingAction` e execução
  - [x] 4.3 Testar `set_budget` com `PendingAction` e execução
  - [x] 4.4 Testar `delete_transaction` com `PendingAction` e execução
  - [x] 4.5 Testar `delete_account` com `PendingAction` e execução

- [x] 5. Validação e Entrega
  - [x] 5.1 Executar `uv run ruff check . && uv run ruff format .`
  - [x] 5.2 Executar `uv run pytest -v` (79 testes passando)
  - [x] 5.3 Atualizar tasks.md e documentação SDD
  - [x] 5.4 Commit e push na branch `feature/007-chat-full-mcp-tools`

