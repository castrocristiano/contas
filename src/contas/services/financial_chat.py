"""Financial chat assistant using OpenAI function calling.

The assistant has read-only and write tools mapped to UIService operations.
Write operations (record_transaction) return a PendingAction instead of executing
immediately — the UI layer is responsible for showing a confirmation step.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from openai import OpenAI

from contas.config import settings
from contas.ui.services import UIService

# ---------------------------------------------------------------------------
# Tool schemas exposed to the model
# ---------------------------------------------------------------------------

_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "list_accounts",
            "description": (
                "Lista todas as contas financeiras do usuário com seus saldos e tipos. "
                "Use para responder perguntas sobre saldos, número de contas, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "include_inactive": {
                        "type": "boolean",
                        "description": "Se true, inclui contas inativas/arquivadas.",
                        "default": False,
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_categories",
            "description": "Lista as categorias de receita ou despesa cadastradas pelo usuário.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category_type": {
                        "type": "string",
                        "enum": ["income", "expense"],
                        "description": "Filtra por tipo: 'income' ou 'expense'. Omita para listar todas.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_financial_summary",
            "description": (
                "Retorna um resumo financeiro consolidado (receitas totais, despesas totais, saldo líquido) "
                "para um período mensal específico. Use quando o usuário perguntar sobre gastos totais, "
                "resumo do mês, receitas, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {
                        "type": "integer",
                        "description": "Mês de referência (1-12). Padrão: mês atual.",
                    },
                    "year": {
                        "type": "integer",
                        "description": "Ano de referência (ex: 2026). Padrão: ano atual.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_statement",
            "description": (
                "Retorna o extrato detalhado de uma conta em um período. "
                "Use quando o usuário perguntar sobre transações específicas, histórico de compras, "
                "gastos por período, últimas movimentações, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "account_name": {
                        "type": "string",
                        "description": (
                            "Nome da conta (ex: 'Nubank', 'Bradesco'). "
                            "Se não especificado, usa a primeira conta disponível."
                        ),
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Data inicial no formato YYYY-MM-DD.",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Data final no formato YYYY-MM-DD.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Número máximo de transações a retornar. Padrão 50.",
                        "default": 50,
                    },
                },
                "required": ["start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_budget_status",
            "description": (
                "Retorna o status dos orçamentos por categoria para um mês/ano, "
                "incluindo quanto já foi gasto e quanto resta. Use para perguntas "
                "sobre metas, orçamentos e limites de gastos."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {
                        "type": "integer",
                        "description": "Mês de referência (1-12). Padrão: mês atual.",
                    },
                    "year": {
                        "type": "integer",
                        "description": "Ano de referência (ex: 2026). Padrão: ano atual.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_transaction",
            "description": (
                "Registra uma transação financeira (receita ou despesa). "
                "Use APENAS quando o usuário pedir explicitamente para registrar, lançar, "
                "adicionar ou criar uma transação. Nunca use para consultas."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "string",
                        "description": "Valor em decimal positivo com ponto (ex: '49.90').",
                    },
                    "transaction_type": {
                        "type": "string",
                        "enum": ["income", "expense"],
                        "description": "Tipo: 'income' para receita, 'expense' para despesa.",
                    },
                    "account_name": {
                        "type": "string",
                        "description": "Nome da conta onde registrar.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Descrição do lançamento.",
                    },
                    "category_name": {
                        "type": "string",
                        "description": (
                            "Nome da categoria (ex: 'Alimentação', 'Salário'). "
                            "Opcional — omita se não souber."
                        ),
                    },
                    "transaction_date": {
                        "type": "string",
                        "description": "Data no formato YYYY-MM-DD. Padrão: hoje.",
                    },
                },
                "required": [
                    "amount",
                    "transaction_type",
                    "account_name",
                    "description",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_account",
            "description": (
                "Cria uma nova conta financeira para o usuário. "
                "Use quando o usuário pedir para criar, adicionar ou cadastrar uma conta bancária, "
                "carteira, poupança, investimento, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Nome da conta (ex: 'Nubank', 'Bradesco Corrente', 'Carteira').",
                    },
                    "account_type": {
                        "type": "string",
                        "enum": ["checking", "savings", "investment", "cash"],
                        "description": (
                            "Tipo da conta: 'checking' (corrente), 'savings' (poupança), "
                            "'investment' (investimento), 'cash' (carteira/dinheiro físico)."
                        ),
                    },
                    "initial_balance": {
                        "type": "string",
                        "description": "Saldo inicial em decimal positivo com ponto (ex: '0.00'). Padrão: '0.00'.",
                        "default": "0.00",
                    },
                },
                "required": ["name", "account_type"],
            },
        },
    },
]

# ---------------------------------------------------------------------------
# Pending action — write operation awaiting confirmation
# ---------------------------------------------------------------------------


@dataclass
class PendingAction:
    """A write operation proposed by the AI, awaiting explicit user confirmation."""

    tool_name: str
    arguments: dict[str, Any]
    summary: str  # Human-readable text shown to the user before they confirm

    # Context needed to resolve IDs at execution time
    accounts: list[dict] = field(default_factory=list)
    categories: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Read-only tool dispatcher
# ---------------------------------------------------------------------------


def _execute_read_tool(
    name: str,
    args: dict[str, Any],
    accounts: list[dict],
    categories: list[dict],
) -> str:
    """Execute a read-only tool and return the result serialised as JSON."""
    now = datetime.now(UTC)

    if name == "list_accounts":
        result = UIService.list_accounts(
            include_inactive=args.get("include_inactive", False)
        )
        return json.dumps(result, ensure_ascii=False, default=str)

    if name == "list_categories":
        result = UIService.list_categories(category_type=args.get("category_type"))
        return json.dumps(result, ensure_ascii=False, default=str)

    if name == "get_financial_summary":
        result = UIService.get_financial_summary(
            month=args.get("month", now.month),
            year=args.get("year", now.year),
        )
        return json.dumps(result, ensure_ascii=False, default=str)

    if name == "get_statement":
        account_name = args.get("account_name")
        account = None
        if account_name:
            account = next(
                (a for a in accounts if account_name.lower() in a["name"].lower()),
                None,
            )
        if account is None and accounts:
            account = accounts[0]
        if account is None:
            return json.dumps({"error": "Nenhuma conta encontrada."})

        from uuid import UUID

        result = UIService.get_statement(
            account_id=UUID(account["id"]),
            start_date=args["start_date"],
            end_date=args["end_date"],
            limit=args.get("limit", 50),
        )
        return json.dumps(result, ensure_ascii=False, default=str)

    if name == "get_budget_status":
        result = UIService.get_budget_status(
            month=args.get("month", now.month),
            year=args.get("year", now.year),
        )
        return json.dumps(result, ensure_ascii=False, default=str)

    return json.dumps({"error": f"Ferramenta desconhecida: {name}"})


# ---------------------------------------------------------------------------
# Write action executor (called only after user confirmation)
# ---------------------------------------------------------------------------


def execute_pending_action(pending: PendingAction) -> dict[str, Any]:
    """Execute a confirmed write action and return the result dict."""
    from uuid import UUID

    args = pending.arguments
    now = datetime.now(UTC)

    if pending.tool_name == "record_transaction":
        # Resolve account by name
        account_name = args.get("account_name", "")
        account = next(
            (a for a in pending.accounts if account_name.lower() in a["name"].lower()),
            pending.accounts[0] if pending.accounts else None,
        )
        if account is None:
            return {"error": {"message": "Conta não encontrada."}}

        # Resolve optional category
        category_id = None
        cat_name = args.get("category_name")
        if cat_name:
            cat = next(
                (
                    c
                    for c in pending.categories
                    if cat_name.lower() in c["name"].lower()
                ),
                None,
            )
            if cat:
                category_id = UUID(cat["id"])

        # Normalise date
        tx_date = args.get("transaction_date") or now.strftime("%Y-%m-%dT%H:%M:%SZ")
        if len(tx_date) == 10:  # date-only (YYYY-MM-DD)
            tx_date = f"{tx_date}T12:00:00Z"

        return UIService.record_transaction(
            amount=args["amount"],
            transaction_type=args["transaction_type"],
            source_account_id=UUID(account["id"]),
            category_id=category_id,
            description=args.get("description", ""),
            transaction_date=tx_date,
        )

    if pending.tool_name == "create_account":
        return UIService.create_account(
            name=args["name"],
            account_type=args.get("account_type", "checking"),
            initial_balance=args.get("initial_balance", "0.00"),
        )

    return {"error": {"message": f"Ação desconhecida: {pending.tool_name}"}}


# ---------------------------------------------------------------------------
# Action summary builder
# ---------------------------------------------------------------------------


def _build_action_summary(
    name: str,
    args: dict[str, Any],
    accounts: list[dict],
    categories: list[dict],
) -> str:
    if name == "record_transaction":
        tx_type = "Receita" if args.get("transaction_type") == "income" else "Despesa"
        try:
            amount_fmt = (
                f"R$ {float(args.get('amount', '0')):,.2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )
        except ValueError:
            amount_fmt = f"R$ {args.get('amount', '?')}"
        date = args.get("transaction_date") or datetime.now(UTC).strftime("%Y-%m-%d")
        return (
            f"**{tx_type}** de **{amount_fmt}** — {args.get('description', '')} | "
            f"Conta: **{args.get('account_name', '?')}** | "
            f"Categoria: {args.get('category_name', '—')} | Data: {date}"
        )
    if name == "create_account":
        type_labels = {
            "checking": "Corrente",
            "savings": "Poupança",
            "investment": "Investimento",
            "cash": "Carteira/Dinheiro",
        }
        acc_type_label = type_labels.get(
            args.get("account_type", "checking"), args.get("account_type", "?")
        )
        initial = args.get("initial_balance", "0.00")
        try:
            initial_fmt = (
                f"R$ {float(initial):,.2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )
        except ValueError:
            initial_fmt = f"R$ {initial}"
        return (
            f"Criar conta **{args.get('name', '?')}** | "
            f"Tipo: {acc_type_label} | Saldo inicial: {initial_fmt}"
        )
    return f"Ação: `{name}` com argumentos `{args}`"


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
Você é o **Contas Assistant**, um assistente financeiro pessoal inteligente e simpático.
Você tem acesso às finanças do usuário: contas, saldos, extratos, categorias e orçamentos.

Diretrizes:
- Responda sempre em Português do Brasil.
- Seja conciso mas completo. Use markdown quando útil (listas, negrito, tabelas simples).
- Para consultas, use as ferramentas disponíveis para buscar dados atualizados antes de responder.
- Para criar contas (create_account) ou registrar transações (record_transaction), o sistema exibirá uma tela de confirmação — não execute sem ela.
- Formate valores monetários sempre como R$ X.XXX,XX (padrão brasileiro).
- Se dados de ferramentas contiverem um campo "error", informe o usuário de forma amigável.
- Se o usuário pedir algo que não é possível com os dados disponíveis, explique gentilmente.
"""

