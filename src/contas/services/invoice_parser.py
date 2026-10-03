import io
import json
import logging
import re
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pypdf import PdfReader

from contas.config import settings

logger = logging.getLogger(__name__)


def extract_installment_from_description(text: str) -> tuple[int | None, int | None]:
    """Extract (installment_current, installment_total) from description strings.

    Supports patterns like:
    - 02/04, 2/10, 02/10, 1/12
    - D02/04, P03/10 (letters directly attached to digits)
    - Parcela 02 de 10, Parc 2/4, Parcela 2/10
    """
    if not text:
        return None, None

    # 1. Pattern: Parcela X de Y / Parc X de Y
    m_de = re.search(
        r"(?:parcela|parc\.?)\s*(\d{1,2})\s*(?:de|\/)\s*(\d{1,2})",
        text,
        re.IGNORECASE,
    )
    if m_de:
        cur, tot = int(m_de.group(1)), int(m_de.group(2))
        if 1 <= cur <= tot:
            return cur, tot

    # 2. Pattern: X/Y with 1 or 2 digits, possibly preceded by word/letter or space (e.g. 'D02/04', ' 02/04', '-02/04')
    # Ensures it's not a date like 05/09/2026 or DD/MM
    matches = re.finditer(r"(?:^|[\s\-_A-Za-z])(\d{1,2})\/(\d{1,2})(?:$|[^\d\/])", text)
    for m in matches:
        cur, tot = int(m.group(1)), int(m.group(2))
        if 1 <= cur <= tot and tot > 1:
            return cur, tot

    return None, None


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
    is_future: bool = Field(
        default=False,
        description="True if this transaction belongs to future invoices, upcoming releases, or scheduled for future periods.",
    )
    selected_for_import: bool = Field(
        default=True,
        description="Whether this transaction is selected for import into the system. Can be set to True or False by user chat commands (e.g. 'selecione apenas compras de mercado', 'desmarque os gastos com Uber', 'marque todas').",
    )

    @model_validator(mode="after")
    def populate_installments_from_description(self) -> "ExtractedInvoiceItem":
        """Auto-detect installment numbers from description if not already set or invalid."""
        if self.installment_current is None or self.installment_total is None:
            cur, tot = extract_installment_from_description(self.description)
            if cur is not None and tot is not None:
                self.installment_current = cur
                self.installment_total = tot
        return self


