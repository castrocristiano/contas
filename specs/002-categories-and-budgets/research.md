# Pesquisa Técnica: Categorias e Orçamentos (002-categories-and-budgets)

**Feature**: `002-categories-and-budgets`
**Data**: 2026-09-19

---

## 1. Modelo de Entidade `Budget` e Relacionamentos

### Decisão
Criar o modelo `Budget` em `src/contas/models/budget.py` utilizando SQLModel/SQLAlchemy:
- `id`: UUID (chave primária)
- `category_id`: UUID (chave estrangeira para `category.id`, com `ondelete="CASCADE"` ou `RESTRICT`)
- `amount`: `Decimal` mapeado como `NUMERIC(14, 2)` (princípio II - proibição estrita de float)
- `month`: `int` (1 a 12, representando o mês de vigência)
- `year`: `int` (ano de vigência, ex: 2026)
- `created_at`: `datetime` (timezone-aware com UTC)
- Restrição de unicidade composta: `UniqueConstraint("category_id", "month", "year")` para garantir no máximo um orçamento por categoria por mês.

### Justificativa
Essa estrutura atende diretamente aos requisitos de controle mensal e preserva integridade sem adicionar complexidade desnecessária (YAGNI).

---

## 2. Cálculo de Execução Orçamentária

### Decisão
O cálculo do montante gasto em um orçamento será executado via agregação SQL (`func.coalesce(func.sum(Transaction.amount), Decimal("0.00"))`) filtrando por:
- `Transaction.category_id == budget.category_id`
- `Transaction.transaction_type == TransactionType.EXPENSE`
- `Transaction.status == TransactionStatus.CLEARED` (ou parametrizável)
- `Transaction.transaction_date` dentro do intervalo do mês (do primeiro dia às 00:00 até o último dia às 23:59:59.999999 UTC)

Métricas derivadas retornadas:
- `budget_amount`: valor total orçado (`Decimal`)
- `spent_amount`: total já gasto (`Decimal`)
- `remaining_balance`: `budget_amount - spent_amount` (pode ser negativo em caso de estouro)
- `spent_percentage`: `(spent_amount / budget_amount) * 100` (formatado com 2 casas)
- `is_exceeded`: booleano indicando se `spent_amount > budget_amount`

---

## 3. Ferramentas MCP a serem Expostas

### Decisão
Seguindo as convenções e contratos estabelecidos na feature `001`, as ferramentas serão:
1. `create_category`: Cadastra nova categoria (`name`, `category_type`).
2. `list_categories`: Lista categorias ativas com filtros opcionais (`category_type`, `include_inactive`).
3. `set_budget`: Cria ou atualiza o teto orçamentário de uma categoria para um determinado mês/ano.
4. `get_budget_status`: Consulta o acompanhamento de um orçamento específico ou de todos os orçamentos do mês.
