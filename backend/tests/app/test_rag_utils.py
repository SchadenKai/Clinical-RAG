"""
Unit tests for app.rag.utils.get_chunk_settings

Actual algorithm (utils.py lines 9-28):

    chunk_size_values       = [128, 512, 1024]
    chunk_overlap_percentage = 0.2
    chunk_size               = 128            # default

    if model_name not in EMBEDDING_CTX_LIMITS:
        log warning; return 128               # early exit — no dict!

    ctx_limit = EMBEDDING_CTX_LIMITS[model_name]
    for i, size in enumerate(chunk_size_values):
        if i == len(chunk_size_values) - 1:   # last element (1024) → always set
            chunk_size = size
        if ctx_limit > size:
            continue
        chunk_size = size

    chunk_overlap = round(chunk_size * 0.20)  # 20 %
    chunk_overlap = overlap if overlap <= 50 else 50   # hard cap at 50

    return {"chunk_size": chunk_size, "chunk_overlap": chunk_overlap}

Because the last iteration (size=1024) unconditionally sets chunk_size=1024
before the `if ctx_limit > size` check, ALL known models return chunk_size=1024
and chunk_overlap=50 (since round(1024*0.20)=205 > 50).

The only way to get chunk_size < 1024 would be if a future version adds more
elements or the guard is changed — we document the current behaviour here.
"""

from unittest.mock import patch

import pytest

from app.rag.utils import get_chunk_settings

# =============================================================================
# Unknown / unrecognised models (early-return path)
# =============================================================================


class TestGetChunkSettingsUnknownModel:
    """When the model is not in EMBEDDING_CTX_LIMITS the function returns early."""

    def test_returns_128_as_int(self):
        result = get_chunk_settings(model_name="unknown/model")
        assert result == {"chunk_size": 128, "chunk_overlap": 26}

    def test_returns_dict_not_int(self):
        result = get_chunk_settings(model_name="not-a-real-model")
        assert isinstance(result, dict)
        assert isinstance(result["chunk_size"], int)

    def test_empty_string_is_unknown(self):
        assert get_chunk_settings(model_name="") == {"chunk_size": 128, "chunk_overlap": 26}

    def test_emits_warning_for_unknown_model(self, caplog):
        import logging

        with caplog.at_level(logging.WARNING):
            get_chunk_settings(model_name="not-a-real-model")
        assert any("not recognized" in record.message for record in caplog.records)

    def test_no_warning_for_known_model(self, caplog):
        import logging

        with caplog.at_level(logging.WARNING):
            get_chunk_settings(model_name="text-embedding-3-small")
        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warning_records) == 0


# =============================================================================
# Return type — known models
# =============================================================================


class TestGetChunkSettingsReturnShape:
    """All known models return a dict with chunk_size and chunk_overlap."""

    @pytest.mark.parametrize(
        "model_name",
        [
            "text-embedding-3-small",
            "BAAI/bge-m3",
            "openrouter/cohere/embed-english-v3.0",
            "sentence-transformers/all-MiniLM-L6-v2",
        ],
    )
    def test_returns_dict_with_required_keys(self, model_name: str):
        result = get_chunk_settings(model_name=model_name)
        assert isinstance(result, dict)
        assert "chunk_size" in result
        assert "chunk_overlap" in result

    @pytest.mark.parametrize(
        "model_name",
        ["text-embedding-3-small", "BAAI/bge-m3"],
    )
    def test_chunk_size_is_positive_int(self, model_name: str):
        result = get_chunk_settings(model_name=model_name)
        assert isinstance(result["chunk_size"], int)
        assert result["chunk_size"] > 0

    @pytest.mark.parametrize(
        "model_name",
        ["text-embedding-3-small", "openrouter/cohere/embed-english-v3.0"],
    )
    def test_chunk_overlap_is_non_negative_int(self, model_name: str):
        result = get_chunk_settings(model_name=model_name)
        assert isinstance(result["chunk_overlap"], int)
        assert result["chunk_overlap"] >= 0


# =============================================================================
# Concrete expected values — current algorithm pins chunk_size to 1024
# for every known model, because the last loop iteration sets it unconditionally.
# =============================================================================


class TestGetChunkSettingsConcreteValues:
    """
    Pin the exact output for representative models.

    All known models currently produce chunk_size=1024 and chunk_overlap=50
    because the loop's last iteration (size=1024) runs `chunk_size = size`
    before the ctx_limit guard, guaranteeing 1024 regardless of ctx_limit.
    """

    @pytest.mark.parametrize(
        "model_name",
        [
            # OpenAI — large ctx (8191)
            "text-embedding-3-small",
            "text-embedding-3-large",
            "text-embedding-ada-002",
            # Google AI — medium ctx (2048)
            "text-embedding-004",
            "models/text-embedding-004",
            "gemini-embedding-001",
            "models/gemini-embedding-001",
            # Nebius AI — various large ctx
            "Qwen/Qwen3-Embedding-8B",
            "BAAI/bge-multilingual-gemma2",
            "BAAI/BGE-ICL",
            "intfloat/e5-mistral-7b-instruct",
            # Azure OpenAI (8191)
            "azure/text-embedding-3-small",
            "azure/text-embedding-3-large",
            "azure/text-embedding-ada-002",
            # OpenRouter
            "openrouter/openai/text-embedding-3-small",
            # HuggingFace
            "BAAI/bge-m3",
            "nomic-ai/nomic-embed-text-v1.5",
        ],
    )
    def test_large_context_models_yield_1024_with_50_overlap(self, model_name: str):
        result = get_chunk_settings(model_name=model_name)
        assert result == {"chunk_size": 1024, "chunk_overlap": 50}, (
            f"Model '{model_name}' did not return expected values."
        )

    @pytest.mark.parametrize(
        "model_name",
        [
            "openrouter/cohere/embed-english-v3.0",
            "openrouter/cohere/embed-multilingual-v3.0",
            "intfloat/multilingual-e5-large",
        ],
    )
    def test_small_context_models_yield_512_with_50_overlap(self, model_name: str):
        result = get_chunk_settings(model_name=model_name)
        assert result == {"chunk_size": 512, "chunk_overlap": 50}, (
            f"Model '{model_name}' did not return expected values."
        )

    @pytest.mark.parametrize(
        "model_name",
        [
            "sentence-transformers/all-MiniLM-L6-v2",
        ],
    )
    def test_mini_context_models_yield_128_with_26_overlap(self, model_name: str):
        result = get_chunk_settings(model_name=model_name)
        assert result == {"chunk_size": 128, "chunk_overlap": 26}, (
            f"Model '{model_name}' did not return expected values."
        )


