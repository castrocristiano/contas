# Tasks: Leitura de Fatura PDF com Chat Interativo e Lançamento (005-invoice-pdf-chat)

- [ ] 1. Configuração e Dependências
  - [ ] 1.1 Adicionar `pypdf>=4.0.0` às dependências do `pyproject.toml`
  - [ ] 1.2 Executar `uv sync` e verificar compatibilidade do ambiente

- [ ] 2. Módulo de Serviços de IA e Extração de PDF
  - [ ] 2.1 Criar schemas Pydantic para os itens extraídos da fatura (`ExtractedInvoiceItem`, `InvoiceExtractionResult`)
  - [ ] 2.2 Implementar função de extração de texto do PDF via `pypdf`
  - [ ] 2.3 Implementar chamada à API OpenAI (`client.beta.chat.completions.parse`) para extração estruturada de compras e parcelas
  - [ ] 2.4 Implementar função de refinamento e filtro interativo via chat (`chat_refine_items`)

- [ ] 3. Integração com Frontend Streamlit
  - [ ] 3.1 Adicionar opção de menu "🧾 Importar Fatura PDF" no `app.py`
  - [ ] 3.2 Implementar componente de upload e pré-visualização das despesas extraídas
  - [ ] 3.3 Integrar chat interativo com histórico na sessão do Streamlit (`st.session_state`)
  - [ ] 3.4 Implementar ação de persistência em lote chamando `UIService.record_transaction` para cada item confirmado

- [ ] 4. Testes Automatizados e Validação
  - [ ] 4.1 Criar testes unitários para extração e schemas em `tests/unit/test_invoice_parser.py`
  - [ ] 4.2 Executar suíte de testes com `uv run pytest -v`
  - [ ] 4.3 Validar linting e formatação com `uv run ruff check .` e `uv run ruff format --check .`

