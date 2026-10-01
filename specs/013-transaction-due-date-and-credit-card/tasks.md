# Tarefas de Implementação - Feature 013

- [x] T001 [Domain] Adicionar `CREDIT_CARD = "credit_card"` ao enum `AccountType` em `src/contas/domain/enums.py` e `src/contas/models/account.py`
- [x] T002 [Domain] Adicionar `due_date: datetime | None = None` na entidade `Transaction` em `src/contas/domain/entities.py` e no modelo `src/contas/models/transaction.py`
- [x] T003 [DB] Criar migração Alembic para adicionar `due_date` na tabela `transaction` e valor `credit_card` ao enum `account_type_enum`
- [x] T004 [Schemas] Atualizar `RecordTransactionInput`, `RecordTransactionResponse`, `GetStatementInput`, `StatementItem` e `StatementPeriod` em `src/contas/schemas/transaction.py` com suporte a `due_date` e `date_type`
- [x] T005 [Repositories] Atualizar `ITransactionRepository`, `SQLAlchemyTransactionRepository` e `InMemoryTransactionRepository` para suportar `due_date` e filtro por `date_type`
- [x] T006 [UseCases] Atualizar `RecordTransactionUseCase` e `GetStatementUseCase` para lidar com `due_date` (inclusive em compras parceladas) e filtro por `date_type`
- [x] T007 [UI Services] Atualizar `UIService.get_statement` e `UIService.record_transaction` para aceitar `due_date` e `date_type`
- [x] T008 [UI App] Atualizar tela de extrato, tabela de lançamentos, formulário de novo lançamento e cadastro de contas em `src/contas/ui/app.py`
- [x] T009 [Chat] Atualizar tools (`get_statement`, `record_transaction`, `create_account`), `SYSTEM_PROMPT` e execução no chat em `src/contas/services/financial_chat.py`
- [x] T010 [Tests] Adicionar e atualizar testes unitários e de integração
- [x] T011 [Verification] Executar linter, formatação e suíte completa de testes
