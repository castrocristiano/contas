"""Financial chat assistant using OpenAI function calling.

The assistant has read-only and write tools mapped to UIService operations.
Write operations (record_transaction) return a PendingAction instead of executing
immediately — the UI layer is responsible for showing a confirmation step.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from openai import OpenAI

from contas.config import settings
from contas.ui.services import UIService

logger = logging.getLogger(__name__)

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
                        "description": "Data inicial no formato YYYY-MM-DD. Se não informada, busca desde o início do ano anterior ou período amplo.",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Data final no formato YYYY-MM-DD. Se não informada, busca até o final do ano corrente ou futuro.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Número máximo de transações a retornar. Padrão 50.",
                        "default": 50,
                    },
                },
                "required": [],
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
                    "total_installments": {
                        "type": "integer",
                        "description": (
                            "Quantidade total de parcelas (ex: 10). "
                            "Use OBRIGATORIAMENTE quando a compra for parcelada ou em várias vezes."
                        ),
                    },
                    "total_amount": {
                        "type": "string",
                        "description": (
                            "Valor total da compra (ex: '2168.10'). "
                            "Se o usuário informar apenas o valor de cada parcela (ex: 10 vezes de 216.81), "
                            "calcule total_amount = parcela * total_installments (2168.10)."
                        ),
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
    {
        "type": "function",
        "function": {
            "name": "create_category",
            "description": (
                "Cria uma nova categoria financeira para receitas ou despesas."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Nome da categoria (ex: 'Educação', 'Lazer', 'Freelance').",
                    },
                    "category_type": {
                        "type": "string",
                        "enum": ["income", "expense"],
                        "description": "Tipo da categoria: 'income' para receita, 'expense' para despesa.",
                    },
                },
                "required": ["name", "category_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_budget",
            "description": (
                "Define ou atualiza o limite mensal de orçamento para uma categoria de despesa específica."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category_name": {
                        "type": "string",
                        "description": "Nome da categoria de despesa.",
                    },
                    "amount": {
                        "type": "string",
                        "description": "Limite monetário mensal em decimal positivo com ponto (ex: '600.00').",
                    },
                    "month": {
                        "type": "integer",
                        "description": "Mês de referência (1-12). Padrão: mês atual.",
                    },
                    "year": {
                        "type": "integer",
                        "description": "Ano de referência (ex: 2026). Padrão: ano atual.",
                    },
                },
                "required": ["category_name", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_installment_plan",
            "description": (
                "Recupera o cronograma completo de um parcelamento pelo seu ID (installment_id), "
                "detalhando parcelas pagas, parcelas restantes, valores e datas de vencimento."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "installment_id": {
                        "type": "string",
                        "description": "UUID do parcelamento (encontrado nos detalhes da transação).",
                    },
                },
                "required": ["installment_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_transaction",
            "description": (
                "Exclui uma transação financeira. Se a transação estiver liquidada, o saldo será estornado automaticamente. "
                "Para compras parceladas, pode excluir apenas a parcela ou todas as parcelas do plano."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "UUID da transação a ser excluída.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Breve descrição ou motivo para conferência pelo usuário.",
                    },
                    "delete_all_installments": {
                        "type": "boolean",
                        "description": "Se True e for compra parcelada, exclui todas as parcelas do plano. Padrão: False.",
                        "default": False,
                    },
                },
                "required": ["transaction_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_account",
            "description": (
                "Exclui ou desativa uma ou mais contas financeiras. "
                "Pode receber o nome de uma única conta (`account_name`) ou uma lista de nomes de contas (`account_names`) para exclusão em lote. "
                "Se force_cascade for True, remove todas as transações associadas permanentemente e deleta as contas."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "account_name": {
                        "type": "string",
                        "description": "Nome de uma única conta a ser excluída/desativada (quando for apenas uma).",
                    },
                    "account_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista com os nomes das contas a serem excluídas/desativadas em lote (quando forem várias contas).",
                    },
                    "force_cascade": {
                        "type": "boolean",
                        "description": "Se True, força a exclusão em cascata de todas as transações vinculadas permanentemente.",
                        "default": False,
                    },
                },
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
    logger.debug("Executing read tool: %s with arguments: %s", name, args)

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
            logger.warning("No account found for get_statement: %s", account_name)
            return json.dumps({"error": "Nenhuma conta encontrada."})

        # Sensible defaults if not specified: cover broad range to not miss transactions
        start_date = args.get("start_date") or f"{now.year - 1}-01-01"
        end_date = args.get("end_date") or f"{now.year + 2}-12-31"

        from uuid import UUID

        result = UIService.get_statement(
            account_id=UUID(account["id"]),
            start_date=start_date,
            end_date=end_date,
            limit=args.get("limit", 50),
        )
        return json.dumps(result, ensure_ascii=False, default=str)

    if name == "get_budget_status":
        result = UIService.get_budget_status(
            month=args.get("month", now.month),
            year=args.get("year", now.year),
        )
        return json.dumps(result, ensure_ascii=False, default=str)

    if name == "get_installment_plan":
        from uuid import UUID

        inst_id = args.get("installment_id")
        if not inst_id:
            logger.warning("installment_id is missing for get_installment_plan")
            return json.dumps({"error": "Parâmetro 'installment_id' é obrigatório."})
        result = UIService.get_installment_plan(installment_id=UUID(inst_id))
        return json.dumps(result, ensure_ascii=False, default=str)

    logger.warning("Unknown read tool requested: %s", name)
    return json.dumps({"error": f"Ferramenta desconhecida: {name}"})


# ---------------------------------------------------------------------------
# Write action executor (called only after user confirmation)
# ---------------------------------------------------------------------------


def execute_pending_action(pending: PendingAction) -> dict[str, Any]:
    """Execute a confirmed write action and return the result dict."""
    from uuid import UUID

    args = pending.arguments
    now = datetime.now(UTC)
    logger.info(
        "Executing pending write action: %s with arguments: %s", pending.tool_name, args
    )

    if pending.tool_name == "record_transaction":
        # Resolve account by name
        account_name = args.get("account_name", "")
        account = next(
            (a for a in pending.accounts if account_name.lower() in a["name"].lower()),
            pending.accounts[0] if pending.accounts else None,
        )
        if account is None:
            logger.warning("Account not found for record_transaction: %s", account_name)
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

        # Handle installment arguments
        total_installments = args.get("total_installments")
        total_amount = args.get("total_amount")
        if (
            total_installments is not None
            and total_installments > 1
            and not total_amount
        ):
            try:
                from decimal import Decimal

                total_amount = f"{Decimal(args['amount']) * total_installments:.2f}"
            except Exception:  # noqa: BLE001
                total_amount = None

        res = UIService.record_transaction(
            amount=args["amount"],
            transaction_type=args["transaction_type"],
            source_account_id=UUID(account["id"]),
            category_id=category_id,
            description=args.get("description", ""),
            transaction_date=tx_date,
            total_installments=total_installments,
            total_amount=total_amount,
        )
        logger.info("record_transaction result: %s", res)
        return res

    if pending.tool_name == "create_account":
        res = UIService.create_account(
            name=args["name"],
            account_type=args.get("account_type", "checking"),
            initial_balance=args.get("initial_balance", "0.00"),
        )
        logger.info("create_account result: %s", res)
        return res

    if pending.tool_name == "create_category":
        res = UIService.create_category(
            name=args["name"],
            category_type=args["category_type"],
        )
        logger.info("create_category result: %s", res)
        return res

    if pending.tool_name == "set_budget":
        cat_name = args.get("category_name", "")
        category = next(
            (c for c in pending.categories if cat_name.lower() in c["name"].lower()),
            None,
        )
        if not category:
            logger.warning("Category not found for set_budget: %s", cat_name)
            return {"error": {"message": f"Categoria '{cat_name}' não encontrada."}}

        month = args.get("month") or now.month
        year = args.get("year") or now.year

        res = UIService.set_budget(
            category_id=UUID(category["id"]),
            amount=args["amount"],
            month=month,
            year=year,
        )
        logger.info("set_budget result: %s", res)
        return res

    if pending.tool_name == "delete_transaction":
        tx_id_str = args.get("transaction_id")
        if not tx_id_str:
            return {"error": {"message": "ID da transação não fornecido."}}
        res = UIService.delete_transaction(
            transaction_id=UUID(tx_id_str),
            delete_all_installments=args.get("delete_all_installments", False),
        )
        logger.info("delete_transaction result: %s", res)
        return res

    if pending.tool_name == "delete_account":
        force_cascade = args.get("force_cascade", False)
        acc_names = args.get("account_names") or []
        if not acc_names and args.get("account_name"):
            acc_names = [args["account_name"]]

        if not acc_names:
            return {"error": {"message": "Nenhuma conta informada para exclusão."}}

        success_accounts = []
        errors = []

        for name in acc_names:
            account = next(
                (a for a in pending.accounts if name.lower() in a["name"].lower()),
                None,
            )
            if not account:
                errors.append(f"Conta '{name}' não encontrada.")
                continue

            res = UIService.delete_account(
                account_id=UUID(account["id"]),
                force_cascade=force_cascade,
            )
            if "error" in res:
                errors.append(
                    f"Conta '{name}': {res['error'].get('message', res['error'])}"
                )
            else:
                success_accounts.append(account["name"])

        if errors and not success_accounts:
            logger.warning("delete_account errors: %s", errors)
            return {"error": {"message": "; ".join(errors)}}

        msg = f"{len(success_accounts)} conta(s) excluída(s)/desativada(s) com sucesso ({', '.join(success_accounts)})."
        if errors:
            msg += f" Erros: {'; '.join(errors)}"
        logger.info("delete_account completed: %s", msg)
        return {"message": msg, "success_count": len(success_accounts)}

    logger.error("Unknown pending action: %s", pending.tool_name)
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

        total_inst = args.get("total_installments")
        if total_inst is not None and total_inst > 1:
            tot_amt_str = args.get("total_amount")
            if not tot_amt_str:
                try:
                    tot_amt_str = f"{float(args.get('amount', '0')) * total_inst:.2f}"
                except ValueError:
                    tot_amt_str = None
            if tot_amt_str:
                try:
                    tot_fmt = (
                        f"R$ {float(tot_amt_str):,.2f}".replace(",", "X")
                        .replace(".", ",")
                        .replace("X", ".")
                    )
                except ValueError:
                    tot_fmt = f"R$ {tot_amt_str}"
                amount_fmt = f"{total_inst}x de {amount_fmt} (Total: {tot_fmt})"
            else:
                amount_fmt = f"{total_inst}x de {amount_fmt}"

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
    if name == "create_category":
        c_type = "Receita" if args.get("category_type") == "income" else "Despesa"
        return f"Criar categoria de {c_type}: **{args.get('name', '?')}**"

    if name == "set_budget":
        try:
            b_amount = (
                f"R$ {float(args.get('amount', '0')):,.2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )
        except ValueError:
            b_amount = f"R$ {args.get('amount', '?')}"
        m = args.get("month") or datetime.now(UTC).month
        y = args.get("year") or datetime.now(UTC).year
        return (
            f"Definir orçamento para **{args.get('category_name', '?')}** em **{b_amount}** "
            f"para o mês **{m:02d}/{y}**"
        )

    if name == "delete_transaction":
        inst_note = (
            " (todas as parcelas vinculadas)"
            if args.get("delete_all_installments")
            else ""
        )
        desc = (
            args.get("description") or f"ID `{args.get('transaction_id', '')[:8]}...`"
        )
        return (
            f"🗑️ **Excluir lançamento**: {desc}{inst_note}\n\n"
            f"*Atenção: Se o lançamento for liquidado, o saldo da conta será estornado automaticamente.*"
        )

    if name == "delete_account":
        force = args.get("force_cascade", False)
        force_note = (
            " ⚠️ **ATENÇÃO: Todas as transações da(s) conta(s) serão excluídas permanentemente!**"
            if force
            else " (desativação ou remoção se sem lançamentos)"
        )
        acc_names = args.get("account_names") or []
        if not acc_names and args.get("account_name"):
            acc_names = [args["account_name"]]

        if len(acc_names) > 1:
            names_str = ", ".join(f"**{n}**" for n in acc_names)
            return f"🗑️ **Excluir/Desativar {len(acc_names)} contas em lote**: {names_str}{force_note}"
        single_name = acc_names[0] if acc_names else args.get("account_name", "?")
        return f"🗑️ **Excluir/Desativar conta**: **{single_name}**{force_note}"

    return f"Ação: `{name}` com argumentos `{args}`"


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
Você é o **Contas Assistant**, um assistente financeiro pessoal inteligente e simpático.
Você tem acesso e controle completo sobre as finanças do usuário: contas, saldos, extratos, categorias e orçamentos.

Diretrizes:
- Responda sempre em Português do Brasil.
- Seja conciso mas completo. Use markdown quando útil (listas, negrito, tabelas simples).
- Para consultas de extrato e transações de uma conta, use a ferramenta `get_statement`. Se o usuário não especificar datas, use um período amplo (ou deixe sem datas) para capturar lançamentos passados, presentes ou futuros (como compras parceladas ou faturas com datas futuras).
- Se o saldo de uma conta estiver diferente de zero, sempre consulte o extrato dela antes de afirmar que não há transações.
- Para consultas de plano de parcelamento, use `get_installment_plan` informando o `installment_id`.
- Para qualquer alteração ou exclusão de dados (`create_account`, `create_category`, `set_budget`, `record_transaction`, `delete_transaction`, `delete_account`), o sistema SEMPRE exigirá confirmação do usuário na interface antes de efetivar.
- Ao registrar compras parceladas (`record_transaction`), se o usuário disser "em 10x", "em 10 vezes", "parcelado em 3x", etc., você DEVE preencher `total_installments`. Se o valor fornecido for o da parcela (ex: "10 vezes de 216.81"), preencha `amount="216.81"` e `total_amount="2168.10"`. Se o valor fornecido for o valor total (ex: "compra de 1000 em 10x"), preencha `total_amount="1000.00"` e `amount="100.00"`.
- Se o usuário pedir para excluir ou desativar múltiplas contas de uma só vez (ex: "apague as contas X, Y e Z"), use `delete_account` passando a lista de nomes no campo `account_names`.
- Se o usuário pedir para excluir um lançamento por descrição ou valor (sem saber o ID), primeiro consulte `get_statement` para obter o `id` da transação antes de propor a ação `delete_transaction`.
- Formate valores monetários sempre como R$ X.XXX,XX (padrão brasileiro).
- Se dados de ferramentas contiverem um campo "error", informe o usuário de forma amigável.
- Se o usuário pedir algo que não é possível com os dados disponíveis, explique gentilmente.
"""

