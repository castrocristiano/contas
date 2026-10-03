# Tarefas de Implementação - Feature 015: Edição de Nome da Conta

- [x] T001 [Domain] Adicionar método `update` na interface `IAccountRepository` em `src/contas/application/ports/repositories.py`
- [x] T002 [Schema] Criar schema `UpdateAccountInput` com validações em `src/contas/schemas/account.py`
- [x] T003 [UseCase] Implementar `UpdateAccountUseCase` em `src/contas/application/use_cases/accounts.py`
- [x] T004 [Repository] Implementar método `update` no repositório SQLAlchemy em `src/contas/infrastructure/repositories/sqlmodel_account_repository.py`
- [x] T005 [MCP] Expor MCP tool `update_account` em `src/contas/server.py`
- [x] T006 [Chat] Integrar `update_account` no assistente financeiro (`financial_chat.py`) como ação pendente
- [x] T007 [UI] Adicionar método `update_account` em `src/contas/ui/services.py` e interface de edição em `src/contas/ui/app.py`
- [x] T008 [Tests] Adicionar testes unitários para o use case em `tests/unit/test_clean_architecture_use_cases.py`
- [x] T009 [Tests] Adicionar testes de integração da tool em `tests/integration/test_account_tools.py`
- [x] T010 [Verification] Executar linter (`ruff check`), formatação (`ruff format`) e suíte de testes (`pytest`)
