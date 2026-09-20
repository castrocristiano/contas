from unittest.mock import MagicMock

from contas.services.invoice_parser import (
    ChatRefinementContainer,
    ExtractedInvoiceItem,
    InvoiceExtractionContainer,
    parse_invoice_with_openai,
    refine_items_with_chat,
)


def test_extracted_invoice_item_schema():
    item = ExtractedInvoiceItem(
        date="2026-09-15",
        description="Supermercado Pão de Açúcar",
        amount="184.50",
        category_suggestion="Alimentação",
        installment_current=1,
        installment_total=3,
    )
    assert item.date == "2026-09-15"
    assert item.amount == "184.50"
    assert item.installment_current == 1
    assert item.installment_total == 3


def test_effective_openai_api_key_fallbacks():
    from contas.config import Settings

    # 1. Test openapi_key takes precedence or falls back seamlessly
    s1 = Settings(openapi_key="key_openapi", openai_api_key="key_openai_api")
    assert s1.effective_openai_api_key == "key_openapi"

    # 2. Test fallback to openai_api_key
    s2 = Settings(openapi_key="", openai_api_key="key_openai_api")
    assert s2.effective_openai_api_key == "key_openai_api"

    # 3. Test fallback to openaiapi_key
    s3 = Settings(openapi_key="", openai_api_key="", openaiapi_key="key_openaiapi")
    assert s3.effective_openai_api_key == "key_openaiapi"


def test_parse_invoice_with_openai_mock():
    mock_client = MagicMock()
    mock_parsed = InvoiceExtractionContainer(
        invoice_period="Setembro/2026",
        items=[
            ExtractedInvoiceItem(
                date="2026-09-02",
                description="Posto Ipiranga",
                amount="150.00",
                category_suggestion="Transporte",
            ),
            ExtractedInvoiceItem(
                date="2026-09-05",
                description="Amazon",
                amount="89.90",
                category_suggestion="Outros",
                installment_current=2,
                installment_total=5,
            ),
        ],
    )

    mock_choice = MagicMock()
    mock_choice.message.parsed = mock_parsed
    mock_client.beta.chat.completions.parse.return_value = MagicMock(
        choices=[mock_choice]
    )

    result = parse_invoice_with_openai(
        pdf_text="Fatura Cartão de Crédito...",
        categories=["Transporte", "Alimentação"],
        client=mock_client,
    )

    assert len(result.items) == 2
    assert result.items[0].description == "Posto Ipiranga"
    assert result.items[0].amount == "150.00"
    assert result.items[1].installment_current == 2
    assert result.items[1].installment_total == 5


def test_refine_items_with_chat_mock():
    mock_client = MagicMock()
    mock_parsed = ChatRefinementContainer(
        assistant_reply="Removi o item Posto Ipiranga conforme solicitado.",
        updated_items=[
            ExtractedInvoiceItem(
                date="2026-09-05",
                description="Amazon",
                amount="89.90",
                category_suggestion="Outros",
                installment_current=2,
                installment_total=5,
            ),
        ],
    )

    mock_choice = MagicMock()
    mock_choice.message.parsed = mock_parsed
    mock_client.beta.chat.completions.parse.return_value = MagicMock(
        choices=[mock_choice]
    )

    current_items = [
        {
            "date": "2026-09-02",
            "description": "Posto Ipiranga",
            "amount": "150.00",
            "category_suggestion": "Transporte",
            "installment_current": None,
            "installment_total": None,
        },
        {
            "date": "2026-09-05",
            "description": "Amazon",
            "amount": "89.90",
            "category_suggestion": "Outros",
            "installment_current": 2,
            "installment_total": 5,
        },
    ]

    updated, reply = refine_items_with_chat(
        current_items=current_items,
        user_message="remova o posto",
        categories=["Transporte", "Alimentação"],
        client=mock_client,
    )

    assert len(updated) == 1
    assert updated[0]["description"] == "Amazon"
    assert "Posto Ipiranga" in reply


def test_check_pdf_encrypted_mock():
    from unittest.mock import patch

    from contas.services.invoice_parser import check_pdf_encrypted

    with patch("contas.services.invoice_parser.PdfReader") as mock_reader_cls:
        mock_reader_cls.return_value.is_encrypted = True
        assert check_pdf_encrypted(b"%PDF-1.4...") is True

        mock_reader_cls.return_value.is_encrypted = False
        assert check_pdf_encrypted(b"%PDF-1.4...") is False


def test_extract_text_from_pdf_encrypted_handling():
    from unittest.mock import MagicMock, patch

    import pytest

    from contas.services.invoice_parser import extract_text_from_pdf

    # 1. Encrypted without password raises ValueError
    with patch("contas.services.invoice_parser.PdfReader") as mock_reader_cls:
        mock_reader_cls.return_value.is_encrypted = True
        with pytest.raises(ValueError, match="protegido por senha"):
            extract_text_from_pdf(b"%PDF...", password=None)

    # 2. Encrypted with wrong password (decrypt returns 0) raises ValueError
    with patch("contas.services.invoice_parser.PdfReader") as mock_reader_cls:
        mock_reader = MagicMock()
        mock_reader.is_encrypted = True
        mock_reader.decrypt.return_value = 0
        mock_reader_cls.return_value = mock_reader
        with pytest.raises(ValueError, match="Senha incorreta"):
            extract_text_from_pdf(b"%PDF...", password="wrong_password")

    # 3. Encrypted with correct password succeeds
    with patch("contas.services.invoice_parser.PdfReader") as mock_reader_cls:
        mock_reader = MagicMock()
        mock_reader.is_encrypted = True
        mock_reader.decrypt.return_value = 1
        page1 = MagicMock()
        page1.extract_text.return_value = "Despesa 1 R$ 50,00"
        mock_reader.pages = [page1]
        mock_reader_cls.return_value = mock_reader

        text = extract_text_from_pdf(b"%PDF...", password="correct_password")
        assert "Despesa 1 R$ 50,00" in text
        mock_reader.decrypt.assert_called_once_with("correct_password")
