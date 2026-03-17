from __future__ import annotations

import ast
from typing import Any, Dict, List

import streamlit as st

from core.ui import bullet_list, metric_row, mode_header


def analyze_python_file(file_text: str) -> Dict[str, Any]:
    lines = file_text.splitlines()

    analysis: Dict[str, Any] = {
        "line_count": len(lines),
        "char_count": len(file_text),
        "import_count": 0,
        "function_count": 0,
        "class_count": 0,
        "todo_count": 0,
        "issues": [],
        "imports": [],
        "functions": [],
        "classes": [],
        "complexity_hints": [],
        "docstring_hints": [],
        "style_hints": [],
        "branch_count": 0,
        "long_lines": 0,
    }

    for raw_line in lines:
        stripped = raw_line.strip()

        if stripped.startswith("import ") or stripped.startswith("from "):
            analysis["import_count"] += 1
            analysis["imports"].append(stripped)

        if "TODO" in raw_line or "FIXME" in raw_line:
            analysis["todo_count"] += 1

        if len(raw_line) > 100:
            analysis["long_lines"] += 1

    try:
        tree = ast.parse(file_text)
    except SyntaxError as error:
        analysis["issues"].append(f"SyntaxError on line {error.lineno}: {error.msg}")
        return analysis

    branch_count = 0
    function_nodes: List[ast.AST] = []
    class_nodes: List[ast.AST] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            analysis["function_count"] += 1
            analysis["functions"].append(node.name)
            function_nodes.append(node)

            if ast.get_docstring(node) is None:
                analysis["docstring_hints"].append(f"Function `{node.name}` has no docstring.")

        elif isinstance(node, ast.ClassDef):
            analysis["class_count"] += 1
            analysis["classes"].append(node.name)
            class_nodes.append(node)

            if ast.get_docstring(node) is None:
                analysis["docstring_hints"].append(f"Class `{node.name}` has no docstring.")

        elif isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.Match)):
            branch_count += 1

    analysis["branch_count"] = branch_count

    module_docstring = ast.get_docstring(tree)
    if module_docstring is None:
        analysis["docstring_hints"].append("Module has no top-level docstring.")

    if analysis["line_count"] > 300:
        analysis["issues"].append("File is getting large. Consider splitting it into smaller modules.")

    if analysis["todo_count"] > 0:
        analysis["issues"].append(f"Found {analysis['todo_count']} TODO/FIXME note(s).")

    if analysis["function_count"] == 0:
        analysis["issues"].append("No functions found.")

    if analysis["long_lines"] > 0:
        analysis["style_hints"].append(
            f"Found {analysis['long_lines']} line(s) longer than 100 characters."
        )

    if analysis["function_count"] >= 12:
        analysis["complexity_hints"].append(
            "This file contains many functions and may benefit from modularization."
        )

    if analysis["class_count"] >= 5:
        analysis["complexity_hints"].append(
            "This file contains many classes and may benefit from clearer separation of responsibilities."
        )

    if analysis["import_count"] >= 10:
        analysis["complexity_hints"].append(
            "This file imports many modules. Check whether responsibilities are too broad."
        )

    if branch_count >= 10:
        analysis["complexity_hints"].append(
            "This file has a high amount of branching logic."
        )

    if analysis["line_count"] > 0 and analysis["function_count"] == 1 and analysis["class_count"] == 0:
        analysis["style_hints"].append(
            "This may be a good candidate for adding helper functions to reduce file-level logic."
        )

    return analysis


def render_summary_block(analysis: Dict[str, Any]) -> None:
    metric_row(
        [
            ("Lines", analysis["line_count"]),
            ("Imports", analysis["import_count"]),
            ("Functions", analysis["function_count"]),
            ("Classes", analysis["class_count"]),
        ]
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Characters", analysis["char_count"])
    with col2:
        st.metric("TODO / FIXME", analysis["todo_count"])
    with col3:
        st.metric("Branches", analysis["branch_count"])


def render_named_list_section(title: str, items: List[str], code_mode: bool = False) -> None:
    if not items:
        return

    st.markdown(f"### {title}")

    if code_mode:
        for item in items:
            st.code(item, language="python")
    else:
        bullet_list(items)


def render_issue_section(issues: List[str]) -> None:
    st.markdown("### Issues")

    if not issues:
        st.success("No major issues found.")
        return

    for issue in issues:
        st.warning(issue)


def render_complexity_section(hints: List[str]) -> None:
    st.markdown("### Complexity Hints")

    if not hints:
        st.info("No major complexity concerns detected.")
        return

    bullet_list(hints)


def render_docstring_section(hints: List[str]) -> None:
    st.markdown("### Documentation Hints")

    if not hints:
        st.success("Documentation coverage looks good.")
        return

    bullet_list(hints)


def render_style_section(hints: List[str]) -> None:
    st.markdown("### Style Hints")

    if not hints:
        st.info("No major style concerns detected.")
        return

    bullet_list(hints)


def render_input_area() -> str:
    uploaded_file = st.file_uploader(
        "Upload a Python file",
        type=["py"],
        key="file_analyzer_uploader",
    )

    pasted_code = st.text_area(
        "Or paste Python code",
        height=220,
        key="file_analyzer_paste",
    )

    if uploaded_file is not None:
        raw_bytes = uploaded_file.read()
        try:
            return raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return raw_bytes.decode("latin-1")

    return pasted_code


def render(progress_data: Dict[str, Any]) -> None:
    _ = progress_data

    mode_header(
        "File Analyzer Mode",
        "Upload or paste Python code to inspect imports, functions, classes, syntax issues, documentation gaps, and complexity hints.",
        "📂",
    )

    file_text = render_input_area()

    if not file_text.strip():
        st.info("Upload a .py file or paste Python code to analyze it.")
        return

    analysis = analyze_python_file(file_text)

    render_summary_block(analysis)
    render_named_list_section("Imports", analysis["imports"], code_mode=True)
    render_named_list_section("Functions", analysis["functions"])
    render_named_list_section("Classes", analysis["classes"])
    render_issue_section(analysis["issues"])
    render_complexity_section(analysis["complexity_hints"])
    render_docstring_section(analysis["docstring_hints"])
    render_style_section(analysis["style_hints"])

    with st.expander("Show File Contents", expanded=False):
        st.code(file_text, language="python")
