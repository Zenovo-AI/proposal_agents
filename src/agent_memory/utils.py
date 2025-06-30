def split_model_and_provider(model_str: str) -> dict:
    """
    Given a model string like "openai:gpt-4.1", returns formatted config for LLM:
    {"provider": "openai", "model": "gpt-4.1"}.
    """
    provider, model = model_str.split(":", 1) if ":" in model_str else ("openai", model_str)
    return {"provider": provider, "model": model}
