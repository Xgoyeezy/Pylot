from __future__ import annotations

from typing import List


def python_list_literal(items: List[str]) -> str:
    escaped_items = [repr(item) for item in items]
    return "[" + ", ".join(escaped_items) + "]"


def build_demo_runner_code(project_code: str, demo_inputs: List[str]) -> str:
    inputs_literal = python_list_literal(demo_inputs)

    return f'''
demo_inputs = {inputs_literal}
demo_index = 0

def input(prompt=""):
    global demo_index
    if demo_index >= len(demo_inputs):
        raise EOFError("No more demo inputs available.")
    value = demo_inputs[demo_index]
    demo_index += 1
    print(prompt + value)
    return value

{project_code}
'''.strip()