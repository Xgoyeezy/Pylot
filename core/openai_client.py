from __future__ import annotations

import os
from functools import lru_cache

from openai import OpenAI


def get_openai_api_key() -> str | None:
    try:
        import streamlit as st

        secret_key = st.secrets.get("OPENAI_API_KEY")
        if secret_key:
            return str(secret_key)
    except (ImportError, AttributeError, KeyError):
        pass

    env_key = os.getenv("OPENAI_API_KEY")
    return env_key or None


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI | None:
    api_key = get_openai_api_key()
    if not api_key:
        return None

    return OpenAI(api_key=api_key)


def is_openai_configured() -> bool:
    return get_openai_api_key() is not None


def reset_openai_client() -> None:
    try:
        get_openai_client.cache_clear()
    except AttributeError:
        pass
