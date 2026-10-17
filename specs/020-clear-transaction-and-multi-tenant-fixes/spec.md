# Feature 020: Liquidação Manual de Lançamentos, Isolamento Multi-Tenant Estrito e Correção na Importação de Faturas

## Contexto e Motivação
Durante o uso da importação de faturas de cartão de crédito em PDF e da operação multi-tenant, foram identificados três pontos críticos de evolução e correção:
1. **Liquidação Indevida na Importação de Faturas**: Ao importar despesas de uma fatura de cartão de crédito em PDF, lançamentos com data de compra no passado estavam sendo marcados automaticamente como liquidados (`is_cleared = True`), impactando imediatamente o saldo antes do efetivo pagamento da fatura. Além disso, faltava na interface (aba Extrato) e no servidor MCP uma ação dedicada para **liquidar manualmente** lançamentos pendentes.
2. **Seleção de Conta na Importação de Fatura e Duplicidade de Nomes**: Em cenários onde o usuário possuía contas com nomes iguais ou similares (ex: Conta Corrente e Cartão de Crédito com o mesmo nome do banco), o dicionário indexado por nome (`{a["name"]: a["id"]}`) sobrescrevia a conta selecionada e podia lançar a fatura na conta incorreta. Além disso, ao importar parcelas individuais de uma fatura (`installment_number` já definido), o caso de uso dividia novamente o valor da parcela por `total_installments`.
3. **Auditoria de Isolamento Multi-Tenant (`user_id`) e Qualidade SonarQube (`dc1`)**: Algumas operações de mutação (`update_account`, `delete_account`, `bulk_delete_accounts`, `delete_transaction`, validação de `destination_account_id` e `category_id`, e ferramentas do assistente de chat financeiro) não propagavam ou não validavam estritamente o `user_id` do proprietário. Adicionalmente, o projeto precisava de integração contínua com o servidor SonarQube (`dc1`) cumprindo o Quality Gate sem issues de segurança ou manutenibilidade.

---

## Requisitos Funcionais

- **RF-001 (Faturas Importadas como Pendentes por Padrão)**:
  - Todos os lançamentos oriundos da importação de fatura PDF (tanto da fatura atual quanto de parcelas futuras projetadas) devem ser registrados com `is_cleared = False`, pois só são efetivamente liquidados mediante o pagamento da fatura.

- **RF-002 (Liquidação Manual de Transações — `clear_transaction`)**:
  - Criar o caso de uso `ClearTransactionUseCase`, schema `ClearTransactionInput` / `ClearTransactionResponse`, método `UIService.clear_transaction` e ferramenta MCP `clear_transaction`.
  - Se a transação estiver pendente (`is_cleared = False`), marcá-la como liquidada (`is_cleared = True`) e aplicar atomicamente o efeito financeiro no saldo da conta de origem (`source_account_id`) e/ou destino (`destination_account_id`).
  - Se a transação já estiver liquidada (`is_cleared = True`), retornar resposta idempotente informando que já se encontra liquidada, sem alterar o saldo novamente.
  - Na aba **Extrato** do Streamlit (`app.py`), permitir selecionar lançamentos pendentes e clicar em **"✅ Liquidar Selecionadas"** para efetivar a baixa em lote.

- **RF-003 (Seleção de Conta por ID Único e Preservação de Parcela Individual)**:
  - Substituir seletores de conta baseados em dicionário por nome (`{a["name"]: a["id"]}`) por seletores baseados no identificador único (`a["id"]`) com `format_func` exibindo nome e tipo da conta em todas as abas (`Extrato`, `Novo Lançamento`, `Importar Fatura PDF`, `Configurações`).
  - Persistir a conta de destino da fatura em `st.session_state["invoice_target_account_id"]` (priorizando contas do tipo `credit_card` por padrão) e exibir seletor sincronizado na etapa final de confirmação antes do lançamento.
  - Em `RecordTransactionUseCase`, quando `installment_number` já for informado (parcela individual importada de fatura), registrar exatamente a parcela informada sem redividir `amount` por `total_installments` nem gerar loop `1..N`.

- **RF-004 (Isolamento Multi-Tenant Estrito em Todas as Interações com o Banco)**:
  - Propagar e validar `user_id` em `UpdateAccountUseCase`, `DeleteAccountUseCase`, `BulkDeleteAccountsUseCase`, `DeleteTransactionUseCase` e `ClearTransactionUseCase`.
  - Validar em `RecordTransactionUseCase` que `source_account_id`, `destination_account_id` e `category_id` pertencem ao mesmo `user_id` da transação.
  - Garantir ordenação determinística (`created_at ASC, id ASC`) em `SQLAlchemyAccountRepository.list_all`.
  - Propagar `user_id` em todas as chamadas de leitura e escrita do `FinancialChatAssistant` e priorizar correspondência exata de nome de conta em `_find_account_by_name`.

---

## Requisitos Não Funcionais

- **RNF-001 (Qualidade e Segurança — SonarQube `dc1`)**:
  - Configurar `sonar-project.properties` e `sonar_check.sh` apontando para o servidor SonarQube em `dc1` (`http://192.168.1.20:9000`).
  - Atingir **Quality Gate: OK** com 0 bugs, 0 vulnerabilidades, 0 security hotspots abertos e cobertura de testes superior a 80% no código novo.
- **RNF-002 (Integridade Matemática)**:
  - Manter todas as operações de saldo estritamente em `Decimal`.
- **RNF-003 (Testes Automatizados)**:
  - Cobertura unitária e de integração para liquidação de transações, isolamento multi-tenant, chat financeiro e importação de parcelas.

