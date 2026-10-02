# Plano de Implementação - Feature 014: Suporte a Faturas Multi-Coluna e Anti-Alucinação

## 1. Módulo `invoice_parser.py`

### 1.1 Função `preprocess_invoice_text(raw_text: str) -> str`
- Implementar função utilitária `preprocess_invoice_text` para sanitizar o texto antes do envio para a OpenAI.
- Regras de desmembramento de linhas:
  1. Quebra de transações concatenadas na mesma linha (duas colunas): linhas que contenham um padrão de transação (`DD/MM ... R$ X,XX` ou `DD/MM ... X,XX`) seguido de outra data (`DD/MM`) e valor monetário.
  2. Desacoplamento de cabeçalhos de cartão/titular e transações: separar strings como `TITULAR(final 1234) DD/MM ESTABELECIMENTO X,XX` em duas linhas distintas.
- Integrar `preprocess_invoice_text` dentro de `extract_text_from_pdf` ou logo no início de `parse_invoice_with_openai`.

### 1.2 Atualização do System Prompt em `parse_invoice_with_openai`
- Reforçar diretrizes de extração:
  - **Proibição de Simulações**: "NUNCA extraia dados de seções de simulação, tabelas de parcelamento de fatura, simulação de saque cash, parcelas fixas ou pagamento mínimo, nem os valores de IOF informativos associados a essas simulações."
  - **Deduplicação de Encargos**: "Não extraia linhas de resumo consolidado de encargos (ex: 'Total de encargos', 'Encargos (financiamento + moratório)') caso os encargos individuais estejam detalhados na fatura (juros do rotativo, juros de mora, multa por atraso, IOF de financiamento). Extraia apenas os componentes individuais discriminados."
  - **Atenção a Lançamentos Lado a Lado**: "Certifique-se de extrair todos os lançamentos individuais, mesmo quando datas antigas ou compras parceladas aparecerem no início da lista de lançamentos."

## 2. Testes Automatizados

### 2.1 Teste Unitário de Pré-processamento de Colunas
- Em `tests/unit/test_invoice_parser.py`:
  - Testar separação de linhas duplas com padrão de 2 colunas da fatura Itaú/LuizaCred.
  - Testar separação de titular/cartão da primeira transação da coluna.
  - Testar que linhas de transação única não são corrompidas.

### 2.2 Teste com PDFs de Amostra Sintéticos
- Validar se o texto pré-processado contém todas as transações de colunas paralelas e discriminadas sem truncamento.

## 3. Validação e Deploy
- Executar suíte de testes com `uv run pytest`.
- Executar linter e formatação com `uv run ruff check` e `uv run ruff format`.
- Rebuild do container de app e verificação.
