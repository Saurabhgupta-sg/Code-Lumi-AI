"""Beginner-friendly code explanations produced by a local Ollama model."""

from __future__ import annotations

import json
from dataclasses import dataclass

import ollama


DEFAULT_MODEL = "qwen2.5-coder:1.5b"


@dataclass(frozen=True)
class AnalysisResult:
    issue_line: int | None
    explanation: str
    hint: str
    display_text: str


def parse_raw_exception(raw_error: str) -> str | None:
    lines = [line.strip() for line in raw_error.strip().splitlines() if line.strip()]
    return lines[-1] if lines else None


def analyze_error(
    language: str,
    code: str,
    raw_error: str,
    model: str = DEFAULT_MODEL,
) -> AnalysisResult:
    raw_exception = parse_raw_exception(raw_error)
    prompt = f"""A student's {language} code produced an error. Explain it for a beginner.

Code (line numbers matter):
```{language}
{code}
```

Error / traceback:
{raw_error}

Respond with ONLY valid JSON, no markdown fences, no extra commentary, in exactly this shape:
{{
  "issue_line": <integer line number in the code above where the problem is, or null if you cannot tell>,
  "explanation": "<1-3 simple sentences: what went wrong and why, in beginner-friendly language>",
  "hint": "<a nudge toward the fix - do NOT give the full corrected code>"
}}"""

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        format="json",
    )
    raw_content = response["message"]["content"].strip()
    if raw_content.startswith("```"):
        raw_content = raw_content.strip("`")
        if raw_content.lower().startswith("json"):
            raw_content = raw_content[4:].strip()

    data = json.loads(raw_content)
    issue_line = data.get("issue_line")
    if not isinstance(issue_line, int) or not 1 <= issue_line <= len(code.splitlines()):
        issue_line = None
    explanation = str(data.get("explanation") or "").strip()
    hint = str(data.get("hint") or "").strip()

    header = f"⛔ {raw_exception}" if raw_exception else "⛔ Error"
    sections = [header]
    if issue_line is not None:
        sections.append(f"📍 Line {issue_line}")
    if explanation:
        sections.append(f"What happened?\n{explanation}")
    if hint:
        sections.append(f"💡 How to fix?\n{hint}")

    return AnalysisResult(issue_line, explanation, hint, "\n\n".join(sections))


def explain_code(language: str, code: str, model: str = DEFAULT_MODEL) -> str:
    prompt = (
        f"Explain what this {language} code does in one simple sentence.\n\n"
        f"```{language}\n{code}\n```"
    )
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"].strip()
