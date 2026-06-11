#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/Shark-Overlord/github-commercial-analysis-skill.git}"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
INSTALL_DIR="${INSTALL_DIR:-$CODEX_HOME/skills/github-commercial-analysis-skill}"

log() {
  printf '[github-commercial-analysis-skill] %s\n' "$1"
}

if ! command -v git >/dev/null 2>&1; then
  echo "Git is required. Please install Git first: https://git-scm.com/downloads" >&2
  exit 1
fi

mkdir -p "$(dirname "$INSTALL_DIR")"

if [ -d "$INSTALL_DIR" ]; then
  if [ -d "$INSTALL_DIR/.git" ]; then
    log "Existing installation found. Updating..."
    git -C "$INSTALL_DIR" pull --ff-only
  else
    echo "Install target exists but is not a Git checkout: $INSTALL_DIR" >&2
    echo "Move or delete it, then rerun installer." >&2
    exit 1
  fi
else
  log "Installing to $INSTALL_DIR"
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

if [ ! -f "$INSTALL_DIR/SKILL.md" ]; then
  echo "Install failed: SKILL.md not found." >&2
  exit 1
fi

if [ ! -f "$INSTALL_DIR/agents/openai.yaml" ]; then
  echo "Install failed: agents/openai.yaml not found." >&2
  exit 1
fi

log "Installed successfully."
cat <<'NEXT'

Next steps:
1. Restart Codex if the skill list does not refresh automatically.
2. In Codex, try:
   Use $github-commercial-analysis-skill to find GitHub projects that I can turn into a paid MVP and generate an HTML report.

Optional data source setup:
   gh auth login --web
NEXT
