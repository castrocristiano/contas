# Interface Contracts: Filtros de Quitação e Projeção de Saldos (023-settlement-filters)

## 1. Contrato da MCP Tool: `get_statement`

A ferramenta MCP existente `get_statement` é estendida com o novo parâmetro `status_filter`.

### Tool Signature (MCP)
```json
{
  "name": "get_statement",
  "description": "Get account statement filtered by date range, transaction type and settlement status (cleared/pending).",
  "parameters": {
    "type": "object",
    "properties": {
      "account_id": {
        "type": "string",
        "format": "uuid",
        "description": "UUID of the account to get the statement for"
      },
      "start_date": {
        "type": "string",
        "description": "Start date in ISO 8601 format (YYYY-MM-DD)"
      },
      "end_date": {
        "type": "string",
        "description": "End date in ISO 8601 format (YYYY-MM-DD)"
      },
      "status_filter": {
        "type": "string",
        "enum": ["all", "cleared", "pending"],
        "default": "all",
        "description": "Filter by settlement status: 'all', 'cleared', or 'pending'"
      },
      "include_pending": {
        "type": "boolean",
        "default": true,
        "description": "Legacy flag to include pending transactions (defaults to true)"
      },
      "date_type": {
        "type": "string",
        "enum": ["transaction_date", "due_date"],
        "default": "transaction_date"
      },
      "limit": {
        "type": "integer",
        "default": 500
      },
      "search": {
        "type": "string",
        "nullable": true
      }
    },
    "required": ["account_id", "start_date", "end_date"]
  }
}
```

### Response Example (`status_filter="pending"`)
```json
{
  "account": {
    "id": "e838f3f8-6b89-4d64-88aa-381c62f279ea",
    "name": "Nubank Conta",
    "current_balance": "1500.00"
  },
  "period": {
    "start": "2026-11-01",
    "end": "2026-11-30",
    "date_type": "transaction_date"
  },
  "transactions": [
    {
      "id": "a90b8f41-01ab-4cf9-9831-294718301824",
      "transaction_date": "2026-11-20T10:00:00Z",
      "due_date": "2026-11-25T00:00:00Z",
      "description": "Conta de Luz - Enel",
      "amount": "230.50",
      "transaction_type": "expense",
      "status": "pending",
      "category": "Moradia"
    }
  ],
  "summary": {
    "total_income": "0.00",
    "total_expense": "230.50",
    "net": "-230.50",
    "count": 1
  }
}
```

---

## 2. Contrato da Camada UI (`UIService`)

```python
class UIService:
    @staticmethod
    def get_statement(
        account_id: UUID,
        start_date: str,
        end_date: str,
        include_pending: bool = True,
        status_filter: str = "all",
        limit: int = 500,
        date_type: str = "transaction_date",
        search: str | None = None,
        user_id: UUID | None = None,
    ) -> dict: ...

    @staticmethod
    def get_dashboard_projections(
        user_id: UUID | None = None,
        until_date: str | None = None,
    ) -> dict: ...
```

---

## 3. Contrato Visual do Dashboard e Extrato (Streamlit)

### Seletor no Extrato
```python
status_choice = st.selectbox(
    "Status de Quitação",
    options=[
        "Todas as Movimentações",
        "Apenas Pendentes (ocultar quitadas)",
        "Apenas Quitadas",
    ],
    index=0,
)
```

### Alternador no Dashboard
```python
vision_mode = st.radio(
    "Modo de Visualização do Saldo",
    options=[
        "🟢 Saldo Atual (Realizado)",
        "🔮 Saldo Projetado (Abatendo pendências)",
    ],
    horizontal=True,
)
```
