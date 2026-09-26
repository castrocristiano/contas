"""Unit tests for financial_chat service — strict mock-only, no real OpenAI calls."""

from unittest.mock import MagicMock, patch

import pytest

from contas.services.financial_chat import (
    PendingAction,
    _build_action_summary,
    _execute_read_tool,
    chat_with_financial_assistant,
    execute_pending_action,
)

# ---------------------------------------------------------------------------
# Helpers to build mock OpenAI responses
# ---------------------------------------------------------------------------


def _mock_text_response(content: str) -> MagicMock:
    """Simulate a plain-text assistant response (no tool_calls)."""
    msg = MagicMock()
    msg.tool_calls = None
    msg.content = content
    msg.model_dump.return_value = {
        "role": "assistant",
        "content": content,
        "tool_calls": None,
    }

    response = MagicMock()
    response.choices = [MagicMock(message=msg)]
    return response


def _mock_tool_call_response(
    tool_name: str, arguments: dict, content: str = ""
) -> MagicMock:
    """Simulate an assistant response that contains a single tool call."""
    import json

    tc = MagicMock()
    tc.id = "call_abc123"
    tc.function.name = tool_name
    tc.function.arguments = json.dumps(arguments)

    msg = MagicMock()
    msg.tool_calls = [tc]
    msg.content = content
    msg.model_dump.return_value = {
        "role": "assistant",
        "content": content,
        "tool_calls": [
            {
                "id": "call_abc123",
                "function": {"name": tool_name, "arguments": json.dumps(arguments)},
            }
        ],
    }

    response = MagicMock()
    response.choices = [MagicMock(message=msg)]
    return response


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_simple_reply_no_tools():
    """Model responds with plain text — no tool_calls — reply is returned as-is."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_text_response(
        "Olá! Como posso ajudar com suas finanças?"
    )

    with patch("contas.services.financial_chat.UIService") as mock_ui:
        mock_ui.list_accounts.return_value = {"accounts": []}
        mock_ui.list_categories.return_value = {"categories": []}

        reply, pending = chat_with_financial_assistant(
            messages=[{"role": "user", "content": "Olá!"}],
            client=mock_client,
        )

    assert reply == "Olá! Como posso ajudar com suas finanças?"
    assert pending is None


def test_tool_call_list_accounts_returns_final_reply():
    """Model calls list_accounts, gets results, then returns a text reply."""
    mock_client = MagicMock()

    # First call: tool invocation
    mock_client.chat.completions.create.side_effect = [
        _mock_tool_call_response("list_accounts", {}),
        _mock_text_response(
            "Você tem 2 contas: Nubank (R$ 1.000,00) e Bradesco (R$ 2.500,00)."
        ),
    ]

    accounts = [
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "name": "Nubank",
            "balance": "1000.00",
        },
        {
            "id": "00000000-0000-0000-0000-000000000002",
            "name": "Bradesco",
            "balance": "2500.00",
        },
    ]

    with patch("contas.services.financial_chat.UIService") as mock_ui:
        mock_ui.list_accounts.return_value = {"accounts": accounts}
        mock_ui.list_categories.return_value = {"categories": []}

        reply, pending = chat_with_financial_assistant(
            messages=[{"role": "user", "content": "Qual meu saldo?"}],
            client=mock_client,
        )

    assert "Nubank" in reply or "Bradesco" in reply
    assert pending is None
    assert mock_client.chat.completions.create.call_count == 2


def test_write_tool_returns_pending_action_without_executing():
    """When model calls record_transaction, function returns PendingAction — no DB write."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_tool_call_response(
        "record_transaction",
        {
            "amount": "80.00",
            "transaction_type": "expense",
            "account_name": "Nubank",
            "description": "Supermercado",
        },
        content="Vou registrar essa despesa. Confirme abaixo:",
    )

    accounts = [
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "name": "Nubank",
            "balance": "500.00",
        }
    ]

    with patch("contas.services.financial_chat.UIService") as mock_ui:
        mock_ui.list_accounts.return_value = {"accounts": accounts}
        mock_ui.list_categories.return_value = {"categories": []}

        _reply, pending = chat_with_financial_assistant(
            messages=[{"role": "user", "content": "Lance R$ 80 de supermercado"}],
            client=mock_client,
        )

    assert pending is not None
    assert isinstance(pending, PendingAction)
    assert pending.tool_name == "record_transaction"
    assert pending.arguments["amount"] == "80.00"
    assert pending.arguments["account_name"] == "Nubank"
    # UIService.record_transaction must NOT have been called yet
    mock_ui.record_transaction.assert_not_called()


