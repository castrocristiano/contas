# Feature 013: Transaction Due Date and Credit Card Account Type

## Contexto e Motivação
Atualmente, as transações financeiras no sistema possuem apenas `transaction_date` (data em que a operação ocorreu ou foi agendada). Para compras com cartão de crédito, boletos e despesas em geral, é fundamental diferenciar a **data da transação** (quando a compra foi feita) da **data de vencimento** (`due_date`, quando o pagamento da fatura ou boleto de fato ocorre ou vence).
Além disso, o sistema conta apenas com os tipos de conta `checking`, `savings`, `investment` e `cash`. É necessário introduzir a categoria de tipo de conta `credit_card` (cartão de crédito) para representar faturas e cartões de crédito adequadamente.
Adicionalmente, os filtros de consulta/extrato e a exibição das transações na interface e no assistente financeiro inteligente (chat) devem suportar ambas as datas e permitir buscas em linguagem natural por vencimento ou por data de lançamento.

---

## Requisitos Funcionais

- **RF-001 (Data de Vencimento)**: As transações (`Transaction`) devem possuir o campo opcional `due_date` (data/hora de vencimento). Ao registrar uma transação, se `due_date` não for informada, deve assumir o valor de `transaction_date`. Em compras parceladas, o cálculo das datas de vencimento subsequentes deve incrementar mensalmente a partir da `due_date` inicial.
- **RF-002 (Tipo de Conta Cartão de Crédito)**: O enum `AccountType` deve incluir o valor `credit_card` ("credit_card"), permitindo a criação e gestão de contas do tipo cartão de crédito.
- **RF-003 (Filtro por Tipo de Data)**: A consulta de extrato (`GetStatementInput`, `UIService.get_statement`, use cases e repositório) deve aceitar o parâmetro `date_type` com os valores `"transaction_date"` (padrão) ou `"due_date"`. Quando `"due_date"` for selecionado, o intervalo de datas deve filtrar pela data de vencimento.
- **RF-004 (Exibição na Interface Streamlit)**:
  - Na tela de Extrato (Dashboard), adicionar opção de filtro por "Data do Lançamento" ou "Data de Vencimento".
  - A tabela de extrato deve exibir as colunas de "Data" (lançamento) e "Vencimento".
  - No formulário de "Novo Lançamento", incluir campo para informar a "Data de Vencimento" (inicializada com a data do lançamento).
  - No cadastro de contas, disponibilizar o tipo "Cartão de Crédito" (`credit_card`).
- **RF-005 (Assistente Financeiro em Linguagem Natural)**:
  - Adaptar a tool `get_statement` para aceitar `date_type` ("transaction_date" | "due_date").
  - Adaptar a tool `record_transaction` para aceitar `due_date` opcional.
  - Adaptar a tool `create_account` para aceitar `account_type="credit_card"`.
  - Atualizar o `SYSTEM_PROMPT` para instruir o assistente a usar `date_type="due_date"` quando o usuário perguntar sobre vencimentos (ex.: "o que vence esta semana?", "quais faturas vencem até dia 15?").

---

## Requisitos Não Funcionais
- **RNF-001**: 100% de retrocompatibilidade com transações e consultas existentes.
- **RNF-002**: Migração Alembic incremental para adicionar a coluna `due_date` e o valor enum `credit_card`.
- **RNF-003**: Manter padrão Clean Architecture (Domain, UseCases, Repositories, Schemas, Tools, UI).
- **RNF-004**: Testes unitários e de integração cobrindo todas as novas capacidades.
