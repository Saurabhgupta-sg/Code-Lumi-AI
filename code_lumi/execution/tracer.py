"""Collect bounded, line-by-line snapshots from Python code."""

from __future__ import annotations

import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class TraceStep:
    line: int
    variables: dict[str, dict[str, str]]


def trace_python(code: str, max_steps: int = 1_000) -> list[TraceStep]:
    steps: list[TraceStep] = []

    def trace_lines(frame, event, _argument):
        if event == "line" and frame.f_code.co_filename == "<code-lumi>":
            if len(steps) >= max_steps:
                raise RuntimeError(
                    f"Animation stopped after {max_steps} steps to protect the application."
                )
            variables = {
                name: {"value": _safe_repr(value), "type": type(value).__name__}
                for name, value in frame.f_locals.items()
                if not name.startswith("__")
            }
            steps.append(TraceStep(frame.f_lineno, variables))
        return trace_lines

    compiled_code = compile(code, "<code-lumi>", "exec")
    try:
        sys.settrace(trace_lines)
        exec(compiled_code, {})
    finally:
        sys.settrace(None)
    return steps


def _safe_repr(value: object, max_length: int = 500) -> str:
    try:
        representation = repr(value)
    except Exception:
        representation = "<value could not be displayed>"
    if len(representation) > max_length:
        return representation[:max_length] + "…"
    return representation
