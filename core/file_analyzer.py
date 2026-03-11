from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from core.ui import render_bullet_list, render_stats, section_panel


def analyze_python_file(file_text: str) -> Dict[str, Any]:
    lines = file_text.splitlines()

    results: Dict[str, Any] = {
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
    }

    for raw_line in lines:
        stripped = raw_line.strip()

        if stripped.startswith("import ") or stripped.startswith("from "):
            results["import_count"] += 1
            results["imports"].append(stripped)

        if "TODO" in raw_line or "FIXME" in raw_line:
            results["todo_count"] += 1

    try:
        tree = ast.parse(file_text)
    except SyntaxError as error:
        results["issues"].append(
            f"SyntaxError on line {error.lineno}: {error.msg}"
        )
        return results

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            results["function_count"] += 1
            results["functions"].append(node.name)
        elif isinstance(node, ast.ClassDef):
            results["class_count"] += 1
            results["classes"].append(node.name)

    if results["line_count"] > 300:
        results["issues"].append("File is getting large. Consider splitting it into smaller modules.")

    if results["todo_count"] > 0:
        results["issues"].append(f"Found {results['todo_count']} TODO/FIXME note(s).")

    if results["function_count"] == 0:
        results["issues"].append("No functions found.")

    return results


def analyze_python_path(file_path: str) -> Dict[str, Any]:
    path = Path(file_path)

    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    if not path.is_file():
        return {"error": f"Not a file: {file_path}"}

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="latin-1")

    return analyze_python_file(text)


def summarize_analysis(analysis: Dict[str, Any]) -> List[str]:
    if "error" in analysis:
        return [analysis["error"]]

    return [
        f"Lines: {analysis.get('line_count', 0)}",
        f"Characters: {analysis.get('char_count', 0)}",
        f"Imports: {analysis.get('import_count', 0)}",
        f"Functions: {analysis.get('function_count', 0)}",
        f"Classes: {analysis.get('class_count', 0)}",
        f"TODO/FIXME notes: {analysis.get('todo_count', 0)}",
    ]


def render_summary_block(analysis: Dict[str, Any]) -> None:
    render_stats(
        [
            ("Lines", analysis["line_count"]),
            ("Imports", analysis["import_count"]),
            ("Functions", analysis["function_count"]),
            ("Classes", analysis["class_count"]),
        ]
    )

    extra_col1, extra_col2 = st.columns(2)
    with extra_col1:
        st.metric("Characters", analysis["char_count"])
    with extra_col2:
        st.metric("TODO / FIXME", analysis["todo_count"])

    st.markdown("### Summary")
    render_bullet_list(summarize_analysis(analysis))


def render_list_section(title: str, values: List[str], language: str | None = None) -> None:
    if not values:
        return

    st.markdown(f"### {title}")

    if language:
        for value in values:
            st.code(value, language=language)
    else:
        render_bullet_list(values)


def render_issues(issues: List[str]) -> None:
    st.markdown("### Issues")

    if not issues:
        st.success("No major issues found.")
        return

    for issue in issues:
        st.warning(issue)


def render(progress_data: Dict[str, Any]) -> None:
    _ = progress_data

    section_panel(
        title="File Analyzer Mode",
        description="Upload a Python file to inspect imports, functions, classes, syntax issues, and TODO markers.",
        icon="📂",
    )

    uploaded_file = st.file_uploader(
        "Upload a Python file",
        type=["py"],
        key="file_analyzer_uploader",
    )

    if not uploaded_file:
        st.info("Upload a .py file to analyze it.")
        return

    try:
        file_text = uploaded_file.read().decode("utf-8")
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        file_text = uploaded_file.read().decode("latin-1")

    analysis = analyze_python_file(file_text)

    if "error" in analysis:
        st.error(analysis["error"])
        return

    render_summary_block(analysis)
    render_list_section("Imports", analysis["imports"], language="python")
    render_list_section("Functions", analysis["functions"])
    render_list_section("Classes", analysis["classes"])
    render_issues(analysis["issues"])

    with st.expander("Show file contents", expanded=False):
        st.code(file_text, language="python")