def test_execute_pending_action_calls_record_transaction():
    """execute_pending_action delegates to UIService.record_transaction with resolved IDs."""
    from uuid import UUID

    accounts = [
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "name": "Nubank",
            "balance": "500.00",
        }
    ]
    categories = [
        {
            "id": "aaaaaaaa-0000-0000-0000-000000000001",
            "name": "Alimentação",
            "category_type": "expense",
        }
    ]

    pending = PendingAction(
        tool_name="record_transaction",
        arguments={
            "amount": "80.00",
            "transaction_type": "expense",
            "account_name": "Nubank",
            "description": "Supermercado",
            "category_name": "Alimentação",
            "transaction_date": "2026-09-20",
        },
        summary="Despesa de R$ 80,00 — Supermercado | Conta: Nubank",
        accounts=accounts,
        categories=categories,
    )

    with patch("contas.services.financial_chat.UIService") as mock_ui:
        mock_ui.record_transaction.return_value = {"id": "tx-001", "amount": "80.00"}

        result = execute_pending_action(pending)

    mock_ui.record_transaction.assert_called_once()
    call_kwargs = mock_ui.record_transaction.call_args.kwargs
    assert call_kwargs["amount"] == "80.00"
    assert call_kwargs["transaction_type"] == "expense"
    assert call_kwargs["source_account_id"] == UUID(
        "00000000-0000-0000-0000-000000000001"
    )
    assert call_kwargs["category_id"] == UUID("aaaaaaaa-0000-0000-0000-000000000001")
    assert call_kwargs["description"] == "Supermercado"
    assert result == {"id": "tx-001", "amount": "80.00"}


def test_execute_pending_action_record_installment_transaction():
    """execute_pending_action forwards total_installments and calculates total_amount if missing."""
    from uuid import UUID

    accounts = [
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "name": "PicPay",
            "balance": "1000.00",
        }
    ]

    pending = PendingAction(
        tool_name="record_transaction",
        arguments={
            "amount": "216.81",
            "transaction_type": "expense",
            "account_name": "PicPay",
            "description": "QUINJALMO",
            "total_installments": 10,
        },
        summary="Parcelamento em 10x de R$ 216,81",
        accounts=accounts,
        categories=[],
    )

    with patch("contas.services.financial_chat.UIService") as mock_ui:
        mock_ui.record_transaction.return_value = {
            "id": "tx-001",
            "installment_id": "inst-123",
            "total_installments": 10,
        }

        result = execute_pending_action(pending)

    mock_ui.record_transaction.assert_called_once()
    call_kwargs = mock_ui.record_transaction.call_args.kwargs
    assert call_kwargs["amount"] == "216.81"
    assert call_kwargs["total_installments"] == 10
    assert call_kwargs["total_amount"] == "2168.10"
    assert call_kwargs["source_account_id"] == UUID(
        "00000000-0000-0000-0000-000000000001"
    )
    assert result["total_installments"] == 10


def test_build_action_summary_expense_installment():
    """_build_action_summary formats installment purchases with total amount."""
    summary = _build_action_summary(
        "record_transaction",
        {
            "amount": "216.81",
            "transaction_type": "expense",
            "account_name": "PicPay",
            "description": "QUINJALMO",
            "total_installments": 10,
            "total_amount": "2168.10",
        },
        accounts=[],
        categories=[],
    )
    assert "10x de R$ 216,81" in summary
    assert "Total: R$ 2.168,10" in summary
    assert "QUINJALMO" in summary
    assert "PicPay" in summary


def test_execute_read_tool_list_accounts():
    """_execute_read_tool for list_accounts returns JSON with accounts from UIService."""
    import json

    accounts = [{"id": "abc", "name": "Nubank", "balance": "500.00"}]

    with patch("contas.services.financial_chat.UIService") as mock_ui:
        mock_ui.list_accounts.return_value = {"accounts": accounts}

        result = _execute_read_tool(
            "list_accounts", {}, accounts=accounts, categories=[]
        )

    data = json.loads(result)
    assert data["accounts"][0]["name"] == "Nubank"


