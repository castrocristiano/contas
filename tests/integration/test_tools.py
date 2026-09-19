from decimal import Decimal
from uuid import uuid4

import pytest
from sqlmodel import select

from contas.db.session import get_session
from contas.models.account import Account, AccountType
from contas.models.transaction import TransactionType
from contas.schemas.account import CreateAccountInput
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
