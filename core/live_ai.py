from __future__ import annotations

import importlib
import inspect
from typing import Any, Dict, Optional

from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from core.openai_client import get_openai_client


DEFAULT_MODEL = "gpt-4o-mini"


def build_system_prompt(role: str) -> str:
    if role == "tutor":
        return (
            "You are an expert Python tutor inside a learning platform called Pylot. "
            "Teach clearly, step by step. Prefer examples and help the student reason "
            "through the solution."
        )

    if role == "debugger":
        return (
            "You are a Python debugging expert. Analyze the code and error carefully. "
            "Explain the bug and provide a corrected solution."
        )

    if role == "reviewer":
        return (
            "You are a Python code reviewer. Evaluate correctness, readability, "
            "Pythonic style, and possible edge cases."
        )

    return "You are an expert Python assistant helping a student learn Python."


def build_user_prompt(
    question: str = "",
    code: str = "",
    error_text: str = "",
    lesson: Optional[Dict[str, Any]] = None,
) -> str:
    parts: list[str] = []

    if lesson:
        parts.append(f"Lesson context:\n{lesson}")

    if question:
        parts.append(f"Student question:\n{question}")

    if code:
        parts.append(f"Student code:\n```python\n{code}\n```")

    if error_text:
        parts.append(f"Error message:\n{error_text}")

    return "\n\n".join(parts)


def extract_response_text(response: Any) -> str:
    choices = getattr(response, "choices", None)
    if choices:
        first_choice = choices[0]
        message = getattr(first_choice, "message", None)
        if message:
            content = getattr(message, "content", None)
            if isinstance(content, str) and content.strip():
                return content

    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    return ""


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def safe_build_memory_context(memory_query: str) -> str:
    try:
        memory_module = importlib.import_module("core.memory")
        builder = getattr(memory_module, "build_memory_context", None)

        if not callable(builder):
            return ""

        try:
            signature = inspect.signature(builder)
            params = signature.parameters
        except (TypeError, ValueError):
            return ""

        if "query" in params and "top_k" in params:
            return normalize_text(builder(query=memory_query, top_k=3))

        if "memory_query" in params and "top_k" in params:
            return normalize_text(builder(memory_query=memory_query, top_k=3))

        if "query" in params:
            return normalize_text(builder(query=memory_query))

        if "memory_query" in params:
            return normalize_text(builder(memory_query=memory_query))

        if "top_k" in params:
            return normalize_text(builder(top_k=3))

        if len(params) == 2:
            return normalize_text(builder(memory_query, 3))

        if len(params) == 1:
            return normalize_text(builder(memory_query))

        return normalize_text(builder())

    except ImportError:
        return ""
    except AttributeError:
        return ""
    except TypeError:
        return ""


def build_chat_messages(system_prompt: str, user_prompt: str) -> list[ChatCompletionMessageParam]:
    system_message: ChatCompletionSystemMessageParam = {
        "role": "system",
        "content": system_prompt,
    }
    user_message: ChatCompletionUserMessageParam = {
        "role": "user",
        "content": user_prompt,
    }
    return [system_message, user_message]


def get_live_ai_response(
    role: str,
    question: str = "",
    code: str = "",
    error_text: str = "",
    lesson: Optional[Dict[str, Any]] = None,
    weak_topics: Optional[Dict[str, Any]] = None,
    model: str = DEFAULT_MODEL,
    use_shared_memory: bool = True,
) -> tuple[str, str, str]:
    _ = weak_topics

    system_prompt = build_system_prompt(role)

    user_prompt = build_user_prompt(
        question=question,
        code=code,
        error_text=error_text,
        lesson=lesson,
    )

    if use_shared_memory:
        memory_query = f"{question}\n{code}\n{error_text}".strip()
        memory_context = safe_build_memory_context(memory_query)

        if memory_context:
            user_prompt += f"\n\nRelevant learning history:\n{memory_context}"

    client = get_openai_client()
    if client is None:
        raise RuntimeError(
            "OpenAI client not available. Ensure OPENAI_API_KEY is configured."
        )

    response = client.chat.completions.create(
        model=model,
        messages=build_chat_messages(system_prompt, user_prompt),
        temperature=0.4,
    )

    reply = extract_response_text(response)
    return system_prompt, user_prompt, reply