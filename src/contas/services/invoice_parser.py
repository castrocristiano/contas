import io
import json
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field
from pypdf import PdfReader

from contas.config import settings


class ExtractedInvoiceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: str = Field(
        ...,
        description="Transaction date in ISO 8601 format (YYYY-MM-DD), or estimated from the invoice context.",
    )
    description: str = Field(
        ...,
        description="Clean description of the merchant or expense.",
    )
    amount: str = Field(
        ...,
        description="Monetary amount in positive decimal string with two decimals (e.g. '49.90').",
        pattern=r"^[0-9]+(\.[0-9]{1,2})?$",
    )
    category_suggestion: str = Field(
        default="Outros",
        description="Suggested category matching one of the user's existing categories, or 'Outros'.",
    )
    installment_current: int | None = Field(
        default=None,
        description="Current installment number if installment purchase (e.g. 2 for '2/10').",
    )
    installment_total: int | None = Field(
        default=None,
        description="Total installments if installment purchase (e.g. 10 for '2/10').",
    )


class InvoiceExtractionContainer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invoice_period: str | None = Field(
        default=None,
        description="Month or period of the invoice if identified (e.g., 'Setembro/2026').",
    )
    items: list[ExtractedInvoiceItem] = Field(
        default_factory=list,
        description="List of extracted transaction items.",
    )


class ChatRefinementContainer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assistant_reply: str = Field(
        ...,
        description="Natural language explanation of the filtering or modification applied.",
    )
    updated_items: list[ExtractedInvoiceItem] = Field(
        ...,
        description="Updated list of transaction items after user commands (removals, filters, recategorizations).",
    )


def check_pdf_encrypted(pdf_bytes: bytes) -> bool:
    """Check if the PDF is encrypted and requires a password."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return bool(reader.is_encrypted)


def extract_text_from_pdf(pdf_bytes: bytes, password: str | None = None) -> str:
    """Extract raw text from PDF bytes using pypdf, with optional password for encrypted files."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    if reader.is_encrypted:
        if not password:
            raise ValueError(
                "O arquivo PDF está protegido por senha. Por favor, informe a senha da fatura."
            )
        decrypt_result = reader.decrypt(password)
        if decrypt_result == 0:
            raise ValueError("Senha incorreta para abrir o arquivo PDF da fatura.")

    pages_text: list[str] = []
    for idx, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages_text.append(f"--- Página {idx + 1} ---\n{text}")
    return "\n\n".join(pages_text)


def parse_invoice_with_openai(
    pdf_text: str,
    categories: list[str],
    client: OpenAI | None = None,
) -> InvoiceExtractionContainer:
    """Parse raw PDF invoice text into structured items using OpenAI Structured Outputs."""
    if not pdf_text.strip():
        return InvoiceExtractionContainer(items=[])

    if client is None:
        api_key = settings.effective_openai_api_key
        if not api_key:
            raise ValueError(
                "Chave da OpenAI não configurada. Defina a variável de ambiente OPENAPI_KEY ou OPENAI_API_KEY."
            )
        client = OpenAI(api_key=api_key)

    categories_list_str = (
        ", ".join(categories) if categories else "Nenhuma (use 'Outros')"
    )

    system_prompt = (
        "Você é um assistente financeiro especialista em extrair dados de faturas de cartão de crédito brasileiras.\n"
        "Analise o texto cru da fatura e extraia todas as despesas individuais/compras efetuadas no período.\n"
        "Regras:\n"
        "1. Ignore pagamentos de fatura anterior, encargos/juros já quitados ou linhas de totais/resumos.\n"
        "2. Formate cada data no formato 'YYYY-MM-DD'. Se o ano não constar na linha, infira pelo cabeçalho/período da fatura.\n"
        "3. O campo amount deve conter apenas números decimais positivos com ponto (ex: '29.90').\n"
        "4. Se a linha indicar parcelas (ex: '02/10', 'Parcela 3 de 5'), extraia installment_current e installment_total.\n"
        f"5. Categorize cada compra sugerindo a melhor opção dentre as existentes: [{categories_list_str}]. Se não houver categoria adequada, use 'Outros'.\n"
    )

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Texto da fatura:\n\n{pdf_text}"},
        ],
        response_format=InvoiceExtractionContainer,
    )

    return completion.choices[0].message.parsed


def refine_items_with_chat(
    current_items: list[dict[str, Any]],
    user_message: str,
    categories: list[str],
    client: OpenAI | None = None,
) -> tuple[list[dict[str, Any]], str]:
    """Refine, filter, or update items based on user natural language instructions."""
    if client is None:
        api_key = settings.effective_openai_api_key
        if not api_key:
            raise ValueError(
                "Chave da OpenAI não configurada. Defina a variável de ambiente OPENAPI_KEY ou OPENAI_API_KEY."
            )
        client = OpenAI(api_key=api_key)

    categories_list_str = (
        ", ".join(categories) if categories else "Nenhuma (use 'Outros')"
    )

    system_prompt = (
        "Você é um assistente financeiro inteligente que ajuda o usuário a filtrar, alterar categorias ou remover despesas de uma fatura de cartão.\n"
        "O usuário enviará uma instrução em linguagem natural (ex: 'remova farmácia', 'filtre compras acima de R$ 50', 'mude Padaria para Alimentação').\n"
        "Você deve aplicar as alterações na lista de transações e responder com:\n"
        "1. assistant_reply: resposta amigável e concisa em Português confirmando o que foi filtrado ou alterado.\n"
        "2. updated_items: a lista atualizada de itens com as alterações aplicadas.\n"
        f"Categorias disponíveis: [{categories_list_str}].\n"
    )

    items_json = json.dumps(current_items, ensure_ascii=False)

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Itens atuais:\n{items_json}\n\nInstrução do usuário:\n{user_message}",
            },
        ],
        response_format=ChatRefinementContainer,
    )

    parsed = completion.choices[0].message.parsed
    updated_dicts = [item.model_dump() for item in parsed.updated_items]
    return updated_dicts, parsed.assistant_reply
