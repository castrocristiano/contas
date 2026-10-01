from decimal import Decimal
from typing import Any
from uuid import UUID

from contas.application.ports.repositories import (
    IAccountRepository,
    ITransactionRepository,
)
from contas.domain.entities import Account
from contas.domain.enums import AccountType
from contas.domain.errors import AccountNotFoundError
from contas.schemas.account import (
    AccountResponse,
    AccountSummary,
    CreateAccountInput,
    DeleteAccountInput,
    DeleteAccountResponse,
    ListAccountsInput,
    ListAccountsResponse,
)


class CreateAccountUseCase:
    def __init__(self, account_repo: IAccountRepository) -> None:
        self.account_repo = account_repo

    async def execute(self, payload: CreateAccountInput) -> dict[str, Any]:
        account = Account(
            name=payload.name,
            account_type=AccountType(payload.account_type),
            balance=Decimal(payload.initial_balance),
            currency=payload.currency,
        )
        created = await self.account_repo.create(account)
        response = AccountResponse(
            id=created.id,
            name=created.name,
            account_type=created.account_type,
            balance=f"{created.balance:.2f}",
            currency=created.currency,
            is_active=created.is_active,
            created_at=created.created_at,
        )
        return response.model_dump(mode="json")


class ListAccountsUseCase:
    def __init__(self, account_repo: IAccountRepository) -> None:
        self.account_repo = account_repo

    async def execute(self, payload: ListAccountsInput) -> dict[str, Any]:
        accounts = await self.account_repo.list_all(
            only_active=not payload.include_inactive,
            limit=1000,
        )
        total = sum((acc.balance for acc in accounts), start=0)
        currency = accounts[0].currency if accounts else "BRL"

        summaries = [
            AccountSummary(
                id=acc.id,
                name=acc.name,
                account_type=acc.account_type,
                balance=f"{acc.balance:.2f}",
                currency=acc.currency,
                is_active=acc.is_active,
            )
            for acc in accounts
        ]
        response = ListAccountsResponse(
            accounts=summaries,
            total_balance=f"{total:.2f}",
            currency=currency,
            count=len(summaries),
        )
        return response.model_dump(mode="json")


class DeleteAccountUseCase:
    def __init__(
        self,
        account_repo: IAccountRepository,
        transaction_repo: ITransactionRepository,
    ) -> None:
        self.account_repo = account_repo
        self.transaction_repo = transaction_repo

    async def execute(self, payload: DeleteAccountInput) -> dict[str, Any]:
        account = await self.account_repo.get_by_id(
            payload.account_id, only_active=False
        )
        if not account:
            raise AccountNotFoundError(str(payload.account_id))

        tx_count = await self.transaction_repo.count_by_account(payload.account_id)

        if tx_count > 0 and not payload.force_cascade:
            account.is_active = False
            await self.account_repo.update(account)
            action_taken = "deactivated"
            message = f"Account '{account.name}' has {tx_count} transaction(s) and was deactivated."
        else:
            await self.account_repo.delete(payload.account_id)
            action_taken = "deleted"
            message = f"Account '{account.name}' was permanently deleted."

        return DeleteAccountResponse(
            account_id=payload.account_id,
            name=account.name,
            action_taken=action_taken,
            message=message,
        ).model_dump(mode="json")


class BulkDeleteAccountsUseCase:
    def __init__(self, account_repo: IAccountRepository) -> None:
        self.account_repo = account_repo

    async def execute(
        self, account_ids: list[UUID], force_cascade: bool = False
    ) -> int:
        return await self.account_repo.bulk_delete(account_ids, cascade=force_cascade)
