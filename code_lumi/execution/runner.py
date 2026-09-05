"""Language execution used by the editor and notebook interfaces."""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
import webbrowser
from collections.abc import Callable


ErrorHandler = Callable[[str, str, str], str]


def execute_code(language: str, code: str, explain_error: ErrorHandler) -> str:
    if not code.strip():
        return "Error: No code to run."
    try:
        if language in {"Python", "Python (.ipynb)"}:
            return _run_python(
                code,
                explain_error,
                print_last_expression=language == "Python (.ipynb)",
            )
        if language == "JavaScript":
            return _run_process(["node", "-e", code], language, code, explain_error)
        if language in {"C", "C++", "Java"}:
            return _run_compiled(language, code, explain_error)
        if language == "HTML/CSS":
            return _preview_html(code)
        return f"Execution for {language} is not implemented."
    except Exception as error:
        return f"Execution Error: {error}"


def _run_python(
    code: str,
    explain_error: ErrorHandler,
    print_last_expression: bool,
) -> str:
    execution_code = code
    if print_last_expression:
        try:
            tree = ast.parse(code)
            if tree.body and isinstance(tree.body[-1], ast.Expr):
                tree.body[-1] = ast.Expr(
                    value=ast.Call(
                        func=ast.Name(id="print", ctx=ast.Load()),
                        args=[tree.body[-1].value],
                        keywords=[],
                    )
                )
                execution_code = ast.unparse(tree)
        except (SyntaxError, ValueError):
            pass
    return _run_process(
        [sys.executable, "-c", execution_code],
        "Python",
        code,
        explain_error,
    )


def _run_process(
    command: list[str],
    language: str,
    original_code: str,
    explain_error: ErrorHandler,
    cwd: str | None = None,
) -> str:
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=cwd,
    )
    if result.returncode != 0:
        return explain_error(language, original_code, result.stderr)
    return result.stdout


def _run_compiled(language: str, code: str, explain_error: ErrorHandler) -> str:
    with tempfile.TemporaryDirectory(prefix="code_lumi_") as temp_directory:
        if language == "Java":
            source_path = os.path.join(temp_directory, "TempApp.java")
            with open(source_path, "w", encoding="utf-8") as source_file:
                source_file.write(code)
            compilation = subprocess.run(
                ["javac", source_path], capture_output=True, text=True, encoding="utf-8"
            )
            if compilation.returncode != 0:
                return explain_error(language, code, compilation.stderr)
            return _run_process(
                ["java", "TempApp"], language, code, explain_error, temp_directory
            )

        extension = ".c" if language == "C" else ".cpp"
        compiler = "gcc" if language == "C" else "g++"
        source_path = os.path.join(temp_directory, f"program{extension}")
        executable_path = os.path.join(temp_directory, "program.exe")
        with open(source_path, "w", encoding="utf-8") as source_file:
            source_file.write(code)
        compilation = subprocess.run(
            [compiler, source_path, "-o", executable_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if compilation.returncode != 0:
            return explain_error(language, code, compilation.stderr)
        return _run_process(
            [executable_path], language, code, explain_error, temp_directory
        )


def _preview_html(code: str) -> str:
    preview_path = os.path.join(tempfile.gettempdir(), "code_lumi_preview.html")
    with open(preview_path, "w", encoding="utf-8") as preview_file:
        preview_file.write(code)
    webbrowser.open("file://" + os.path.realpath(preview_path))
    return "HTML preview opened in default browser."
