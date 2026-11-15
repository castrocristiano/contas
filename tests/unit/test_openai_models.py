from unittest.mock import MagicMock, PropertyMock, patch

from contas.config import Settings
from contas.services.openai_models import (
    DEFAULT_FALLBACK_MODELS,
    DEFAULT_MODEL,
    _is_compatible_chat_model,
    clear_models_cache,
    get_available_openai_models,
)


def test_is_compatible_chat_model_rules():
    assert _is_compatible_chat_model("gpt-4o") is True
    assert _is_compatible_chat_model("gpt-4o-mini") is True
    assert _is_compatible_chat_model("gpt-4o-2024-08-06") is True
    assert _is_compatible_chat_model("o1") is True
    assert _is_compatible_chat_model("o1-preview") is True
    assert _is_compatible_chat_model("chatgpt-4o-latest") is True

    # Excluded models
    assert _is_compatible_chat_model("o3-mini") is False
    assert _is_compatible_chat_model("o3-mini-2025-01-31") is False
    assert _is_compatible_chat_model("whisper-1") is False
    assert _is_compatible_chat_model("text-embedding-3-small") is False
    assert _is_compatible_chat_model("tts-1") is False
    assert _is_compatible_chat_model("dall-e-3") is False
    assert _is_compatible_chat_model("gpt-4o-realtime-preview") is False
    assert _is_compatible_chat_model("gpt-4o-audio-preview") is False


def test_fallback_when_no_api_key():
    clear_models_cache()
    with patch.object(
        Settings,
        "effective_openai_api_key",
        new_callable=PropertyMock,
        return_value="",
    ):
        models = get_available_openai_models(client=None)
        assert models == DEFAULT_FALLBACK_MODELS
        assert DEFAULT_MODEL in models
        assert "o3-mini" not in models


def test_dynamic_fetch_success():
    clear_models_cache()
    mock_client = MagicMock()

    m1 = MagicMock()
    m1.id = "gpt-4o"
    m2 = MagicMock()
    m2.id = "gpt-4o-mini"
    m3 = MagicMock()
    m3.id = "o1"
    m4 = MagicMock()
    m4.id = "whisper-1"
    m5 = MagicMock()
    m5.id = "o3-mini"

    mock_client.models.list.return_value = MagicMock(data=[m1, m2, m3, m4, m5])

    models = get_available_openai_models(client=mock_client)
    assert DEFAULT_MODEL in models
    assert "gpt-4o-mini" in models
    assert "o1" in models
    assert "whisper-1" not in models
    assert "o3-mini" not in models


def test_cache_and_force_refresh():
    clear_models_cache()
    mock_client = MagicMock()

    m1 = MagicMock()
    m1.id = "gpt-4o"
    mock_client.models.list.return_value = MagicMock(data=[m1])

    # First call - triggers API call
    models1 = get_available_openai_models(client=mock_client)
    assert mock_client.models.list.call_count == 1
    assert "gpt-4o" in models1

    # Second call without force_refresh - uses cache
    models2 = get_available_openai_models(client=mock_client)
    assert mock_client.models.list.call_count == 1
    assert models2 == models1

    # Third call with force_refresh - triggers API call again
    m2 = MagicMock()
    m2.id = "o1"
    mock_client.models.list.return_value = MagicMock(data=[m1, m2])
    models3 = get_available_openai_models(client=mock_client, force_refresh=True)
    assert mock_client.models.list.call_count == 2
    assert "o1" in models3
