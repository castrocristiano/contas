# Tarefas de Implementação - Feature 015: Edição de Nome da Conta

- [ ] T001 [Domain] Adicionar método `update` na interface `IAccountRepository` em `src/contas/application/ports/repositories.py`
- [ ] T002 [Schema] Criar schema `UpdateAccountInput` com validações em `src/contas/schemas/account.py`
- [ ] T003 [UseCase] Implementar `UpdateAccountUseCase` em `src/contas/application/use_cases/accounts.py`
- [ ] T004 [Repository] Implementar método `update` no repositório SQLAlchemy em `src/contas/infrastructure/repositories/sqlmodel_account_repository.py`
- [ ] T005 [MCP] Expor MCP tool `update_account` em `src/contas/server.py`
- [ ] T006 [Chat] Integrar `update_account` no assistente financeiro (`financial_chat.py`) como ação pendente
- [ ] T007 [UI] Adicionar método `update_account` em `src/contas/ui/services.py` e interface de edição em `src/contas/ui/app.py`
- [ ] T008 [Tests] Adicionar testes unitários para o use case em `tests/unit/test_clean_architecture_use_cases.py`
- [ ] T009 [Tests] Adicionar testes de integração da tool em `tests/integration/test_account_tools.py`
- [ ] T010 [Verification] Executar linter (`ruff check`), formatação (`ruff format`) e suíte de testes (`pytest`)
