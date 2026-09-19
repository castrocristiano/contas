from uuid import uuid4

import pytest
from pydantic import ValidationError

from contas.models.account import AccountType
from contas.models.transaction import TransactionStatus, TransactionType
from contas.schemas.account import CreateAccountInput
from contas.schemas.transaction import RecordTransactionInput


def test_create_account_input_valid():
    payload = CreateAccountInput(
        name="Conta Corrente",
        account_type=AccountType.CHECKING,
        initial_balance="1500.00",
        currency="BRL",
    )
    assert payload.name == "Conta Corrente"
    assert payload.account_type == AccountType.CHECKING
    assert payload.initial_balance == "1500.00"
    assert payload.currency == "BRL"


def test_create_account_input_rejects_empty_name():
    with pytest.raises(ValidationError):
        CreateAccountInput(
            name="",
            account_type=AccountType.CHECKING,
        )


def test_create_account_input_rejects_invalid_currency():
    with pytest.raises(ValidationError):
        CreateAccountInput(
            name="Conta Teste",
            account_type=AccountType.CHECKING,
            currency="br",  # Lowercase and only 2 chars
        )


def test_create_account_input_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        CreateAccountInput(
            name="Conta Teste",
            account_type=AccountType.CHECKING,
            unexpected_field="invalid",
        )


def test_record_transaction_input_valid_expense():
    source_id = uuid4()
    payload = RecordTransactionInput(
        amount="35.50",
        transaction_type=TransactionType.EXPENSE,
        source_account_id=source_id,
        description="Supermercado",
    )
    assert payload.amount == "35.50"
    assert payload.transaction_type == TransactionType.EXPENSE
    assert payload.status == TransactionStatus.CLEARED


def test_record_transaction_input_rejects_zero_amount():
    with pytest.raises(ValidationError):
        RecordTransactionInput(
            amount="0.00",
            transaction_type=TransactionType.EXPENSE,
            source_account_id=uuid4(),
        )


def test_record_transaction_input_rejects_negative_amount():
    with pytest.raises(ValidationError):
        RecordTransactionInput(
            amount="-10.00",
            transaction_type=TransactionType.EXPENSE,
            source_account_id=uuid4(),
        )


def test_record_transaction_input_rejects_invalid_amount_format():
    with pytest.raises(ValidationError):
        RecordTransactionInput(
            amount="abc",
            transaction_type=TransactionType.EXPENSE,
            source_account_id=uuid4(),
        )


def test_record_transaction_input_transfer_requires_destination():
    with pytest.raises(ValidationError, match="destination_account_id is required"):
        RecordTransactionInput(
            amount="50.00",
            transaction_type=TransactionType.TRANSFER,
            source_account_id=uuid4(),
            destination_account_id=None,
        )


def test_record_transaction_input_transfer_rejects_same_account():
    same_id = uuid4()
    with pytest.raises(ValidationError, match="must be different"):
        RecordTransactionInput(
            amount="50.00",
            transaction_type=TransactionType.TRANSFER,
            source_account_id=same_id,
            destination_account_id=same_id,
        )
