# Guia de Validação Rápida: Categorias e Orçamentos

**Feature**: `002-categories-and-budgets`
**Data**: 2026-09-19

---

## 1. Inicializar o Ambiente

```bash
# Garantir que o banco de dados está em execução
podman-compose up -d

# Executar novas migrações
uv run alembic upgrade head
```

---

## 2. Cenário P1: Criação e Listagem de Categorias

1. Chamar tool `create_category`:
   ```json
   {
     "name": "Supermercado",
     "category_type": "expense"
   }
   ```
2. Chamar tool `list_categories`:
   ```json
   {
     "category_type": "expense"
   }
   ```
   **Resultado esperado**: Categoria `Supermercado` listada com status ativo.

---

## 3. Cenário P2: Definição de Orçamento Mensal

1. Chamar tool `set_budget`:
   ```json
   {
     "category_id": "<UUID da categoria Supermercado>",
     "amount": "600.00",
     "month": 9,
     "year": 2026
   }
   ```
   **Resultado esperado**: Orçamento criado com sucesso com `amount: "600.00"`.

---

## 4. Cenário P3: Monitoramento de Execução Orçamentária

1. Registrar despesa vinculada à categoria:
   ```json
   {
     "amount": "150.00",
     "transaction_type": "expense",
     "source_account_id": "<UUID da Conta>",
     "category_id": "<UUID da Categoria Supermercado>",
     "description": "Compras do mês"
   }
   ```
2. Consultar status do orçamento via `get_budget_status`:
   ```json
   {
     "month": 9,
     "year": 2026
   }
   ```
   **Resultado esperado**:
   - `budget_amount: "600.00"`
   - `spent_amount: "150.00"`
   - `remaining_balance: "450.00"`
   - `spent_percentage: "25.00"`
   - `is_exceeded: false`

