from decimal import Decimal
from uuid import uuid4

import pytest
from sqlmodel import select

from contas.db.session import get_session
from contas.models.account import Account, AccountType
from contas.models.transaction import TransactionType
from contas.schemas.account import CreateAccountInput, UpdateAccountInput
from contas.schemas.transaction import RecordTransactionInput
from contas.server import create_server


@pytest.fixture
def server():
    return create_server()


@pytest.mark.anyio
async def test_record_transaction_nonexistent_account_returns_structured_error(server):
    record_handler = server._tool_manager._tools["record_transaction"].fn
    fake_id = uuid4()

    # When source account does not exist
    result = await record_handler(
        payload=RecordTransactionInput(
            amount="50.00",
            transaction_type=TransactionType.EXPENSE,
            source_account_id=fake_id,
        )
    )

    assert "error" in result
    assert result["error"]["code"] == "ACCOUNT_NOT_FOUND"
    assert result["error"]["details"]["field"] == "source_account_id"


@pytest.mark.anyio
async def test_record_transaction_transfer_same_account_returns_structured_error(
    server,
):
    create_handler = server._tool_manager._tools["create_account"].fn
    acc = await create_handler(
        payload=CreateAccountInput(
            name="Conta Mesma",
            account_type=AccountType.CHECKING,
            initial_balance="100.00",
        )
    )
    acc_id = acc["id"]

    # Validate model-level schema catches it
    with pytest.raises(ValueError, match="must be different"):
        RecordTransactionInput(
            amount="20.00",
            transaction_type=TransactionType.TRANSFER,
            source_account_id=acc_id,
            destination_account_id=acc_id,
        )

    # Verify database balance is unchanged
    async with get_session() as session:
        account_in_db = (
            await session.exec(select(Account).where(Account.id == acc_id))
        ).first()
        assert account_in_db is not None
        assert account_in_db.balance == Decimal("100.00")


@pytest.mark.anyio
async def test_record_transaction_with_due_date_and_credit_card_statement_filter(
    server,
):
    from contas.models.transaction import Transaction
    from contas.schemas.transaction import GetStatementInput

    create_acc_handler = server._tool_manager._tools["create_account"].fn
    record_handler = server._tool_manager._tools["record_transaction"].fn
    statement_handler = server._tool_manager._tools["get_statement"].fn

    # 1. Create credit_card account
    acc = await create_acc_handler(
        payload=CreateAccountInput(
            name="Cartão Black Integration",
            account_type=AccountType.CREDIT_CARD,
            initial_balance="0.00",
        )
    )
    acc_id = acc["id"]
    assert acc["account_type"] == "credit_card"

    async with get_session() as session:
        db_acc = (
            await session.exec(select(Account).where(Account.id == acc_id))
        ).first()
        assert db_acc is not None
        assert db_acc.account_type == AccountType.CREDIT_CARD

    # 2. Record tx1: bought in Oct, due in Nov
    tx1_res = await record_handler(
        payload=RecordTransactionInput(
            amount="150.00",
            transaction_type=TransactionType.EXPENSE,
            source_account_id=acc_id,
            description="Compra Outubro / Vence Novembro",
            transaction_date="2026-10-15T10:00:00Z",
            due_date="2026-11-10T10:00:00Z",
        )
    )
    assert "error" not in tx1_res
    tx1_id = tx1_res["id"]

    async with get_session() as session:
        db_tx1 = (
            await session.exec(select(Transaction).where(Transaction.id == tx1_id))
        ).first()
        assert db_tx1 is not None
        assert db_tx1.due_date is not None
        assert db_tx1.due_date.month == 11

    # 3. Record tx2: bought in Nov, due in Dec
    tx2_res = await record_handler(
        payload=RecordTransactionInput(
            amount="250.00",
            transaction_type=TransactionType.EXPENSE,
            source_account_id=acc_id,
            description="Compra Novembro / Vence Dezembro",
            transaction_date="2026-11-05T10:00:00Z",
            due_date="2026-12-10T10:00:00Z",
        )
    )
    assert "error" not in tx2_res

    # 4. Filter statement by transaction_date for Nov
    stmt_tx_date = await statement_handler(
        payload=GetStatementInput(
            account_id=acc_id,
            start_date="2026-11-01",
            end_date="2026-11-30",
            date_type="transaction_date",
        )
    )
    assert "error" not in stmt_tx_date
    tx_descs = [t["description"] for t in stmt_tx_date["transactions"]]
    assert "Compra Novembro / Vence Dezembro" in tx_descs
    assert "Compra Outubro / Vence Novembro" not in tx_descs

    # 5. Filter statement by due_date for Nov
    stmt_due_date = await statement_handler(
        payload=GetStatementInput(
            account_id=acc_id,
            start_date="2026-11-01",
            end_date="2026-11-30",
            date_type="due_date",
        )
    )
    assert "error" not in stmt_due_date
    due_descs = [t["description"] for t in stmt_due_date["transactions"]]
    assert "Compra Outubro / Vence Novembro" in due_descs
    assert "Compra Novembro / Vence Dezembro" not in due_descs


@pytest.mark.anyio
async def test_update_account_tool_success(server):
    create_handler = server._tool_manager._tools["create_account"].fn
    update_handler = server._tool_manager._tools["update_account"].fn

    acc = await create_handler(
        payload=CreateAccountInput(
            name="Conta Para Renomear",
            account_type=AccountType.CHECKING,
            initial_balance="150.00",
        )
    )
    acc_id = acc["id"]

    updated = await update_handler(
        payload=UpdateAccountInput(
            account_id=acc_id,
            name="Conta Renomeada Com Sucesso",
        )
    )
    assert "error" not in updated
    assert updated["id"] == str(acc_id)
    assert updated["name"] == "Conta Renomeada Com Sucesso"


@pytest.mark.anyio
async def test_update_account_tool_not_found(server):
    update_handler = server._tool_manager._tools["update_account"].fn
    fake_id = uuid4()

    result = await update_handler(
        payload=UpdateAccountInput(
            account_id=fake_id,
            name="Conta Fantasma",
        )
    )
    assert "error" in result
    assert result["error"]["code"] == "ACCOUNT_NOT_FOUND"
