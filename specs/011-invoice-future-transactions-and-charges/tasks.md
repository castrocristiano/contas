# Tasks: Transações Futuras, Encargos e Projeção de Parcelas na Importação de Faturas (011-invoice-future-transactions-and-charges)

- [x] 1. Spec & Planejamento SDD
  - [x] 1.1 Criar `specs/011-invoice-future-transactions-and-charges/spec.md`
  - [x] 1.2 Criar `specs/011-invoice-future-transactions-and-charges/plan.md`
  - [x] 1.3 Criar `specs/011-invoice-future-transactions-and-charges/tasks.md`

- [x] 2. Modelo de Extração e Prompt OpenAI
  - [x] 2.1 Adicionar campo `is_future` em `ExtractedInvoiceItem` em `src/contas/services/invoice_parser.py`
  - [x] 2.2 Atualizar prompt do sistema para extrair tarifas, juros, encargos, multas e marcar itens futuros com `is_future=True`
  - [x] 2.3 Adicionar extração automática de parcelas embutidas em descrições (ex: `D02/04`, `02/04`, `Parc X de Y`) com `model_validator` e fallback na UI
  - [x] 2.4 Adicionar campo `selected_for_import` em `ExtractedInvoiceItem` e suporte a marcação/desmarcação por linguagem natural no prompt do chat de refinamento

- [x] 3. Camada de Serviço da UI
  - [x] 3.1 Adicionar parâmetros `status` e `installment_number` em `UIService.record_transaction` em `src/contas/ui/services.py`

- [x] 4. Interface Streamlit de Importação de Faturas
  - [x] 4.1 Adicionar checkbox "Listar lançamentos de faturas futuras"
  - [x] 4.2 Adicionar checkbox "Projetar e lançar parcelas futuras restantes como pendentes"
  - [x] 4.3 Adicionar coluna editável "Fatura Futura?" no `st.data_editor`
  - [x] 4.4 Implementar lógica de gravação com `status=TransactionStatus.PENDING` para itens futuros
  - [x] 4.5 Implementar loop de projeção das parcelas restantes (offset de meses com `add_months` e status pendente)
  - [x] 4.6 Sincronizar seleção da tabela com `selected_for_import`, permitindo marcar/desmarcar via comandos no chat interativo e invalidando o cache do editor
  - [x] 4.7 Permitir desfazer/resetar filtros anteriores por linguagem natural via histórico de `invoice_items_original`

- [x] 5. Testes e Validação
  - [x] 5.1 Atualizar `tests/unit/test_invoice_parser.py` para testar `is_future` e comandos de seleção via chat
  - [x] 5.2 Atualizar `tests/unit/test_schemas.py` para validar `RecordTransactionInput` com status pendente
  - [x] 5.3 Adicionar teste em `tests/unit/test_ui_services.py` para validar chamada de gravação pendente e parcelada
  - [x] 5.4 Executar `uv run ruff check --fix . && uv run ruff format .`
  - [x] 5.5 Executar suite de testes unitários com `pytest`

