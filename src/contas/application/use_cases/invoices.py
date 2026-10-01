from typing import Any

from openai import OpenAI

from contas.services.invoice_parser import (
    check_pdf_encrypted,
    extract_text_from_pdf,
    parse_invoice_with_openai,
    refine_items_with_chat,
)


class ParseInvoiceUseCase:
    @staticmethod
    def extract_text(pdf_bytes: bytes, password: str | None = None) -> str:
        return extract_text_from_pdf(pdf_bytes, password=password)

    @staticmethod
    def is_encrypted(pdf_bytes: bytes) -> bool:
        return check_pdf_encrypted(pdf_bytes)

    @staticmethod
    def parse_with_ai(
        pdf_text: str, categories: list[str], client: OpenAI | None = None
    ) -> Any:
        return parse_invoice_with_openai(pdf_text, categories=categories, client=client)


class RefineInvoiceUseCase:
    @staticmethod
    def refine_with_chat(
        current_items: list[dict[str, Any]],
        user_message: str,
        categories: list[str],
        original_items: list[dict[str, Any]] | None = None,
        client: OpenAI | None = None,
    ) -> tuple[list[dict[str, Any]], str]:
        return refine_items_with_chat(
            current_items=current_items,
            user_message=user_message,
            categories=categories,
            original_items=original_items,
            client=client,
        )