_WRITE_TOOLS: frozenset[str] = frozenset({"record_transaction", "create_account"})


# ---------------------------------------------------------------------------
# Main chat function
# ---------------------------------------------------------------------------


def chat_with_financial_assistant(
    messages: list[dict[str, Any]],
    client: OpenAI | None = None,
    model: str = "gpt-4o-mini",
) -> tuple[str, PendingAction | None]:
    """Run one conversational turn with the financial assistant.

    Args:
        messages: Full conversation history (role/content dicts), WITHOUT system prompt.
        client: OpenAI client — injected for unit testing; created from settings if None.
        model: OpenAI model identifier.

    Returns:
        A tuple of (reply_text, pending_action):
        - reply_text: The assistant's plain-text/markdown reply.
        - pending_action: If not None, a write operation awaiting user confirmation in the UI.
    """
    if client is None:
        api_key = settings.effective_openai_api_key
        if not api_key:
            raise ValueError(
                "Chave da OpenAI não configurada. "
                "Defina a variável de ambiente OPENAPI_KEY ou OPENAI_API_KEY."
            )
        client = OpenAI(api_key=api_key)

    # Load lightweight context once per turn
    accounts: list[dict] = UIService.list_accounts().get("accounts", [])
    categories: list[dict] = UIService.list_categories().get("categories", [])

    full_messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *messages,
    ]

    # Agentic loop: keep resolving tool_calls until plain text reply or max iterations
    for _ in range(6):
        response = client.chat.completions.create(
            model=model,
            messages=full_messages,
            tools=_TOOLS,
            tool_choice="auto",
        )

        msg = response.choices[0].message
        full_messages.append(msg.model_dump(exclude_unset=False))

        if not msg.tool_calls:
            return msg.content or "", None

        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args: dict[str, Any] = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            if name in _WRITE_TOOLS:
                # Return early — UI must handle confirmation
                summary = _build_action_summary(name, args, accounts, categories)
                pending = PendingAction(
                    tool_name=name,
                    arguments=args,
                    summary=summary,
                    accounts=accounts,
                    categories=categories,
                )
                reply = (
                    msg.content
                    or "Encontrei o lançamento para registrar. Confirme os dados abaixo antes de efetivar:"
                )
                return reply, pending

            # Read-only: execute and feed result back to the model
            tool_result = _execute_read_tool(name, args, accounts, categories)
            full_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": tool_result,
                }
            )

    return (
        "Não consegui concluir após várias tentativas. Tente reformular sua pergunta.",
        None,
    )
