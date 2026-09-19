# Pesquisa Técnica: MCP SDK (Python)

**Feature**: `001-core-infra-mcp`
**Tecnologia**: `mcp >= 2.2.0` com Pydantic v2
**Data**: 2026-09-19

---

## Versão Estável e API de Alto Nível

O SDK oficial evoluiu na versão 2.x:

| Versão | Classe principal | Import |
| :--- | :--- | :--- |
| `mcp < 2.0` | `FastMCP` | `from mcp.server.fastmcp import FastMCP` |
| `mcp >= 2.0` (atual) | `MCPServer` | `from mcp.server.mcpserver import MCPServer` |

**Decisão**: Usar `MCPServer` (SDK 2.x). A API de alto nível infere o JSON Schema automaticamente via assinaturas tipadas com `Annotated` e `pydantic.Field`, eliminando o boilerplate de `list_tools()` + `call_tool()` da API low-level.

---

## Registro de Ferramentas com `@mcp.tool()`

### Padrão com argumentos tipados (`Annotated` + `Field`)

```python
from typing import Annotated
from pydantic import Field
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("contas-server")


@mcp.tool()
async def create_account(
    name: Annotated[
        str,
        Field(description="Display name of the account", min_length=1, max_length=100),
    ],
    account_type: Annotated[
        str, Field(description="Type: checking, savings, investment, cash")
    ],
    initial_balance: Annotated[
        str, Field(default="0.00", description="Opening balance as decimal string")
    ] = "0.00",
) -> dict:
    """Create a new financial account."""
    ...
```

### Padrão com `BaseModel` dedicado (payloads complexos)

```python
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.mcpserver import MCPServer


class CreateAccountInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(description="Display name", min_length=1, max_length=100)
    account_type: str = Field(description="Type: checking, savings, investment, cash")
    initial_balance: str = Field(
        default="0.00", description="Opening balance as decimal string"
    )
    currency: str = Field(
        default="BRL", description="ISO 4217 code", pattern=r"^[A-Z]{3}$"
    )


@mcp.tool()
async def create_account(payload: CreateAccountInput) -> dict:
    """Create a new financial account."""
    ...
```

**Decisão**: Usar `BaseModel` dedicado por tool — mais legível, testável e mantém o schema isolado do handler.

---

## Transporte: `stdio`

O transporte `stdio` executa o servidor como subprocesso do cliente MCP (Claude Desktop, VS Code, etc.). Comunicação via `stdin`/`stdout` com JSON-RPC.

```python
def main() -> None:
    server = create_server()
    server.run()  # padrão: stdio
```

> **Regra crítica**: `stdout` pertence **exclusivamente** ao protocolo JSON-RPC.
> Logs e debug vão **sempre** para `stderr`:
> ```python
> import logging, sys
> logging.basicConfig(stream=sys.stderr, level=logging.INFO)
> ```

---

## Registro Modular de Ferramentas

Cada módulo de tools expõe uma função de registro que recebe o `MCPServer`:

```python
# tools/accounts.py
def register_account_tools(mcp: MCPServer) -> None:
    @mcp.tool()
    async def create_account(payload: CreateAccountInput) -> dict: ...

    @mcp.tool()
    async def list_accounts(payload: ListAccountsInput) -> dict: ...


# server.py
def create_server() -> MCPServer:
    mcp = MCPServer("contas-server")
    register_account_tools(mcp)
    register_transaction_tools(mcp)
    register_health_tools(mcp)
    return mcp
```

---

## Boas Práticas de Validação Pydantic v2 nas Tools

| Prática | Motivo |
| :--- | :--- |
| `ConfigDict(extra="forbid")` | Bloqueia parâmetros inventados pelo LLM |
| `ConfigDict(str_strip_whitespace=True)` | Higienização automática de strings |
| `description` em cada campo | Guia semântico para o modelo de linguagem |
| `field_validator` / `model_validator` | Regras de domínio (ex: `start_date <= end_date`) |
| Erros informativos com código estruturado | Permite ao LLM corrigir os parâmetros |

---

## Execução com `uv run`

```bash
# Modo desenvolvimento (MCP Inspector em http://localhost:6274)
uv run mcp dev src/contas/server.py

# Módulo direto
uv run python -m contas

# Via entry-point do pyproject.toml
uv run contas
```

---

## Configuração no Claude Desktop

```json
{
  "mcpServers": {
    "contas": {
      "command": "uv",
      "args": ["--directory", "/home/cristiano/Dev/contas", "run", "python", "-m", "contas"],
      "env": {
        "DATABASE_URL": "postgresql+psycopg://contas:senha@localhost:5432/contas"
      }
    }
  }
}
```

