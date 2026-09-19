# Contratos MCP — Ferramentas do Servidor Contas

**Feature**: `001-core-infra-mcp`
**Protocolo**: Model Context Protocol (MCP) — JSON-RPC 2.0 via `stdio`
**SDK**: `mcp >= 2.2.0` (`MCPServer`)
**Data**: 2026-09-19

---

## Convenções Gerais

- **Transporte**: `stdio` (padrão para integração com Claude Desktop e agentes locais)
- **Schemas**: Pydantic v2 com `ConfigDict(extra="forbid", str_strip_whitespace=True)`
- **Valores monetários**: sempre `string` no JSON (ex: `"35.50"`) para preservar precisão decimal exata
- **IDs**: sempre `string` UUID4 (ex: `"3fa85f64-5717-4562-b3fc-2c963f66afa6"`)
- **Datas**: ISO 8601 com timezone (ex: `"2026-09-19T14:00:00-03:00"`)
- **Idioma dos campos**: todos em inglês (EN-US)

---

## Ferramentas Expostas

### `create_account`
Cria uma nova conta financeira no sistema.

**Input Schema**:
```json
{
  "name": {
    "type": "string",
    "description": "Display name of the account (e.g., 'Checking Account', 'Carteira')",
    "minLength": 1,
    "maxLength": 100
  },
  "account_type": {
    "type": "string",
    "enum": ["checking", "savings", "investment", "cash"],
    "description": "Type of account"
  },
  "initial_balance": {
    "type": "string",
    "description": "Opening balance as a decimal string (e.g., '1500.00'). Defaults to '0.00'.",
    "default": "0.00"
  },
  "currency": {
    "type": "string",
    "description": "Three-letter ISO 4217 currency code",
    "default": "BRL",
    "pattern": "^[A-Z]{3}$"
  }
}
```

