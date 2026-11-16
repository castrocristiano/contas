"""Service for dynamically discovering and filtering compatible OpenAI models.

Provides in-memory caching and fallback models if the API is offline or unauthenticated.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from openai import OpenAI

from contas.config import settings

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o"
DEFAULT_FALLBACK_MODELS: list[str] = ["gpt-4o", "gpt-4o-mini", "o1"]

# Cache entry: (models_list, expires_at)
_CACHE: tuple[list[str], datetime] | None = None
_CACHE_TTL_SECONDS = 3600  # 1 hour


def _is_compatible_chat_model(model_id: str) -> bool:
    """Determine whether an OpenAI model ID is suitable for chat/structured outputs."""
    mid = model_id.lower().strip()

    # Exclude deprecated, audio, realtime, or non-chat models
    excluded_fragments = (
        "audio",
        "realtime",
        "transcription",
        "tts",
        "embedding",
        "dall-e",
        "o3-mini",
        "moderation",
        "search",
        "davinci",
        "babbage",
        "whisper",
    )
    if any(frag in mid for frag in excluded_fragments):
        return False

    # Retain standard chat and reasoning families
    allowed_prefixes = ("gpt-4", "o1", "chatgpt")
    return mid.startswith(allowed_prefixes)


def clear_models_cache() -> None:
    """Clear in-memory cached model list."""
    global _CACHE
    _CACHE = None


def get_available_openai_models(
    client: OpenAI | None = None,
    force_refresh: bool = False,
) -> list[str]:
    """Retrieve available and compatible OpenAI models with fallback and cache.

    Args:
        client: Optional OpenAI client instance. If None, initialized using settings.
        force_refresh: If True, bypasses the in-memory cache and performs an API call.

    Returns:
        List of compatible model identifier strings (e.g., ['gpt-4o', 'gpt-4o-mini', 'o1']).
    """
    global _CACHE

    now = datetime.now(UTC)
    if not force_refresh and _CACHE is not None:
        cached_models, expires_at = _CACHE
        if now < expires_at:
            return list(cached_models)

    # Attempt dynamic fetch via OpenAI client
    try:
        if client is None:
            api_key = settings.effective_openai_api_key
            if not api_key:
                logger.debug("OpenAI API key not configured. Using fallback models.")
                return list(DEFAULT_FALLBACK_MODELS)
            client = OpenAI(api_key=api_key)

        response = client.models.list()
        raw_ids = [m.id for m in response.data if hasattr(m, "id")]

        filtered_models = [m_id for m_id in raw_ids if _is_compatible_chat_model(m_id)]

        # Ensure priority order: default model first, followed by others deduplicated
        ordered_models: list[str] = []
        if DEFAULT_MODEL in filtered_models:
            ordered_models.append(DEFAULT_MODEL)

        for m_id in sorted(filtered_models):
            if m_id not in ordered_models:
                ordered_models.append(m_id)

        # Fallback if no matching models found
        if not ordered_models:
            ordered_models = list(DEFAULT_FALLBACK_MODELS)

        _CACHE = (ordered_models, now + timedelta(seconds=_CACHE_TTL_SECONDS))
        logger.info(
            "Successfully fetched %d OpenAI models (cached for 1h): %s",
            len(ordered_models),
            ordered_models[:5],
        )
        return list(ordered_models)

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Failed to fetch OpenAI models dynamically (%s). Using fallback models: %s",
            exc,
            DEFAULT_FALLBACK_MODELS,
        )
        return list(DEFAULT_FALLBACK_MODELS)