_WRITE_TOOLS: frozenset[str] = frozenset(
    {
        "record_transaction",
        "create_account",
        "create_category",
        "set_budget",
        "delete_transaction",
        "delete_account",
    }
)


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

    logger.info("Starting chat turn with %d message(s)", len(messages))
    if messages:
        logger.info("Last user message: %s", messages[-1].get("content"))

    # Agentic loop: keep resolving tool_calls until plain text reply or max iterations
    for iteration in range(6):
        logger.debug(
            "Chat iteration %d: sending request to OpenAI (%s)", iteration + 1, model
        )
        response = client.chat.completions.create(
            model=model,
            messages=full_messages,
            tools=_TOOLS,
            tool_choice="auto",
        )

        msg = response.choices[0].message
        full_messages.append(msg.model_dump(exclude_unset=False))

        if not msg.tool_calls:
            logger.info(
                "Chat turn completed with text reply (length: %d)",
                len(msg.content or ""),
            )
            return msg.content or "", None

        logger.info("Model requested %d tool call(s)", len(msg.tool_calls))
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args: dict[str, Any] = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                logger.warning(
                    "Failed to decode arguments for tool %s: %s",
                    name,
                    tc.function.arguments,
                )
                args = {}

            logger.info("Tool called: %s | Args: %s", name, args)

            if name in _WRITE_TOOLS:
                # Return early — UI must handle confirmation
                logger.info(
                    "Write tool detected: %s. Returning PendingAction for UI confirmation.",
                    name,
                )
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

    logger.warning("Chat turn reached maximum iterations without completing.")
    return (
        "Não consegui concluir após várias tentativas. Tente reformular sua pergunta.",
        None,
    )
