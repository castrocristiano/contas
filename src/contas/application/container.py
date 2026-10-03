from dataclasses import dataclass
from functools import lru_cache

from contas.application.ports.repositories import (
    IAccountRepository,
    IBudgetRepository,
    ICategoryRepository,
    ITransactionRepository,
    IUserRepository,
)
from contas.application.use_cases.accounts import (
    BulkDeleteAccountsUseCase,
    CreateAccountUseCase,
    DeleteAccountUseCase,
    ListAccountsUseCase,
    UpdateAccountUseCase,
)
from contas.application.use_cases.auth import (
    AdminResetPasswordUseCase,
    ApproveUserUseCase,
    AuthenticateUserUseCase,
    ChangePasswordUseCase,
    GoogleOAuthUseCase,
    ListUsersUseCase,
    RegisterUserUseCase,
)
from contas.application.use_cases.budgets import (
    GetBudgetStatusUseCase,
    SetBudgetUseCase,
)
from contas.application.use_cases.categories import (
    CreateCategoryUseCase,
    ListCategoriesUseCase,
)
from contas.application.use_cases.transactions import (
    DeleteTransactionUseCase,
    GetFinancialSummaryUseCase,
    GetInstallmentPlanUseCase,
    GetStatementUseCase,
    RecordTransactionUseCase,
)
from contas.infrastructure.repositories.account import SQLAlchemyAccountRepository
from contas.infrastructure.repositories.budget import SQLAlchemyBudgetRepository
from contas.infrastructure.repositories.category import SQLAlchemyCategoryRepository
from contas.infrastructure.repositories.transaction import (
    SQLAlchemyTransactionRepository,
)
from contas.infrastructure.repositories.user import SQLAlchemyUserRepository


@dataclass
class Container:
    account_repo: IAccountRepository
    category_repo: ICategoryRepository
    transaction_repo: ITransactionRepository
    budget_repo: IBudgetRepository
    user_repo: IUserRepository

    # Auth Use Cases
    register_user_uc: RegisterUserUseCase
    authenticate_user_uc: AuthenticateUserUseCase
    google_oauth_uc: GoogleOAuthUseCase
    approve_user_uc: ApproveUserUseCase
    list_users_uc: ListUsersUseCase
    change_password_uc: ChangePasswordUseCase
    admin_reset_password_uc: AdminResetPasswordUseCase

    # Use Cases
    create_account_uc: CreateAccountUseCase
    list_accounts_uc: ListAccountsUseCase
    update_account_uc: UpdateAccountUseCase
    delete_account_uc: DeleteAccountUseCase
    bulk_delete_accounts_uc: BulkDeleteAccountsUseCase

    create_category_uc: CreateCategoryUseCase
    list_categories_uc: ListCategoriesUseCase

    record_transaction_uc: RecordTransactionUseCase
    get_statement_uc: GetStatementUseCase
    get_installment_plan_uc: GetInstallmentPlanUseCase
    delete_transaction_uc: DeleteTransactionUseCase
    get_financial_summary_uc: GetFinancialSummaryUseCase

    set_budget_uc: SetBudgetUseCase
    get_budget_status_uc: GetBudgetStatusUseCase


@lru_cache
def get_container() -> Container:
    account_repo = SQLAlchemyAccountRepository()
    category_repo = SQLAlchemyCategoryRepository()
    transaction_repo = SQLAlchemyTransactionRepository()
    budget_repo = SQLAlchemyBudgetRepository()
    user_repo = SQLAlchemyUserRepository()

    return Container(
        account_repo=account_repo,
        category_repo=category_repo,
        transaction_repo=transaction_repo,
        budget_repo=budget_repo,
        user_repo=user_repo,
        register_user_uc=RegisterUserUseCase(user_repo),
        authenticate_user_uc=AuthenticateUserUseCase(user_repo),
        google_oauth_uc=GoogleOAuthUseCase(user_repo),
        approve_user_uc=ApproveUserUseCase(user_repo),
        list_users_uc=ListUsersUseCase(user_repo),
        change_password_uc=ChangePasswordUseCase(user_repo),
        admin_reset_password_uc=AdminResetPasswordUseCase(user_repo),
        create_account_uc=CreateAccountUseCase(account_repo),
        list_accounts_uc=ListAccountsUseCase(account_repo),
        update_account_uc=UpdateAccountUseCase(account_repo),
        delete_account_uc=DeleteAccountUseCase(account_repo, transaction_repo),
        bulk_delete_accounts_uc=BulkDeleteAccountsUseCase(account_repo),
        create_category_uc=CreateCategoryUseCase(category_repo),
        list_categories_uc=ListCategoriesUseCase(category_repo),
        record_transaction_uc=RecordTransactionUseCase(
            account_repo, transaction_repo, category_repo
        ),
        get_statement_uc=GetStatementUseCase(
            account_repo, transaction_repo, category_repo
        ),
        get_installment_plan_uc=GetInstallmentPlanUseCase(transaction_repo),
        delete_transaction_uc=DeleteTransactionUseCase(account_repo, transaction_repo),
        get_financial_summary_uc=GetFinancialSummaryUseCase(account_repo),
        set_budget_uc=SetBudgetUseCase(budget_repo, category_repo),
        get_budget_status_uc=GetBudgetStatusUseCase(budget_repo, category_repo),
    )