**Output (sucesso)**:
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Conta Corrente",
  "account_type": "checking",
  "balance": "1500.00",
  "currency": "BRL",
  "is_active": true,
  "created_at": "2026-09-19T14:00:00-03:00"
}
```

---

### `list_accounts`
Lista todas as contas ativas com seus saldos atuais.

**Input Schema**:
```json
{
  "include_inactive": {
    "type": "boolean",
    "description": "If true, also returns inactive accounts. Default: false.",
    "default": false
  }
}
```

**Output (sucesso)**:
```json
{
  "accounts": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "Conta Corrente",
      "account_type": "checking",
      "balance": "1500.00",
      "currency": "BRL",
      "is_active": true
    }
  ],
  "total_balance": "1500.00",
  "currency": "BRL",
  "count": 1
}
```

---

### `record_transaction`
Registra uma transação financeira (receita, despesa ou transferência).

**Input Schema**:
```json
{
  "amount": {
    "type": "string",
    "description": "Transaction amount as a positive decimal string (e.g., '35.50'). Must be > 0.",
    "pattern": "^[0-9]+(\\.[0-9]{1,2})?$"
  },
  "transaction_type": {
    "type": "string",
    "enum": ["income", "expense", "transfer"],
    "description": "Type of transaction"
  },
  "source_account_id": {
    "type": "string",
    "description": "UUID of the source (debit) account"
  },
  "destination_account_id": {
    "type": "string",
    "description": "UUID of the destination (credit) account. Required when transaction_type is 'transfer'.",
    "default": null
  },
  "category_id": {
    "type": "string",
    "description": "UUID of the category. Optional.",
    "default": null
  },
  "description": {
    "type": "string",
    "description": "Short description of the transaction",
    "maxLength": 255,
    "default": ""
  },
  "transaction_date": {
    "type": "string",
    "description": "ISO 8601 datetime with timezone (e.g., '2026-09-19T14:00:00-03:00'). Defaults to current time.",
    "default": null
  },
  "status": {
    "type": "string",
    "enum": ["cleared", "pending"],
    "description": "Settlement status. 'pending' for scheduled future transactions.",
    "default": "cleared"
  }
}
```

**Regras de validação no servidor**:
- `amount` deve ser convertível para `Decimal` e `> 0`
- Se `transaction_type == "transfer"`: `destination_account_id` obrigatório e `!= source_account_id`
- Ambas as contas devem existir e estar ativas

**Output (sucesso)**:
```json
{
  "id": "7bd3a1b2-f42c-4e8d-9c11-1a2b3c4d5e6f",
  "amount": "35.50",
  "transaction_type": "expense",
  "status": "cleared",
  "transaction_date": "2026-09-19T14:00:00-03:00",
  "description": "Supermercado",
  "source_account": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "Conta Corrente",
    "new_balance": "1464.50"
  },
  "category_id": null,
  "created_at": "2026-09-19T17:00:00-03:00"
}
```

---

### `get_statement`
Retorna o extrato detalhado de uma conta em um período.

**Input Schema**:
```json
{
  "account_id": {
    "type": "string",
    "description": "UUID of the account to query"
  },
  "start_date": {
    "type": "string",
    "description": "Start of period. ISO 8601 date or datetime (e.g., '2026-09-01')."
  },
  "end_date": {
    "type": "string",
    "description": "End of period. ISO 8601 date or datetime (e.g., '2026-09-30')."
  },
  "include_pending": {
    "type": "boolean",
    "description": "If true, includes pending transactions. Default: false.",
    "default": false
  },
  "limit": {
    "type": "integer",
    "description": "Maximum number of transactions to return. Default: 50.",
    "default": 50,
    "minimum": 1,
    "maximum": 500
  }
}
```

**Output (sucesso)**:
```json
{
  "account": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "Conta Corrente",
    "current_balance": "1464.50"
  },
  "period": {
    "start": "2026-09-01T00:00:00-03:00",
    "end": "2026-09-30T23:59:59-03:00"
  },
  "transactions": [
    {
      "id": "7bd3a1b2-f42c-4e8d-9c11-1a2b3c4d5e6f",
      "transaction_date": "2026-09-19T14:00:00-03:00",
      "description": "Supermercado",
      "amount": "35.50",
      "transaction_type": "expense",
      "status": "cleared",
      "category": null
    }
  ],
  "summary": {
    "total_income": "0.00",
    "total_expense": "35.50",
    "net": "-35.50",
    "count": 1
  }
}
```

---

### `get_financial_summary`
Retorna o resumo patrimonial consolidado de todas as contas.

**Input Schema**:
```json
{
  "reference_date": {
    "type": "string",
    "description": "Reference date for balance calculation. ISO 8601. Defaults to today.",
    "default": null
  }
}
```

**Output (sucesso)**:
```json
{
  "reference_date": "2026-09-19",
  "accounts": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "Conta Corrente",
      "account_type": "checking",
      "balance": "1464.50",
      "currency": "BRL"
    }
  ],
  "total_assets": "1464.50",
  "currency": "BRL"
}
```

---

### `health_check`
Verifica a prontidão operacional do servidor MCP e da conexão com o banco de dados.

**Input Schema**: nenhum (sem parâmetros)

**Output (saudável)**:
```json
{
  "status": "healthy",
  "database": "connected",
  "server": "contas-mcp",
  "version": "0.1.0",
  "checked_at": "2026-09-19T17:00:00-03:00"
}
```

**Output (degradado)**:
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "error": "could not connect to server: Connection refused",
  "server": "contas-mcp",
  "version": "0.1.0",
  "checked_at": "2026-09-19T17:00:00-03:00"
}
```

---

## Contratos de Erro

Todos os erros retornam estrutura consistente via exceção MCP:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable error description",
    "details": {
      "field": "amount",
      "reason": "value must be greater than 0"
    }
  }
}
```

**Códigos de erro definidos**:

| Código | Situação |
| :--- | :--- |
| `VALIDATION_ERROR` | Falha de schema Pydantic (campo inválido, tipo errado, constraint violada) |
| `ACCOUNT_NOT_FOUND` | UUID de conta não encontrado ou inativo |
| `CATEGORY_NOT_FOUND` | UUID de categoria não encontrado ou inativo |
| `TRANSFER_SAME_ACCOUNT` | `source_account_id == destination_account_id` em transferência |
| `DATABASE_ERROR` | Falha transitória de conexão ou constraint do banco |
| `INTEGRITY_ERROR` | Violação de integridade referencial (FK, unique, etc.) |