class InvoiceExtractionContainer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invoice_period: str | None = Field(
        default=None,
        description="Month or period of the invoice if identified (e.g., 'Setembro/2026').",
    )
    invoice_due_date: str | None = Field(
        default=None,
        description="Due date of the invoice in ISO 8601 format (YYYY-MM-DD), found in the header or payment slip (e.g., '2026-09-20').",
    )
    invoice_total_amount: str | None = Field(
        default=None,
        description="Total amount of the invoice as stated on the header/summary/payment slip (e.g. '4138.00').",
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


def preprocess_invoice_text(text: str) -> str:
    """Pre-process extracted raw invoice text to split concatenated columns and isolate transactions.

    Handles layout quirks from Brazilian credit card invoices (e.g. Itaú, LuizaCred) where
    two parallel transaction columns get joined on the same line, or cardholder headers
    are merged with the first transaction of a column.
    """
    if not text:
        return text

    lines = text.split("\n")
    processed_lines: list[str] = []

    # 1. Regex to split joined two-column transaction lines:
    # Matches: DD/MM ... AMOUNT followed by DD/MM ...
    # Ex: '15/01 LOJA EXEMPLO A 25,00 16/01 LOJA EXEMPLO B 50,00'
    two_col_tx_pattern = re.compile(
        r"^(\d{2}/\d{2}(?:/\d{2,4})?.*?[-]?\d+[\.,]\d{2})\s+(\d{2}/\d{2}(?:/\d{2,4})?.*)$"
    )

    # 2. Regex to split cardholder/card number header concatenated with transaction on same line:
    # Ex: 'NOME DO CLIENTE(final 0000) 10/01 FARMACIA EXEMPLO 30,00'
    header_tx_pattern = re.compile(
        r"^(.*?(?:final\s*\d+[^\d]*|\bCART[ÃA]O\b[^\d]*))\s+(\d{2}/\d{2}(?:/\d{2,4})?.*[-]?\d+[\.,]\d{2}.*)$",
        re.IGNORECASE,
    )

    # 3. Regex to split words where a date is glued directly without spaces (common in wrapped table cells):
    # Ex: '...texto12/09 LOJA EXEMPLO 01/03 45,00' -> '...texto' e '12/09 LOJA EXEMPLO 01/03 45,00'
    glued_date_pattern = re.compile(
        r"^(.*?)([A-Za-zÀ-ÿ]+)(\d{2}/\d{2}(?:/\d{2,4})?\s+.*[-]?\d+[\.,]\d{2}.*)$"
    )

    for line in lines:
        stripped = line.strip()
        m_col = two_col_tx_pattern.match(stripped)
        if m_col:
            # Emit Col 1 as a separate, distinct line with clean separation
            processed_lines.append(m_col.group(1).strip())
            processed_lines.append(m_col.group(2).strip())
            continue

        m_hdr = header_tx_pattern.match(stripped)
        if m_hdr:
            processed_lines.append(m_hdr.group(1).strip())
            processed_lines.append(m_hdr.group(2).strip())
            continue

        m_glue = glued_date_pattern.match(stripped)
        if m_glue and not stripped.startswith("http"):
            prefix = (m_glue.group(1) + m_glue.group(2)).strip()
            suffix = m_glue.group(3).strip()
            if prefix:
                processed_lines.append(prefix)
            if suffix:
                processed_lines.append(suffix)
            continue

        processed_lines.append(line)

    return "\n".join(processed_lines)


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
    raw_combined = "\n\n".join(pages_text)
    return preprocess_invoice_text(raw_combined)


def parse_invoice_with_openai(
    pdf_text: str,
    categories: list[str],
    client: OpenAI | None = None,
    model: str | None = None,
) -> InvoiceExtractionContainer:
    """Parse raw PDF invoice text into structured items using OpenAI Structured Outputs."""
    if not pdf_text.strip():
        return InvoiceExtractionContainer(items=[])

    # Ensure pre-processing even if text came from an external caller
    clean_text = preprocess_invoice_text(pdf_text)

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
        "Analise o texto da fatura e extraia todas as despesas individuais, compras, tarifas, juros, IOF, multas e encargos cobrados na fatura atual ou previstos para próximas faturas.\n"
        "Regras fundamentais:\n"
        "1. Extraia compras, despesas, tarifas de anuidade, juros reais cobrados, encargos financeiros, multas e IOF efetivo como despesas com valor positivo.\n"
        "2. ENCARGOS COBRADOS NESTA FATURA (OBRIGATÓRIO): na seção 'Encargos cobrados nesta fatura' ou no extrato detalhado, extraia OBRIGATORIAMENTE todos os encargos e tarifas aplicados (ex: 'Juros do rotativo', 'Juros de mora', 'Multa por atraso', 'IOF', 'IOF de financiamento', 'Encargos de atraso', 'Encargos de financiamento'). A data desses encargos deve ser a data de fechamento ou vencimento da fatura. NUNCA omita nenhum encargo ou juros cobrado na fatura.\n"
        "3. NUNCA EXTRAIA DADOS DE SIMULAÇÕES OU OPÇÕES DE PAGAMENTO: ignore completamente seções de 'Opções de parcelamento', 'Simulação Saque Cash', 'Simulação de Compras parceladas', 'Parcelas fixas', 'Pagamento mínimo' e quaisquer valores de IOF ou juros meramente simulados contidos nessas tabelas explicativas.\n"
        "4. TOTAIS E RESUMOS: ignore linhas puramente totalizadoras gerais (ex: 'Total desta fatura', 'Lançamentos atuais', 'Total para próximas faturas'). Se a fatura trouxer linhas de encargos individuais (juros, multa, IOF), extraia cada uma individualmente. Se trouxer uma linha única como 'ENCARGOS (financiamento + moratório)' cobrada na fatura, extraia-a como encargo.\n"
        "5. Ignore linhas que representem pagamentos efetuados pelo cliente (ex: 'Pagamento recebido', 'Pagamento efetuado', 'Pagamento de fatura'). Ajustes a crédito ou estornos de centavos (ex: '- 0,01') não devem impedir a extração das outras compras da mesma data.\n"
        "6. NÃO OMITA NENHUMA COMPRA: analise minuciosamente todas as linhas de compras, inclusive compras antigas parceladas listadas no início da fatura e compras de parcelas intermediárias (ex: parcelas 02/04, 02/05, 03/03).\n"
        "7. Identifique transações de faturas futuras (seção 'Próximas faturas', 'Lançamentos futuros' ou parcelas com vencimento posterior ao fechamento) e marque 'is_future=True'. Para transações da fatura atual, marque 'is_future=False'.\n"
        "8. Formate cada data no formato 'YYYY-MM-DD'. Se o ano não constar na linha, deduza com base no período/emissão da fatura.\n"
        "9. O campo amount deve conter apenas números decimais positivos com ponto (ex: '29.90').\n"
        "10. Se a linha indicar parcelas em qualquer formato (ex: '02/10', 'Parcela 3 de 5', 'D02/04', '02/04' no final do nome do estabelecimento ou na descrição), extraia obrigatoriamente installment_current e installment_total.\n"
        f"11. Categorize cada item sugerindo a melhor opção dentre as existentes: [{categories_list_str}]. Para encargos e juros, categorize apropriadamente (ex: 'Tarifas', 'Encargos', 'Juros' ou 'Outros'). Se não houver categoria adequada, use 'Outros'.\n"
        "12. Identifique também o 'invoice_due_date' (data de vencimento da fatura, formato 'YYYY-MM-DD'), 'invoice_period' (ex: 'Setembro/2026') e 'invoice_total_amount' (valor total da fatura/boleto impresso no cabeçalho ou resumo, apenas números positivos com ponto, ex: '4138.00').\n"
    )

    model_to_use = model or settings.invoice_model or "gpt-4o"

    completion = client.beta.chat.completions.parse(
        model=model_to_use,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Texto da fatura:\n\n{clean_text}"},
        ],
        response_format=InvoiceExtractionContainer,
        store=settings.openai_store,
        metadata={"app": "contas", "feature": "invoice_parser"},
    )

    parsed = completion.choices[0].message.parsed

    # Reconciliação Matemática em Log
    try:
        current_invoice_items = [it for it in parsed.items if not bool(it.is_future)]
        sum_current = sum(float(it.amount) for it in current_invoice_items)
        sum_total = sum(float(it.amount) for it in parsed.items)
        declared_total = (
            float(parsed.invoice_total_amount) if parsed.invoice_total_amount else None
        )

        log_msg = (
            f"[RECONCILIAÇÃO FATURA] Modelo: {model_to_use} | "
            f"Total de itens extraídos: {len(parsed.items)} (Atuais: {len(current_invoice_items)}) | "
            f"Soma itens atuais: R$ {sum_current:.2f} | Soma total: R$ {sum_total:.2f}"
        )
        if declared_total is not None:
            diff = round(declared_total - sum_current, 2)
            log_msg += f" | Total declarado no boleto: R$ {declared_total:.2f} | Diferença: R$ {diff:.2f}"
            if abs(diff) < 0.05:
                logger.info(f"{log_msg} | Status: RECONCILIAÇÃO PERFEITA ✅")
            else:
                logger.warning(
                    f"{log_msg} | Status: DIVERGÊNCIA DETECTADA ⚠️ (Verificar encargos ou compras parceladas)"
                )
        else:
            logger.info(log_msg)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Falha ao registrar reconciliação em log: %s", exc)

    return parsed


