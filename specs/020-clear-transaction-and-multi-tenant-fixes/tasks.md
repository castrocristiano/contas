# Tarefas de Implementação - Feature 020: Liquidação Manual, Isolamento Multi-Tenant e Correções de Fatura

- [x] T001 [Schemas] Adicionar `ClearTransactionInput` e `ClearTransactionResponse` em `src/contas/schemas/transaction.py` e `user_id` em `DeleteAccountInput` e `UpdateAccountInput` (`src/contas/schemas/account.py`)
- [x] T002 [Ports & Infra] Adicionar método `update` em `ITransactionRepository` e implementar `SQLAlchemyTransactionRepository.update` com filtro por `user_id` e ordenação determinística em `SQLAlchemyAccountRepository.list_all`
- [x] T003 [UseCases] Implementar `ClearTransactionUseCase` em `src/contas/application/use_cases/transactions.py` e registrá-lo no `Container` (`src/contas/application/container.py`)
- [x] T004 [UseCases] Corrigir `RecordTransactionUseCase` para não redividir parcelas individuais (`installment_number` preenchido) e validar `user_id` em `destination_account_id`, `category_id`, `DeleteTransactionUseCase`, `UpdateAccountUseCase`, `DeleteAccountUseCase` e `BulkDeleteAccountsUseCase`
- [x] T005 [MCP & Services] Expor ferramenta MCP `clear_transaction` em `src/contas/tools/transactions.py` e adicionar `UIService.clear_transaction` e propagação de `user_id` em `src/contas/ui/services.py`
- [x] T006 [Chat] Propagar `user_id` em todas as tools do `FinancialChatAssistant` e implementar `_find_account_by_name` com prioridade para match exato em `src/contas/services/financial_chat.py`
- [x] T007 [UI] Ajustar importação de fatura para manter `is_cleared=False`, adicionar botão de liquidação em lote no Extrato e substituir seletores de conta por ID único em `src/contas/ui/app.py`
- [x] T008 [SonarQube] Configurar `sonar-project.properties` e `sonar_check.sh` para análise no servidor `dc1` e eliminar code smells reportados
- [x] T009 [Tests] Adicionar testes unitários e de integração para `ClearTransactionUseCase`, isolamento multi-tenant, chat e importação de parcelas (`127 passed`, 95.2% de cobertura em código novo)