def test_execute_read_tool_get_statement_defaults():
    """_execute_read_tool for get_statement handles empty dates by defaulting to a broad range."""
    import json
    from uuid import UUID

    accounts = [
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "name": "Cartão Mãe",
            "balance": "-53.97",
        }
    ]

    with patch("contas.services.financial_chat.UIService") as mock_ui:
        mock_ui.get_statement.return_value = {
            "account": {"name": "Cartão Mãe"},
            "transactions": [{"id": "tx1", "description": "PICPAY", "amount": "32.99"}],
        }

        result = _execute_read_tool(
            "get_statement",
            {"account_name": "Cartão Mãe"},
            accounts=accounts,
            categories=[],
        )

    mock_ui.get_statement.assert_called_once()
    call_kwargs = mock_ui.get_statement.call_args.kwargs
    assert call_kwargs["account_id"] == UUID("00000000-0000-0000-0000-000000000001")
    assert "start_date" in call_kwargs
    assert "end_date" in call_kwargs
    data = json.loads(result)
    assert len(data["transactions"]) == 1


def test_chat_raises_without_api_key():
    """chat_with_financial_assistant raises ValueError when no API key is configured."""
    with patch("contas.services.financial_chat.settings") as mock_settings:
        mock_settings.effective_openai_api_key = ""

        with pytest.raises(ValueError, match="Chave da OpenAI"):
            chat_with_financial_assistant(messages=[{"role": "user", "content": "Olá"}])


def test_execute_read_tool_get_installment_plan():
    import json
    from uuid import UUID

    inst_uuid = "11111111-1111-1111-1111-111111111111"
    with patch("contas.services.financial_chat.UIService") as mock_ui:
        mock_ui.get_installment_plan.return_value = {
            "installment_id": inst_uuid,
            "description": "Notebook",
            "total_installments": 10,
            "paid_installments": 3,
            "remaining_installments": 7,
        }

        res = _execute_read_tool(
            "get_installment_plan",
            {"installment_id": inst_uuid},
            accounts=[],
            categories=[],
        )

    mock_ui.get_installment_plan.assert_called_once_with(installment_id=UUID(inst_uuid))
    data = json.loads(res)
    assert data["total_installments"] == 10


def test_execute_pending_action_create_category():
    pending = PendingAction(
        tool_name="create_category",
        arguments={"name": "Lazer", "category_type": "expense"},
        summary="Criar categoria de Despesa: **Lazer**",
    )
    with patch("contas.services.financial_chat.UIService") as mock_ui:
        mock_ui.create_category.return_value = {"id": "cat-1", "name": "Lazer"}
        res = execute_pending_action(pending)

    mock_ui.create_category.assert_called_once_with(
        name="Lazer", category_type="expense"
    )
    assert res["name"] == "Lazer"


def test_execute_pending_action_set_budget():
    from uuid import UUID

    cat_id = "22222222-2222-2222-2222-222222222222"
    categories = [{"id": cat_id, "name": "Alimentação"}]
    pending = PendingAction(
        tool_name="set_budget",
        arguments={
            "category_name": "Alimentação",
            "amount": "800.00",
            "month": 9,
            "year": 2026,
        },
        summary="Definir orçamento",
        categories=categories,
    )
    with patch("contas.services.financial_chat.UIService") as mock_ui:
        mock_ui.set_budget.return_value = {"id": "b-1", "amount": "800.00"}
        res = execute_pending_action(pending)

    mock_ui.set_budget.assert_called_once_with(
        category_id=UUID(cat_id),
        amount="800.00",
        month=9,
        year=2026,
    )
    assert res["amount"] == "800.00"


