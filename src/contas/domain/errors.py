from typing import Any


class DomainError(Exception):
    """Base class for all domain errors."""

    def __init__(
        self,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class ValidationError(DomainError):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(code="VALIDATION_ERROR", message=message, details=details)


class AccountNotFoundError(DomainError):
    def __init__(self, account_id: str, field: str = "account_id") -> None:
        super().__init__(
            code="ACCOUNT_NOT_FOUND",
            message=f"Active account with ID '{account_id}' was not found.",
            details={"field": field, "account_id": account_id},
        )


class CategoryNotFoundError(DomainError):
    def __init__(self, category_id: str, field: str = "category_id") -> None:
        super().__init__(
            code="CATEGORY_NOT_FOUND",
            message=f"Active category with ID '{category_id}' was not found.",
            details={"field": field, "category_id": category_id},
        )


class CategoryAlreadyExistsError(DomainError):
    def __init__(self, name: str) -> None:
        super().__init__(
            code="CATEGORY_ALREADY_EXISTS",
            message=f"Category with name '{name}' already exists.",
            details={"name": name},
        )


class TransferSameAccountError(DomainError):
    def __init__(self, account_id: str) -> None:
        super().__init__(
            code="TRANSFER_SAME_ACCOUNT",
            message="Source and destination accounts must be different in a transfer.",
            details={"account_id": account_id},
        )


class InstallmentPlanNotFoundError(DomainError):
    def __init__(self, installment_id: str) -> None:
        super().__init__(
            code="INSTALLMENT_PLAN_NOT_FOUND",
            message=f"Installment plan with ID '{installment_id}' was not found.",
            details={"installment_id": installment_id},
        )


class TransactionNotFoundError(DomainError):
    def __init__(self, transaction_id: str) -> None:
        super().__init__(
            code="TRANSACTION_NOT_FOUND",
            message=f"Transaction with ID '{transaction_id}' was not found.",
            details={"transaction_id": transaction_id},
        )


class IntegrityError(DomainError):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(code="INTEGRITY_ERROR", message=message, details=details)


class DatabaseError(DomainError):
    def __init__(
        self,
        message: str = "An unexpected database error occurred.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code="DATABASE_ERROR", message=message, details=details)


class UserNotFoundError(DomainError):
    def __init__(self, identifier: str) -> None:
        super().__init__(
            code="USER_NOT_FOUND",
            message=f"Usuário '{identifier}' não foi encontrado.",
            details={"identifier": identifier},
        )


class UserAlreadyExistsError(DomainError):
    def __init__(self, field: str, value: str) -> None:
        super().__init__(
            code="USER_ALREADY_EXISTS",
            message=f"Já existe um usuário com {field} '{value}'.",
            details={"field": field, "value": value},
        )


class InvalidCredentialsError(DomainError):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_CREDENTIALS",
            message="Usuário/e-mail ou senha incorretos.",
        )


class AccountPendingApprovalError(DomainError):
    def __init__(self) -> None:
        super().__init__(
            code="ACCOUNT_PENDING_APPROVAL",
            message="Sua conta foi criada e está aguardando aprovação do administrador.",
        )


class InvalidCurrentPasswordError(DomainError):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_CURRENT_PASSWORD",
            message="A senha atual informada está incorreta.",
        )


ContasError = DomainError
