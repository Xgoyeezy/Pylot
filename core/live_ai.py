from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from core.openai_client import get_openai_client


DEFAULT_MODEL = "gpt-4o-mini"

ROLE_PROMPTS = {
    "tutor": (
        "You are an expert Python tutor inside Pylix. "
        "Teach clearly, step by step. Use examples often. "
        "Prefer hints before full solutions when the student seems stuck. "
        "Assume the learner may be a beginner unless context shows otherwise."
    ),
    "debugger": (
        "You are a Python debugging expert. "
        "Explain what is wrong, why it happened, and how to fix it. "
        "Be concrete and practical. "
        "When useful, show corrected code and prevention tips."
    ),
    "reviewer": (
        "You are a Python code reviewer. "
        "Evaluate completeness, clarity, correctness, and Python best practices. "
        "Give direct, constructive feedback. "
        "Point out what is strong, what is weak, and what to improve next."
    ),
}


def build_system_prompt(role: str) -> str:
    return ROLE_PROMPTS.get(
        role,
        "You are a helpful Python programming assistant.",
    )


def _format_mapping_block(title: str, data: Dict[str, Any]) -> str:
    if not data:
        return ""

    lines: List[str] = [f"{title}:"]
    for key, value in data.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def build_user_prompt(
    question: str = "",
    code: str = "",
    error_text: str = "",
    lesson: Optional[Dict[str, Any]] = None,
    weak_topics: Optional[Dict[str, Any]] = None,
    personalization: Optional[Dict[str, Any]] = None,
    shared_memory: Optional[List[str]] = None,
) -> str:
    sections: List[str] = []

    if lesson:
        lesson_block = _format_mapping_block("Learning context", lesson)
        if lesson_block:
            sections.append(lesson_block)

    if weak_topics:
        weak_topic_block = _format_mapping_block("Weak topics", weak_topics)
        if weak_topic_block:
            sections.append(weak_topic_block)

    if personalization:
        personalization_block = _format_mapping_block("Personalization", personalization)
        if personalization_block:
            sections.append(personalization_block)

    if shared_memory:
        memory_lines = ["Shared memory:"]
        for item in shared_memory:
            memory_lines.append(f"- {item}")
        sections.append("\n".join(memory_lines))

    if question.strip():
        sections.append(f"Student request:\n{question.strip()}")

    if code.strip():
        sections.append(f"Student code:\n```python\n{code.strip()}\n```")

    if error_text.strip():
        sections.append(f"Error message or traceback:\n{error_text.strip()}")

    if not sections:
        sections.append("Help with Python.")

    return "\n\n".join(sections)


def build_messages(system_prompt: str, user_prompt: str) -> List[ChatCompletionMessageParam]:
    system_message: ChatCompletionSystemMessageParam = {
        "role": "system",
        "content": system_prompt,
    }
    user_message: ChatCompletionUserMessageParam = {
        "role": "user",
        "content": user_prompt,
    }
    return [system_message, user_message]


def extract_response_text(response: Any) -> str:
    try:
        message = response.choices[0].message
        if message and message.content:
            return str(message.content)
    except Exception:
        pass
    return ""


def get_live_ai_response(
    role: str,
    question: str = "",
    code: str = "",
    error_text: str = "",
    lesson: Optional[Dict[str, Any]] = None,
    weak_topics: Optional[Dict[str, Any]] = None,
    personalization: Optional[Dict[str, Any]] = None,
    shared_memory: Optional[List[str]] = None,
    model: str = DEFAULT_MODEL,
    use_shared_memory: bool = True,
) -> Tuple[str, str, str]:
    if not use_shared_memory:
        shared_memory = None

    system_prompt = build_system_prompt(role)
    user_prompt = build_user_prompt(
        question=question,
        code=code,
        error_text=error_text,
        lesson=lesson,
        weak_topics=weak_topics,
        personalization=personalization,
        shared_memory=shared_memory,
    )

    client = get_openai_client()
    if client is None:
        raise RuntimeError("OpenAI API key is not configured.")

    response = client.chat.completions.create(
        model=model,
        messages=build_messages(system_prompt, user_prompt),
        temperature=0.5,
    )

    reply = extract_response_text(response)
    return system_prompt, user_prompt, reply
