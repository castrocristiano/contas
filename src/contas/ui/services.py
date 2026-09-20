import asyncio
from uuid import UUID

from contas.schemas.account import (
    CreateAccountInput,
    DeleteAccountInput,
    ListAccountsInput,
)
from contas.schemas.budget import GetBudgetStatusInput, SetBudgetInput
from contas.schemas.category import CreateCategoryInput, ListCategoriesInput
from contas.schemas.transaction import (
    DeleteTransactionInput,
    GetFinancialSummaryInput,
    GetInstallmentPlanInput,
    GetStatementInput,
    RecordTransactionInput,
)
from contas.server import create_server

_server = None


def get_mcp_server():
    global _server
    if _server is None:
        _server = create_server()
    return _server


def run_async(coro):
    """Safely run async coroutine in sync Streamlit context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


class UIService:
    @staticmethod
    def list_accounts(include_inactive: bool = False) -> dict:
        server = get_mcp_server()
        handler = server._tool_manager._tools["list_accounts"].fn
        return run_async(
            handler(payload=ListAccountsInput(include_inactive=include_inactive))
        )

    @staticmethod
    def create_account(name: str, account_type: str, initial_balance: str) -> dict:
        server = get_mcp_server()
        handler = server._tool_manager._tools["create_account"].fn
        return run_async(
            handler(
                payload=CreateAccountInput(
                    name=name,
                    account_type=account_type,
                    initial_balance=initial_balance,
                )
            )
        )

    @staticmethod
    def delete_account(account_id: UUID, force_cascade: bool = False) -> dict:
        server = get_mcp_server()
        handler = server._tool_manager._tools["delete_account"].fn
        return run_async(
            handler(
                payload=DeleteAccountInput(
                    account_id=account_id,
                    force_cascade=force_cascade,
                )
            )
        )

    @staticmethod
    def list_categories(
        category_type: str | None = None, include_inactive: bool = False
    ) -> dict:
        server = get_mcp_server()
        handler = server._tool_manager._tools["list_categories"].fn
        return run_async(
            handler(
                payload=ListCategoriesInput(
                    category_type=category_type,
                    include_inactive=include_inactive,
                )
            )
        )

    @staticmethod
    def create_category(name: str, category_type: str) -> dict:
        server = get_mcp_server()
        handler = server._tool_manager._tools["create_category"].fn
        return run_async(
            handler(
                payload=CreateCategoryInput(
                    name=name,
                    category_type=category_type,
                )
            )
        )

    @staticmethod
    def get_statement(
        account_id: UUID,
        start_date: str,
        end_date: str,
        include_pending: bool = True,
        limit: int = 100,
    ) -> dict:
        server = get_mcp_server()
        handler = server._tool_manager._tools["get_statement"].fn
        return run_async(
            handler(
                payload=GetStatementInput(
                    account_id=account_id,
                    start_date=start_date,
                    end_date=end_date,
                    include_pending=include_pending,
                    limit=limit,
                )
            )
        )

    @staticmethod
    def record_transaction(
        amount: str,
        transaction_type: str,
        source_account_id: UUID,
        destination_account_id: UUID | None = None,
        category_id: UUID | None = None,
        description: str = "",
        transaction_date: str | None = None,
        total_installments: int | None = None,
        total_amount: str | None = None,
    ) -> dict:
        server = get_mcp_server()
        handler = server._tool_manager._tools["record_transaction"].fn
        return run_async(
            handler(
                payload=RecordTransactionInput(
                    amount=amount,
                    transaction_type=transaction_type,
                    source_account_id=source_account_id,
                    destination_account_id=destination_account_id,
                    category_id=category_id,
                    description=description,
                    transaction_date=transaction_date,
                    total_installments=total_installments,
                    total_amount=total_amount,
                )
            )
        )

    @staticmethod
    def get_financial_summary(
        month: int | None = None,
        year: int | None = None,
    ) -> dict:
        server = get_mcp_server()
        handler = server._tool_manager._tools["get_financial_summary"].fn
        return run_async(
            handler(
                payload=GetFinancialSummaryInput(
                    month=month,
                    year=year,
                )
            )
        )

    @staticmethod
    def get_budget_status(
        month: int | None = None,
        year: int | None = None,
        category_id: UUID | None = None,
    ) -> dict:
        server = get_mcp_server()
        handler = server._tool_manager._tools["get_budget_status"].fn
        return run_async(
            handler(
                payload=GetBudgetStatusInput(
                    month=month,
                    year=year,
                    category_id=category_id,
                )
            )
        )

    @staticmethod
    def set_budget(category_id: UUID, amount: str, month: int, year: int) -> dict:
        server = get_mcp_server()
        handler = server._tool_manager._tools["set_budget"].fn
        return run_async(
            handler(
                payload=SetBudgetInput(
                    category_id=category_id,
                    amount=amount,
                    month=month,
                    year=year,
                )
            )
        )

    @staticmethod
    def get_installment_plan(installment_id: UUID) -> dict:
        server = get_mcp_server()
        handler = server._tool_manager._tools["get_installment_plan"].fn
        return run_async(
            handler(payload=GetInstallmentPlanInput(installment_id=installment_id))
        )

    @staticmethod
    def delete_transaction(
        transaction_id: UUID, delete_all_installments: bool = False
    ) -> dict:
        server = get_mcp_server()
        handler = server._tool_manager._tools["delete_transaction"].fn
        return run_async(
            handler(
                payload=DeleteTransactionInput(
                    transaction_id=transaction_id,
                    delete_all_installments=delete_all_installments,
                )
            )
        )
