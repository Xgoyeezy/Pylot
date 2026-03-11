from __future__ import annotations

import os
from typing import Optional

import streamlit as st
from openai import OpenAI


_client: Optional[OpenAI] = None


def get_openai_api_key() -> str | None:
    try:
        api_key = st.secrets.get("OPENAI_API_KEY")
        if api_key:
            return str(api_key)
    except (AttributeError, KeyError):
        pass

    env_key = os.getenv("OPENAI_API_KEY")
    return env_key if env_key else None


def get_openai_client() -> OpenAI | None:
    global _client

    if _client is not None:
        return _client

    api_key = get_openai_api_key()
    if not api_key:
        return None

    _client = OpenAI(api_key=api_key)
    return _client


def reset_openai_client() -> None:
    global _client
    _client = None