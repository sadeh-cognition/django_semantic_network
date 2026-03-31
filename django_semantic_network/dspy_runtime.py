import os

import dspy


def _normalize_model_name(model: str, api_base: str | None = None) -> str:
    if "/" in model or not api_base:
        return model
    # OpenAI-compatible local providers typically expect the OpenAI adapter in DSPy.
    return f"openai/{model}"


def get_lm(
    model: str,
    *,
    api_base: str | None = None,
    api_key: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 4000,
) -> dspy.LM:
    kwargs = {
        "model": _normalize_model_name(model, api_base),
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if api_base:
        kwargs["api_base"] = api_base
    if api_key:
        kwargs["api_key"] = api_key
    return dspy.LM(**kwargs)


def get_default_chat_lm(model: str | None = None) -> dspy.LM:
    return get_lm(
        model=model or os.environ.get("LLM_MODEL", "groq/llama-3.1-8b-instant"),
        api_base=os.environ.get("LLM_API_BASE"),
        api_key=os.environ.get("LLM_API_KEY"),
        temperature=0.0,
    )


def get_embedding_config() -> tuple[str, str, str]:
    return (
        os.environ.get("EMBEDDING_MODEL", "text-embedding-embeddinggemma-300m"),
        os.environ.get("EMBEDDING_PROVIDER", "LMStudio"),
        os.environ.get("EMBEDDING_API_BASE", "http://localhost:1234"),
    )


def get_embedder(
    model: str,
    *,
    api_base: str | None = None,
    api_key: str | None = None,
    batch_size: int = 200,
    caching: bool = True,
) -> dspy.Embedder:
    kwargs = {
        "model": _normalize_model_name(model, api_base),
        "batch_size": batch_size,
        "caching": caching,
    }
    if api_base:
        kwargs["api_base"] = api_base
    if api_key:
        kwargs["api_key"] = api_key
    return dspy.Embedder(**kwargs)


def get_default_embedder(model: str | None = None) -> dspy.Embedder:
    return get_embedder(
        model=model
        or os.environ.get("LMSTUDIO_EMBEDDING_MODEL", "text-embedding-ada-002"),
        api_base=os.environ.get("LMSTUDIO_API_BASE", "http://localhost:1234/v1"),
        api_key=os.environ.get("LMSTUDIO_API_KEY"),
    )
