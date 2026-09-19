from typing import Any


class ContasError(Exception):
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


class ValidationError(ContasError):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(code="VALIDATION_ERROR", message=message, details=details)


class AccountNotFoundError(ContasError):
    def __init__(self, account_id: str, field: str = "account_id") -> None:
        super().__init__(
            code="ACCOUNT_NOT_FOUND",
            message=f"Active account with ID '{account_id}' was not found.",
            details={"field": field, "account_id": account_id},
        )


class CategoryNotFoundError(ContasError):
    def __init__(self, category_id: str, field: str = "category_id") -> None:
        super().__init__(
            code="CATEGORY_NOT_FOUND",
            message=f"Active category with ID '{category_id}' was not found.",
            details={"field": field, "category_id": category_id},
        )


class CategoryAlreadyExistsError(ContasError):
    def __init__(self, name: str) -> None:
        super().__init__(
            code="CATEGORY_ALREADY_EXISTS",
            message=f"Category with name '{name}' already exists.",
            details={"name": name},
        )


class TransferSameAccountError(ContasError):
    def __init__(self, account_id: str) -> None:
        super().__init__(
            code="TRANSFER_SAME_ACCOUNT",
            message="Source and destination accounts must be different in a transfer.",
            details={"account_id": account_id},
        )


class InstallmentPlanNotFoundError(ContasError):
    def __init__(self, installment_id: str) -> None:
        super().__init__(
            code="INSTALLMENT_PLAN_NOT_FOUND",
            message=f"Installment plan with ID '{installment_id}' was not found.",
            details={"installment_id": installment_id},
        )


class DatabaseError(ContasError):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(code="DATABASE_ERROR", message=message, details=details)


class IntegrityError(ContasError):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(code="INTEGRITY_ERROR", message=message, details=details)
