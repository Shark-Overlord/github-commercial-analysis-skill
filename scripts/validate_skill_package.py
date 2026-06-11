from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def check_skill_frontmatter() -> str:
    skill = ROOT / "SKILL.md"
    if not skill.exists():
        fail("SKILL.md does not exist")
    text = skill.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail("SKILL.md missing YAML frontmatter")
    try:
        _, frontmatter, body = text.split("---", 2)
    except ValueError:
        fail("SKILL.md frontmatter is not closed")
    keys = [line.split(":", 1)[0].strip() for line in frontmatter.splitlines() if line.strip()]
    if keys != ["name", "description"]:
        fail(f"SKILL.md frontmatter keys must be name and description only, got {keys}")
    if "name: github-commercial-analysis-skill" not in frontmatter:
        fail("SKILL.md name must be github-commercial-analysis-skill")
    return body


def check_references(skill_body: str) -> None:
    refs = sorted(set(re.findall(r"`([^`]+\.(?:md|json|html|yaml|py))`", skill_body)))
    ignored = {
        "github-opportunity-daily-report.html",
        "data/config/current-user-profile.json",
    }
    for ref in refs:
        if ref in ignored:
            continue
        if not (ROOT / ref).exists():
            fail(f"Referenced file does not exist: {ref}")


def check_json() -> None:
    for path in ROOT.rglob("*.json"):
        if "data" in path.relative_to(ROOT).parts:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(f"JSON parse failed: {path.relative_to(ROOT)}: {exc}")


def check_html_templates() -> None:
    for path in (ROOT / "templates").glob("*.html"):
        text = path.read_text(encoding="utf-8").lower().replace("'", '"')
        if '<meta charset="utf-8"' not in text:
            fail(f"HTML template missing UTF-8 meta: {path.relative_to(ROOT)}")
        blocked = ["cdn.", "<script src=", 'rel="stylesheet"', "@import"]
        hit = next((item for item in blocked if item in text), None)
        if hit:
            fail(f"HTML template has external dependency marker {hit}: {path.relative_to(ROOT)}")


def check_openai_yaml() -> None:
    path = ROOT / "agents" / "openai.yaml"
    if not path.exists():
        fail("agents/openai.yaml does not exist")
    text = path.read_text(encoding="utf-8")
    for marker in ["display_name:", "short_description:", "default_prompt:"]:
        if marker not in text:
            fail(f"agents/openai.yaml missing {marker}")
    if "$github-commercial-analysis-skill" not in text:
        fail("agents/openai.yaml default_prompt must mention $github-commercial-analysis-skill")


def check_package_json() -> None:
    path = ROOT / "package.json"
    if not path.exists():
        fail("package.json does not exist")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("name") != "github-commercial-analysis-skill":
        fail("package.json name must be github-commercial-analysis-skill")
    bin_path = (data.get("bin") or {}).get("github-commercial-analysis-skill")
    if bin_path != "scripts/install-skill.mjs":
        fail("package.json bin must point to scripts/install-skill.mjs")
    if not (ROOT / bin_path).exists():
        fail(f"package.json bin target does not exist: {bin_path}")


def main() -> None:
    body = check_skill_frontmatter()
    check_references(body)
    check_json()
    check_html_templates()
    check_openai_yaml()
    check_package_json()
    print("[OK] skill package validation passed")


if __name__ == "__main__":
    main()
