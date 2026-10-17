# Plano de Arquitetura e Implementação - Feature 020: Liquidação Manual, Isolamento Multi-Tenant e Correções de Fatura

## 1. Visão Geral da Arquitetura
Esta especificação abrange melhorias transversais respeitando a separação da **Clean Architecture**:
- **Domínio & Portas**: Adição do contrato `update(transaction: Transaction) -> Transaction` em `ITransactionRepository`.
- **Casos de Uso (`Application`)**: Implementação de `ClearTransactionUseCase` e blindagem multi-tenant (`user_id`) em `RecordTransactionUseCase`, `DeleteTransactionUseCase`, `UpdateAccountUseCase`, `DeleteAccountUseCase` e `BulkDeleteAccountsUseCase`.
- **Infraestrutura (`Infrastructure`)**: Implementação de `SQLAlchemyTransactionRepository.update` com filtro estrito por `id` e `user_id`, e ordenação determinística em `SQLAlchemyAccountRepository.list_all`.
- **Interface & Ferramentas (`UI` / `MCP` / `Chat`)**: Exposição da ferramenta `clear_transaction` no servidor MCP, botão de liquidação em lote na aba Extrato, seleção de contas por ID único no Streamlit e propagação de `user_id` no `FinancialChatAssistant`.

---

## 2. Camadas e Componentes Modificados

### 2.1 Schemas (`src/contas/schemas/`)
- `src/contas/schemas/transaction.py`:
  - Adição de `ClearTransactionInput(transaction_id: UUID, user_id: UUID | None = None)`.
  - Adição de `ClearTransactionResponse(id: UUID, description: str | None, amount: Decimal, is_cleared: bool, source_account_new_balance: Decimal, destination_account_new_balance: Decimal | None, message: str)`.
- `src/contas/schemas/account.py`:
  - Inclusão do campo `user_id: UUID | None = None` em `DeleteAccountInput` e `UpdateAccountInput`.

### 2.2 Portas e Repositórios (`src/contas/application/ports/` & `src/contas/infrastructure/repositories/`)
- `ITransactionRepository`: novo método abstrato `update(self, transaction: Transaction) -> Transaction`.
- `SQLAlchemyTransactionRepository.update`: busca registro ORM filtrando por `ORMTransaction.id == transaction.id` e `ORMTransaction.user_id == transaction.user_id`, sincroniza campos mutáveis (`is_cleared`, `description`, `amount`, etc.) e persiste via `session.flush()`.
- `SQLAlchemyAccountRepository.list_all`: adiciona `.order_by(ORMAccount.created_at.asc(), ORMAccount.id.asc())`.

### 2.3 Casos de Uso (`src/contas/application/use_cases/`)
- `ClearTransactionUseCase` (`transactions.py`):
  - Valida existência da transação sob o `user_id` informado.
  - Se `tx.is_cleared` já for `True`, retorna os saldos atuais sem reaplicar movimentação financeira.
  - Caso contrário, aplica o efeito no saldo da conta de origem (`INCOME` soma, `EXPENSE`/`TRANSFER` subtrai) e na conta de destino (`TRANSFER` soma), marca `tx.is_cleared = True` e persiste.
- `RecordTransactionUseCase` (`transactions.py`):
  - Diferencia criação de novo parcelamento (`total_installments > 1` e `installment_number is None`) de registro de parcela individual já calculada (`installment_number is not None`).
  - Valida `destination_account` e `category` com `tx_user_id`.
- `DeleteTransactionUseCase`, `UpdateAccountUseCase`, `DeleteAccountUseCase`, `BulkDeleteAccountsUseCase`:
  - Propagam `user_id` em todas as leituras e exclusões/atualizações de entidades relacionadas.

### 2.4 MCP Tools, Chat e UI (`src/contas/tools/`, `src/contas/services/`, `src/contas/ui/`)
- `src/contas/tools/transactions.py`: exposição da tool `clear_transaction` e refatoração do tratamento de erros em `_execute_uc`.
- `src/contas/services/financial_chat.py`:
  - Helper `_find_account_by_name` priorizando match exato normalizado antes de fallback por substring.
  - Propagação de `self.user_id` em todas as tools executadas pelo assistente.
- `src/contas/ui/app.py` e `src/contas/ui/services.py`:
  - Lançamentos de fatura criados sempre com `is_cleared=False`.
  - Botão `"✅ Liquidar Selecionadas"` na aba Extrato.
  - Seletores de conta baseados em ID (`options=[a["id"] for a in accounts]`) com `st.session_state["invoice_target_account_id"]`.

---

## 3. Qualidade e Verificação (SonarQube `dc1`)
- Configuração de `sonar-project.properties` e `sonar_check.sh` com suporte a token local (`.sonar_token` / `.sonar_remote_token`), geração de relatório `coverage.xml` com `pytest --cov=src/contas` e validação do Quality Gate no servidor `http://192.168.1.20:9000`.

