# Interface Contracts: Modelos Dinâmicos OpenAI (024-dynamic-llm-models)

## 1. Assinatura da Função de Descoberta de Modelos

```python
def get_available_openai_models(
    client: OpenAI | None = None,
    force_refresh: bool = False,
) -> list[str]:
    """Retrieve available and compatible OpenAI models for invoice extraction and chat.

    Args:
        client: Optional OpenAI client instance (created from settings if None).
        force_refresh: If True, bypasses in-memory cache and fetches fresh list from API.

    Returns:
        List of compatible model identifier strings (e.g. ['gpt-4o', 'gpt-4o-mini', 'o1']).
    """
```

## 2. Contrato da Camada de Interface (Streamlit)

```python
models = get_available_openai_models()
selected_model = st.selectbox(
    "🤖 Modelo de IA (OpenAI)",
    options=models,
    index=models.index("gpt-4o") if "gpt-4o" in models else 0,
)
```