def test_execute_pending_action_delete_transaction():
    from uuid import UUID

    tx_id = "33333333-3333-3333-3333-333333333333"
    pending = PendingAction(
        tool_name="delete_transaction",
        arguments={"transaction_id": tx_id, "delete_all_installments": True},
        summary="Excluir lançamento",
    )
    with patch("contas.services.financial_chat.UIService") as mock_ui:
        mock_ui.delete_transaction.return_value = {
            "message": "Lançamento excluído com sucesso!"
        }
        res = execute_pending_action(pending)

    mock_ui.delete_transaction.assert_called_once_with(
        transaction_id=UUID(tx_id),
        delete_all_installments=True,
    )
    assert "excluído" in res["message"]


def test_execute_pending_action_delete_account():
    from uuid import UUID

    acc_id = "44444444-4444-4444-4444-444444444444"
    accounts = [{"id": acc_id, "name": "Conta Teste"}]
    pending = PendingAction(
        tool_name="delete_account",
        arguments={"account_name": "Conta Teste", "force_cascade": False},
        summary="Excluir/Desativar conta",
        accounts=accounts,
    )
    with patch("contas.services.financial_chat.UIService") as mock_ui:
        mock_ui.delete_account.return_value = {
            "message": "Conta desativada com sucesso!"
        }
        res = execute_pending_action(pending)

    mock_ui.delete_account.assert_called_once_with(
        account_id=UUID(acc_id),
        force_cascade=False,
    )
    assert "desativada" in res["message"]


def test_execute_pending_action_delete_accounts_bulk():

    acc_1_id = "44444444-4444-4444-4444-444444444441"
    acc_2_id = "44444444-4444-4444-4444-444444444442"
    accounts = [
        {"id": acc_1_id, "name": "Conta 1"},
        {"id": acc_2_id, "name": "Conta 2"},
    ]
    pending = PendingAction(
        tool_name="delete_account",
        arguments={"account_names": ["Conta 1", "Conta 2"], "force_cascade": True},
        summary="Excluir 2 contas em lote",
        accounts=accounts,
    )
    with patch("contas.services.financial_chat.UIService") as mock_ui:
        mock_ui.delete_account.return_value = {
            "message": "Conta processada com sucesso!"
        }
        res = execute_pending_action(pending)

    assert mock_ui.delete_account.call_count == 2
    assert res["success_count"] == 2
    assert "2 conta(s)" in res["message"]


def test_build_action_summary_all_write_tools():
    s_cat = _build_action_summary(
        "create_category", {"name": "Mercado", "category_type": "expense"}, [], []
    )
    assert "Mercado" in s_cat and "Despesa" in s_cat

    s_bud = _build_action_summary(
        "set_budget",
        {"category_name": "Lazer", "amount": "500.00", "month": 10, "year": 2026},
        [],
        [],
    )
    assert "Lazer" in s_bud and "500,00" in s_bud and "10/2026" in s_bud

    s_del_tx = _build_action_summary(
        "delete_transaction",
        {
            "transaction_id": "tx12345678",
            "description": "Gasolina",
            "delete_all_installments": False,
        },
        [],
        [],
    )
    assert "Gasolina" in s_del_tx and "estornado" in s_del_tx

    s_del_acc = _build_action_summary(
        "delete_account",
        {"account_name": "Nubank Antiga", "force_cascade": True},
        [],
        [],
    )
    assert "Nubank Antiga" in s_del_acc and "ATENÇÃO" in s_del_acc

    s_del_accs = _build_action_summary(
        "delete_account",
        {"account_names": ["Conta A", "Conta B"], "force_cascade": False},
        [],
        [],
    )
    assert "2 contas em lote" in s_del_accs
    assert "Conta A" in s_del_accs and "Conta B" in s_del_accs


def test_chat_logging(caplog):
    """Verify that financial_chat logs start of turn, tool execution, and replies."""
    import logging

    client = MagicMock()
    client.chat.completions.create.return_value = _mock_text_response(
        "Olá! Como posso ajudar?"
    )

    with caplog.at_level(logging.INFO):
        reply, pending = chat_with_financial_assistant(
            messages=[{"role": "user", "content": "Olá assistente"}],
            client=client,
        )

    assert reply == "Olá! Como posso ajudar?"
    assert pending is None
    assert any("Starting chat turn" in record.message for record in caplog.records)
    assert any(
        "Last user message: Olá assistente" in record.message
        for record in caplog.records
    )
    assert any(
        "Chat turn completed with text reply" in record.message
        for record in caplog.records
    )
