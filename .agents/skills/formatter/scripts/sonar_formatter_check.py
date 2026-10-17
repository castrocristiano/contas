#!/usr/bin/env python3
"""Generate SonarQube external issue reports for Ruff Formatter & Linter checks."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
FORMATTER_REPORT_PATH = PROJECT_ROOT / "sonar-formatter-issues.json"
RUFF_REPORT_PATH = PROJECT_ROOT / "ruff-report.json"


def _resolve_ruff_bin() -> str:
    venv_ruff = PROJECT_ROOT / ".venv" / "bin" / "ruff"
    if venv_ruff.exists():
        return str(venv_ruff)
    which_ruff = shutil.which("ruff")
    if which_ruff:
        return which_ruff
    raise FileNotFoundError("Ruff binary not found in .venv/bin/ruff or PATH.")


def _parse_diff_first_lines(diff_output: str) -> dict[str, int]:
    """Extract the first modified line number per file from `ruff format --diff`."""
    file_lines: dict[str, int] = {}
    current_file: str | None = None
    hunk_pattern = re.compile(r"^@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@")

    for raw_line in diff_output.splitlines():
        if raw_line.startswith("--- "):
            path_part = raw_line[4:].strip()
            path_part = path_part.removeprefix("a/")
            current_file = path_part
        elif raw_line.startswith("@@ ") and current_file:
            match = hunk_pattern.match(raw_line)
            if match and current_file not in file_lines:
                file_lines[current_file] = max(1, int(match.group(1)))

    return file_lines


def run_formatter_check(
    fix: bool = False, container_path_prefix: str | None = None
) -> int:
    ruff_bin = _resolve_ruff_bin()

    if fix:
        subprocess.run([ruff_bin, "check", "--fix", "."], cwd=PROJECT_ROOT, check=False)
        subprocess.run([ruff_bin, "format", "."], cwd=PROJECT_ROOT, check=False)

    # 1. Generate native Ruff JSON report for SonarQube (sonar.python.ruff.reportPaths)
    lint_proc = subprocess.run(
        [ruff_bin, "check", "--output-format=json", "."],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    ruff_json_text = lint_proc.stdout.strip() or "[]"
    if container_path_prefix:
        ruff_json_text = ruff_json_text.replace(
            str(PROJECT_ROOT), container_path_prefix
        )
    RUFF_REPORT_PATH.write_text(ruff_json_text, encoding="utf-8")

    # 2. Check formatting and build SonarQube Generic Issue Import JSON
    fmt_proc = subprocess.run(
        [ruff_bin, "format", "--check", "--diff", "."],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    rules: list[dict] = []
    issues: list[dict] = []

    if fmt_proc.returncode != 0:
        file_lines = _parse_diff_first_lines(fmt_proc.stdout)
        rules.append(
            {
                "id": "unformatted-file",
                "name": "Arquivo fora do padrão de formatação Ruff Formatter",
                "description": (
                    "O arquivo possui divergências de formatação em relação ao "
                    "padrão do projeto (`ruff format`). Execute `uv run ruff format .`."
                ),
                "engineId": "ruff-formatter",
                "cleanCodeAttribute": "FORMATTED",
                "impacts": [
                    {
                        "softwareQuality": "MAINTAINABILITY",
                        "severity": "MEDIUM",
                    }
                ],
            }
        )

        for rel_file, line_num in sorted(file_lines.items()):
            file_path = (
                f"{container_path_prefix}/{rel_file}"
                if container_path_prefix
                else rel_file
            )
            issues.append(
                {
                    "engineId": "ruff-formatter",
                    "ruleId": "unformatted-file",
                    "primaryLocation": {
                        "message": (
                            f"Arquivo '{rel_file}' não está formatado com Ruff Formatter. "
                            "Execute `ruff format .` antes do commit."
                        ),
                        "filePath": file_path,
                        "textRange": {"startLine": line_num},
                    },
                    "effortMinutes": 1,
                }
            )

    report_payload = {"rules": rules, "issues": issues}
    FORMATTER_REPORT_PATH.write_text(
        json.dumps(report_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    if issues:
        print(
            f"❌ [Formatter Rule] {len(issues)} arquivo(s) fora do padrão de formatação Ruff!"
        )
        for item in issues:
            loc = item["primaryLocation"]
            print(f"   - {loc['filePath']}:{loc['textRange']['startLine']}")
        return 1

    print(
        "✅ [Formatter Rule] Todos os arquivos estão devidamente formatados (0 issues)."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Ruff formatting and export SonarQube external issues."
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically run `ruff check --fix .` and `ruff format .` before checking.",
    )
    parser.add_argument(
        "--container-prefix",
        default=None,
        help="Optional path prefix replacement for containerized SonarScanner (e.g. /usr/src).",
    )
    args = parser.parse_args()
    return run_formatter_check(
        fix=args.fix, container_path_prefix=args.container_prefix
    )


if __name__ == "__main__":
    sys.exit(main())
