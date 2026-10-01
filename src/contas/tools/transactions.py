from mcp.server.mcpserver import MCPServer
from sqlalchemy.exc import DBAPIError
from sqlalchemy.exc import IntegrityError as SAIntegrityError

from contas.application.container import get_container
from contas.domain.errors import ContasError, DatabaseError, IntegrityError
from contas.schemas.transaction import (
    DeleteTransactionInput,
    GetFinancialSummaryInput,
    GetInstallmentPlanInput,
    GetStatementInput,
    RecordTransactionInput,
)


def register_transaction_tools(mcp: MCPServer) -> None:
    @mcp.tool()
    async def record_transaction(payload: RecordTransactionInput) -> dict:
        """Record a financial transaction (income, expense, transfer, or installment purchase) and atomically update balances."""
        try:
            container = get_container()
            return await container.record_transaction_uc.execute(payload)
        except ContasError as err:
            return err.to_dict()
        except SAIntegrityError as err:
            return IntegrityError(str(err.orig or err)).to_dict()
        except DBAPIError as err:
            return DatabaseError(str(err.orig or err)).to_dict()

    @mcp.tool()
    async def get_statement(payload: GetStatementInput) -> dict:
        """Get the detailed statement of an account for a given period."""
        try:
            container = get_container()
            return await container.get_statement_uc.execute(payload)
        except ContasError as err:
            return err.to_dict()
        except DBAPIError as err:
            return DatabaseError(str(err.orig or err)).to_dict()

    @mcp.tool()
    async def get_installment_plan(payload: GetInstallmentPlanInput) -> dict:
        """Get the full installment plan and schedule for a given installment purchase ID."""
        try:
            container = get_container()
            return await container.get_installment_plan_uc.execute(payload)
        except ContasError as err:
            return err.to_dict()
        except DBAPIError as err:
            return DatabaseError(str(err.orig or err)).to_dict()

    @mcp.tool()
    async def get_financial_summary(payload: GetFinancialSummaryInput) -> dict:
        """Get consolidated financial summary of all active accounts."""
        try:
            container = get_container()
            return await container.get_financial_summary_uc.execute(payload)
        except ContasError as err:
            return err.to_dict()
        except DBAPIError as err:
            return DatabaseError(str(err.orig or err)).to_dict()

    @mcp.tool()
    async def delete_transaction(payload: DeleteTransactionInput) -> dict:
        """Delete a transaction, reverting any cleared amounts to account balances atomically, with support for deleting individual installments or all installments in a plan."""
        try:
            container = get_container()
            return await container.delete_transaction_uc.execute(payload)
        except ContasError as err:
            return err.to_dict()
        except DBAPIError as err:
            return DatabaseError(str(err.orig or err)).to_dict()
