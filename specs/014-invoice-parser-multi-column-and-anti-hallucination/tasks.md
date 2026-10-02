# Tarefas de Implementação - Feature 014

- [x] T001 [Service] Implementar a função `preprocess_invoice_text` em `src/contas/services/invoice_parser.py` para separar linhas com múltiplas colunas e desacoplar cabeçalhos de transações
- [x] T002 [Service] Integrar `preprocess_invoice_text` no fluxo de extração de texto de PDF (`extract_text_from_pdf` e `parse_invoice_with_openai`)
- [x] T003 [Prompt] Aprimorar o `system_prompt` de `parse_invoice_with_openai` com regras anti-simulação (bloqueio de simulações de financiamento/IOF) e deduplicação de encargos consolidados
- [x] T004 [Tests] Criar testes unitários para `preprocess_invoice_text` e regras de extração em `tests/unit/test_invoice_parser.py`
- [x] T005 [Verification] Validar a extração e o pré-processamento contra faturas de teste
- [x] T006 [Verification] Executar linter (`ruff check`), formatação (`ruff format`) e bateria de testes com `pytest`
- [x] T007 [Deploy] Rebuild do container `contas_app` via podman-compose e verificação da inicialização
