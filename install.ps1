param(
    [string]$RepoUrl = "https://github.com/Shark-Overlord/github-commercial-analysis-skill.git",
    [string]$InstallDir = "$env:USERPROFILE\.codex\skills\github-commercial-analysis-skill"
)

$ErrorActionPreference = "Stop"

function Write-Step($Message) {
    Write-Host "[github-commercial-analysis-skill] $Message"
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git is required. Please install Git first: https://git-scm.com/downloads"
}

$parent = Split-Path -Parent $InstallDir
if (-not (Test-Path $parent)) {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
}

if (Test-Path $InstallDir) {
    if (Test-Path (Join-Path $InstallDir ".git")) {
        Write-Step "Existing installation found. Updating..."
        git -C $InstallDir pull --ff-only
    }
    else {
        throw "Install target exists but is not a Git checkout: $InstallDir. Move or delete it, then rerun installer."
    }
}
else {
    Write-Step "Installing to $InstallDir"
    git clone $RepoUrl $InstallDir
}

$skillPath = Join-Path $InstallDir "SKILL.md"
$agentPath = Join-Path $InstallDir "agents\openai.yaml"
if (-not (Test-Path $skillPath)) {
    throw "Install failed: SKILL.md not found at $skillPath"
}
if (-not (Test-Path $agentPath)) {
    throw "Install failed: agents/openai.yaml not found at $agentPath"
}

Write-Step "Installed successfully."
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Restart Codex if the skill list does not refresh automatically."
Write-Host "2. In Codex, try:"
Write-Host "   Use `$github-commercial-analysis-skill to find GitHub projects that I can turn into a paid MVP and generate an HTML report."
Write-Host ""
Write-Host "Optional data source setup:"
Write-Host "   gh auth login --web"