def refine_items_with_chat(
    current_items: list[dict[str, Any]],
    user_message: str,
    categories: list[str],
    original_items: list[dict[str, Any]] | None = None,
    client: OpenAI | None = None,
    model: str | None = None,
) -> tuple[list[dict[str, Any]], str]:
    """Refine, filter, or update items based on user natural language instructions.

    Supports undoing filters/resetting to the original extracted items if requested.
    """
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
        "Você é um assistente financeiro inteligente que ajuda o usuário a filtrar, alterar categorias, remover, marcar/desmarcar despesas para importação de uma fatura de cartão, ou desfazer/resetar filtros anteriores.\n"
        "O usuário enviará uma instrução em linguagem natural (ex: 'remova farmácia', 'filtre compras acima de R$ 50', 'mude Padaria para Alimentação', 'marque apenas compras de alimentação para importar', 'desmarque gastos com Uber', 'selecione tudo', 'desfaça os filtros', 'volte os itens que foram removidos', 'restaure a lista original').\n"
        "Regras:\n"
        "1. Para comandos de desfazimento/restauração de filtros ou itens removidos (ex: 'desfaça os filtros', 'restaure todos os itens', 'volte os itens removidos', 'cancelar filtros', 'desfaça a última remoção'): utilize a lista de 'Itens originais extraídos da fatura' para restaurar os itens que haviam sido removidos ou filtrados.\n"
        "2. Para comandos de marcar/desmarcar/selecionar para importar (ex: 'marque para importar X', 'não importe Y', 'selecione apenas Z', 'selecione tudo', 'desmarque tudo'): ajuste o campo 'selected_for_import' para True (marcada para importar) ou False (desmarcada da importação).\n"
        "3. Para comandos explícitos de remoção/exclusão da lista (ex: 'remova as compras do iFood'): você pode remover os itens da lista ou deixá-los com selected_for_import=False.\n"
        "4. Para alterações de categorias ou valores, atualize os respectivos campos.\n"
        "5. Responda com:\n"
        "   - assistant_reply: resposta amigável e concisa em Português confirmando o que foi restaurado, marcado, desmarcado, filtrado ou alterado.\n"
        "   - updated_items: a lista atualizada de itens com as alterações aplicadas.\n"
        f"Categorias disponíveis: [{categories_list_str}].\n"
    )

    items_json = json.dumps(current_items, ensure_ascii=False)
    user_prompt_content = f"Itens atuais:\n{items_json}\n"
    if original_items:
        orig_json = json.dumps(original_items, ensure_ascii=False)
        user_prompt_content += f"\nItens originais extraídos da fatura (referência para desfazer/restaurar):\n{orig_json}\n"
    user_prompt_content += f"\nInstrução do usuário:\n{user_message}"

    model_to_use = model or settings.invoice_model or "gpt-4o"

    completion = client.beta.chat.completions.parse(
        model=model_to_use,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": user_prompt_content,
            },
        ],
        response_format=ChatRefinementContainer,
        store=settings.openai_store,
        metadata={"app": "contas", "feature": "invoice_refinement"},
    )

    parsed = completion.choices[0].message.parsed
    updated_dicts = [item.model_dump() for item in parsed.updated_items]
    return updated_dicts, parsed.assistant_reply
