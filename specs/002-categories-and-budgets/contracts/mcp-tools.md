# Contratos MCP — Ferramentas de Categorias e Orçamentos

**Feature**: `002-categories-and-budgets`
**Protocolo**: Model Context Protocol (MCP) — JSON-RPC 2.0 via `stdio`
**SDK**: `MCPServer` (Python MCP SDK)
**Data**: 2026-09-19

---

## 1. `create_category`
Cria uma nova categoria financeira.

**Input Schema**:
```json
{
  "name": {
    "type": "string",
    "description": "Unique name of the category (e.g., 'Alimentação', 'Salário')",
    "minLength": 1,
    "maxLength": 100
  },
  "category_type": {
    "type": "string",
    "enum": ["income", "expense"],
    "description": "Type of the category: income or expense"
  }
}
```

**Output**:
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Alimentação",
  "category_type": "expense",
  "is_active": true
}
```

---

## 2. `list_categories`
Lista as categorias cadastradas no sistema.

**Input Schema**:
```json
{
  "category_type": {
    "type": "string",
    "enum": ["income", "expense"],
    "description": "Filter by category type. Optional.",
    "default": null
  },
  "include_inactive": {
    "type": "boolean",
    "description": "If true, also includes inactive categories. Default: false.",
    "default": false
  }
}
```

**Output**:
```json
{
  "categories": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "Alimentação",
      "category_type": "expense",
      "is_active": true
    }
  ],
  "count": 1
}
```

---

## 3. `set_budget`
Define ou atualiza o teto orçamentário de uma categoria para um determinado mês e ano.

**Input Schema**:
```json
{
  "category_id": {
    "type": "string",
    "description": "UUID of the expense category"
  },
  "amount": {
    "type": "string",
    "description": "Monthly budget limit as a decimal string (e.g., '500.00'). Must be > 0.",
    "pattern": "^[0-9]+(\\.[0-9]{1,2})?$"
  },
  "month": {
    "type": "integer",
    "description": "Month number (1 to 12)",
    "minimum": 1,
    "maximum": 12
  },
  "year": {
    "type": "integer",
    "description": "Year (e.g., 2026)",
    "minimum": 2000,
    "maximum": 2100
  }
}
```

**Output**:
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "category_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "category_name": "Alimentação",
  "amount": "500.00",
  "month": 9,
  "year": 2026,
  "created_at": "2026-09-19T20:00:00+00:00"
}
```

---

## 4. `get_budget_status`
Consulta a execução orçamentária para um mês/ano especificado.

**Input Schema**:
```json
{
  "month": {
    "type": "integer",
    "description": "Month number (1 to 12). Defaults to current month.",
    "default": null
  },
  "year": {
    "type": "integer",
    "description": "Year (e.g., 2026). Defaults to current year.",
    "default": null
  },
  "category_id": {
    "type": "string",
    "description": "Filter by specific category UUID. Optional.",
    "default": null
  }
}
```

**Output**:
```json
{
  "period": {
    "month": 9,
    "year": 2026
  },
  "budgets": [
    {
      "category_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "category_name": "Alimentação",
      "budget_amount": "500.00",
      "spent_amount": "350.00",
      "remaining_balance": "150.00",
      "spent_percentage": "70.00",
      "is_exceeded": false
    }
  ],
  "summary": {
    "total_budgeted": "500.00",
    "total_spent": "350.00",
    "total_remaining": "150.00",
    "overall_percentage": "70.00"
  }
}
```
