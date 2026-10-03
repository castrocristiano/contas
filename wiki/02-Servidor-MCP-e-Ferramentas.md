# 🔌 02. Servidor MCP e Ferramentas

O **Model Context Protocol (MCP)** é um protocolo aberto padronizado pela Anthropic que estabelece uma comunicação bidirecional e estruturada entre modelos de linguagem (LLMs) e ecossistemas de software locais.

O **Contas** atua nativamente como um **MCP Server**, permitindo que assistentes de IA (como Claude Desktop, Antigravity, Cursor e VS Code) executem operações financeiras reais com segurança matemática, validação de tipos e integridade referencial.

---

## 🛠️ Catálogo Completo das 13 Ferramentas MCP

| Ferramenta | Descrição | Principais Parâmetros |
| :--- | :--- | :--- |
| `create_account` | Cria uma nova conta financeira no sistema | `name`, `account_type`, `initial_balance`, `currency` |
| `list_accounts` | Lista contas do usuário com saldos e cálculo patrimonial | `include_inactive` |
| `update_account` | Atualiza o nome ou dados cadastrais de uma conta existente | `account_id`, `name`, `account_type` |
| `delete_account` | Exclui ou desativa conta (com opção cascade para apagar transações) | `account_id`, `force_cascade` |
| `record_transaction` | Registra receita, despesa, transferência ou compra parcelada | `amount`, `transaction_type`, `source_account_id`, `destination_account_id`, `category_id`, `total_installments` |
| `get_statement` | Retorna o extrato detalhado de uma conta em determinado período | `account_id`, `start_date`, `end_date`, `date_type`, `search` |
| `get_installment_plan` | Consulta o plano detalhado e o progresso de quitação de uma compra parcelada | `installment_id` |
| `delete_transaction` | Exclui uma transação ou plano parcelado, revertendo saldos de forma atômica | `transaction_id`, `delete_all_installments` |
| `get_financial_summary` | Consolida o total de receitas, despesas e saldo de todas as contas ativas | `start_date`, `end_date` |
| `create_category` | Cadastra uma nova categoria de receitas ou despesas | `name`, `category_type` |
| `list_categories` | Lista as categorias cadastradas com filtros por tipo | `category_type`, `include_inactive` |
| `set_budget` | Define ou atualiza o teto orçamentário mensal para uma categoria | `category_id`, `amount`, `month`, `year` |
| `get_budget_status` | Consulta o consumo real versus limite orçamentário no mês/ano | `category_id`, `month`, `year` |

---

## 🚀 Como Integrar com Clientes MCP

### 1. Claude Desktop
Adicione o servidor no arquivo de configuração do Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "contas": {
      "command": "uv",
      "args": [
        "--directory",
        "/caminho/absoluto/para/contas",
        "run",
        "python",
        "-m",
        "contas"
      ]
    }
  }
}
```

### 2. Modo Interativo de Depuração (MCP Inspector)
Para inspecionar e testar as ferramentas visualmente no navegador:

```bash
uv run mcp dev src/contas/server.py
```
