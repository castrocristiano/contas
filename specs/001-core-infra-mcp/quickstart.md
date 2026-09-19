# Guia de Validação Rápida: Infraestrutura Base e Servidor MCP

**Feature**: `001-core-infra-mcp`
**Data**: 2026-09-19

Este guia documenta como validar que a feature está funcionando de ponta a ponta após a implementação. Não inclui código de implementação — apenas como inicializar o ambiente e verificar os cenários de aceitação da spec.

---

## Pré-requisitos

| Requisito | Verificação |
| :--- | :--- |
| Podman instalado | `podman --version` |
| podman-compose instalado | `podman-compose --version` |
| uv instalado | `uv --version` |
| Arquivo `.env` configurado na raiz | Ver seção abaixo |

### Arquivo `.env` mínimo para desenvolvimento local

```bash
# .env (NÃO versionar — está no .gitignore)
POSTGRES_DB=contas
POSTGRES_USER=contas
POSTGRES_PASSWORD=contas_dev_password

DATABASE_URL=postgresql+psycopg://contas:contas_dev_password@localhost:5432/contas
OPENAI_API_KEY=sk-...  # opcional para validação do servidor MCP
```

---

## 1. Inicializar o Ambiente Completo

```bash
# Subir o PostgreSQL via podman-compose
podman-compose up -d

# Verificar que o banco está saudável
podman-compose ps
# Esperado: contas-db com status "healthy"

# Rodar as migrações do banco de dados
uv run alembic upgrade head

# Verificar o log de migrações
uv run alembic current
```

---

## 2. Validar o Servidor MCP com o MCP Inspector

```bash
# Inicia o servidor MCP com interface web interativa
uv run mcp dev src/contas/server.py
# Abre em: http://localhost:6274

# Ou executar diretamente (modo stdio)
uv run python -m contas
```

---

## 3. Cenário: Criar Conta e Verificar Listagem

No MCP Inspector (ou via cliente MCP), chamar:

**Tool**: `create_account`
```json
{
  "name": "Conta Corrente",
  "account_type": "checking",
  "initial_balance": "1500.00",
  "currency": "BRL"
}
```
**Resultado esperado**: JSON com `id` (UUID), `name`, `balance: "1500.00"`, `is_active: true`

---

**Tool**: `list_accounts`
```json
{}
```
**Resultado esperado**: Lista com a conta criada e `total_balance: "1500.00"`

---

## 4. Cenário P1: Registrar Despesa e Verificar Saldo Atualizado

> Referência: História de Usuário 1, Cenário de Aceitação 1

**Tool**: `record_transaction`
```json
{
  "amount": "35.50",
  "transaction_type": "expense",
  "source_account_id": "<UUID da conta criada>",
  "description": "Supermercado"
}
```
**Resultado esperado**:
- `status: "cleared"`
- `source_account.new_balance: "1464.50"` (1500.00 - 35.50)

---

**Tool**: `get_statement`
```json
{
  "account_id": "<UUID da conta>",
  "start_date": "2026-09-01",
  "end_date": "2026-09-30"
}
```
**Resultado esperado**: Lista com a transação de despesa de R$ 35,50 e `summary.total_expense: "35.50"`

---

## 5. Cenário P2: Consultar Resumo Financeiro Consolidado

**Tool**: `get_financial_summary`
```json
{}
```
**Resultado esperado**: `total_assets: "1464.50"` com todas as contas listadas

---

## 6. Cenário P3: Rejeição de Lançamentos Inválidos

### Valor zero:
```json
{ "amount": "0.00", "transaction_type": "expense", "source_account_id": "<UUID>" }
```
**Resultado esperado**: Erro `VALIDATION_ERROR` — `amount must be > 0`

### Conta inexistente:
```json
{ "amount": "10.00", "transaction_type": "expense", "source_account_id": "00000000-0000-0000-0000-000000000000" }
```
**Resultado esperado**: Erro `ACCOUNT_NOT_FOUND`

### Transferência sem destino:
```json
{ "amount": "100.00", "transaction_type": "transfer", "source_account_id": "<UUID>" }
```
**Resultado esperado**: Erro `VALIDATION_ERROR` — `destination_account_id required for transfer`

---

## 7. Verificar Health Check

**Tool**: `health_check`
```json
{}
```
**Resultado esperado**: `status: "healthy"`, `database: "connected"`

---

## 8. Validar Testes Automatizados

```bash
# Rodar todos os testes
uv run pytest -v

# Rodar com cobertura (quando implementado)
uv run pytest --cov=src/contas --cov-report=term-missing
```

**Resultado esperado**: 100% dos testes passando

---

## 9. Validar Linting e Formatação

```bash
uv run ruff check .
uv run ruff format --check .
```

**Resultado esperado**: `All checks passed!`

---

## 10. Encerrar o Ambiente

```bash
# Parar os containers sem apagar os dados
podman-compose down

# Parar E apagar os dados (volume)
podman-compose down -v
```

---

## Referências

- Modelo de dados: [`data-model.md`](./data-model.md)
- Contratos das tools: [`contracts/mcp-tools.md`](./contracts/mcp-tools.md)
- Especificação completa: [`spec.md`](./spec.md)

