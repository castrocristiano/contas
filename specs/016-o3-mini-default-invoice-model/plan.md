# Plano de Implementação - Feature 016: o3-mini como Modelo Padrão

## 1. Módulo de Configuração
- Em `src/contas/config.py`:
  - Alterar o default de `invoice_model`:
    ```python
    invoice_model: str = "o3-mini"
    ```
- Em `.env.example`:
  - Atualizar comentário e valor padrão de `INVOICE_MODEL=o3-mini`.

## 2. Camada de UI (Streamlit)
- Em `src/contas/ui/app.py`:
  - Reordenar a lista de opções para colocar `"o3-mini"` em primeiro lugar:
    ```python
    model_options = ["o3-mini", "gpt-4o", "gpt-4o-mini"]
    ```
  - Garantir que `default` seja `settings.invoice_model`.

## 3. Testes Automatizados
- Executar `tests/unit/test_invoice_parser.py` para garantir que as funções continuam funcionando com o novo default.
- Adicionar asserção em teste unitário verificando que `settings.invoice_model == "o3-mini"`.

## 4. Validação
- Validar logs de inicialização e interface web com `podman-compose`.
