# Data Model: Modelos Dinâmicos OpenAI (024-dynamic-llm-models)

## Entidades & Estruturas de Dados

### 1. `OpenAIModelFilter` (Estrutura de filtragem em memória)

Localização: `src/contas/services/openai_models.py`

```python
class OpenAIModelFilter:
    """Filter logic to retain only chat completion and structured output compatible models."""

    ALLOWED_PREFIXES = ("gpt-4", "o1", "chatgpt")
    EXCLUDED_SUBSTRINGS = (
        "audio",
        "realtime",
        "transcription",
        "tts",
        "embedding",
        "dall-e",
        "o3-mini",
    )
```

### 2. Cache de Modelos em Memória

```python
@dataclass
class ModelsCache:
    models: list[str]
    expires_at: datetime
```

### 3. Configurações da Aplicação

Localização: `src/contas/config.py`

```python
class Settings(BaseSettings):
    ...
    invoice_model: str = "gpt-4o"
```
