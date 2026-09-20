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


def test_build_action_summary_expense():
    """_build_action_summary produces a human-readable confirmation string."""
    summary = _build_action_summary(
        "record_transaction",
        {
            "amount": "99.90",
            "transaction_type": "expense",
            "account_name": "Nubank",
            "description": "Farmácia",
            "category_name": "Saúde",
            "transaction_date": "2026-09-15",
        },
        accounts=[],
        categories=[],
    )
    assert "Despesa" in summary
    assert "99,90" in summary
    assert "Farmácia" in summary
    assert "Nubank" in summary
    assert "Saúde" in summary


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


def test_chat_raises_without_api_key():
    """chat_with_financial_assistant raises ValueError when no API key is configured."""
    with patch("contas.services.financial_chat.settings") as mock_settings:
        mock_settings.effective_openai_api_key = ""

        with pytest.raises(ValueError, match="Chave da OpenAI"):
            chat_with_financial_assistant(messages=[{"role": "user", "content": "Olá"}])