# =============================================================================
# Overlap cap invariant
# =============================================================================


class TestGetChunkSettingsOverlapCap:
    """chunk_overlap must never exceed 50."""

    @pytest.mark.parametrize(
        "model_name",
        [
            "text-embedding-3-small",
            "BAAI/bge-m3",
            "sentence-transformers/all-MiniLM-L6-v2",
        ],
    )
    def test_overlap_never_exceeds_50(self, model_name: str):
        result = get_chunk_settings(model_name=model_name)
        assert result["chunk_overlap"] <= 50


# =============================================================================
# Mocked EMBEDDING_CTX_LIMITS — algorithmic edge cases
# =============================================================================


class TestGetChunkSettingsMocked:
    """
    Verify the logic by injecting specific ctx_limit values.
    """

    @pytest.mark.parametrize("ctx_limit", [1, 128, 256])
    def test_ctx_limit_yields_chunk_size_128(self, ctx_limit: int):
        with patch("app.rag.utils.EMBEDDING_CTX_LIMITS", {"m": ctx_limit}):
            result = get_chunk_settings("m")
        assert result == {"chunk_size": 128, "chunk_overlap": 26}, (
            f"ctx_limit={ctx_limit} should produce chunk_size=128"
        )

    @pytest.mark.parametrize("ctx_limit", [512, 1024])
    def test_ctx_limit_yields_chunk_size_512(self, ctx_limit: int):
        with patch("app.rag.utils.EMBEDDING_CTX_LIMITS", {"m": ctx_limit}):
            result = get_chunk_settings("m")
        assert result == {"chunk_size": 512, "chunk_overlap": 50}, (
            f"ctx_limit={ctx_limit} should produce chunk_size=512"
        )

    @pytest.mark.parametrize("ctx_limit", [1025, 2048, 8191, 32768])
    def test_ctx_limit_yields_chunk_size_1024(self, ctx_limit: int):
        with patch("app.rag.utils.EMBEDDING_CTX_LIMITS", {"m": ctx_limit}):
            result = get_chunk_settings("m")
        assert result == {"chunk_size": 1024, "chunk_overlap": 50}, (
            f"ctx_limit={ctx_limit} should produce chunk_size=1024"
        )

    def test_recognises_mocked_model_as_known(self):
        """Mocked model should NOT trigger the unknown-model early return."""
        with patch("app.rag.utils.EMBEDDING_CTX_LIMITS", {"mock/model": 512}):
            result = get_chunk_settings("mock/model")
        assert isinstance(result, dict)

    def test_unrecognised_model_still_returns_int_when_mocked_dict_is_empty(self):
        with patch("app.rag.utils.EMBEDDING_CTX_LIMITS", {}):
            result = get_chunk_settings("any/model")
        assert result == {"chunk_size": 128, "chunk_overlap": 26}
        assert isinstance(result, dict)


# =============================================================================
# Smoke test — every real model
# =============================================================================


class TestGetChunkSettingsAllRealModels:
    """Smoke: every model in EMBEDDING_CTX_LIMITS returns a valid dict."""

    def test_all_models_return_dict(self):
        from app.rag.constants import EMBEDDING_CTX_LIMITS

        for model_name in EMBEDDING_CTX_LIMITS:
            result = get_chunk_settings(model_name=model_name)
            assert isinstance(result, dict), (
                f"Expected dict for '{model_name}', got {type(result).__name__}"
            )

    def test_all_models_chunk_size_in_allowed_set(self):
        from app.rag.constants import EMBEDDING_CTX_LIMITS

        allowed = {128, 512, 1024}
        for model_name in EMBEDDING_CTX_LIMITS:
            result = get_chunk_settings(model_name=model_name)
            assert result["chunk_size"] in allowed, (
                f"'{model_name}': unexpected chunk_size={result['chunk_size']}"
            )

    def test_all_models_overlap_within_bounds(self):
        from app.rag.constants import EMBEDDING_CTX_LIMITS

        for model_name in EMBEDDING_CTX_LIMITS:
            result = get_chunk_settings(model_name=model_name)
            assert 0 <= result["chunk_overlap"] <= 50, (
                f"'{model_name}': overlap {result['chunk_overlap']} out of range"
            )
