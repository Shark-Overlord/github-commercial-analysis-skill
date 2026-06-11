#!/usr/bin/env node

import { existsSync } from "node:fs";
import { cp, mkdir, rm } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import os from "node:os";

const sourceRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const codexHome = process.env.CODEX_HOME || join(os.homedir(), ".codex");
const targetRoot = resolve(
  process.env.INSTALL_DIR || join(codexHome, "skills", "github-commercial-analysis-skill"),
);

const rootFiles = [
  "SKILL.md",
  "README.md",
  "package.json",
  "install.ps1",
  "install.sh",
  ".gitignore",
  ".gitattributes",
];

const rootDirs = [
  "agents",
  "assets",
  "criteria",
  "examples",
  "prompts",
  "schemas",
  "scripts",
  "sop",
  "strategies",
  "templates",
  "tools",
];

function log(message) {
  console.log(`[github-commercial-analysis-skill] ${message}`);
}

async function copyFileIfExists(name) {
  const source = join(sourceRoot, name);
  if (!existsSync(source)) {
    return;
  }
  await cp(source, join(targetRoot, name), { force: true });
}

async function copyDirFresh(name) {
  const source = join(sourceRoot, name);
  if (!existsSync(source)) {
    return;
  }
  const target = join(targetRoot, name);
  await rm(target, { recursive: true, force: true });
  await cp(source, target, {
    recursive: true,
    force: true,
    filter: (item) => {
      const normalized = item.replaceAll("\\", "/");
      return !normalized.includes("/__pycache__/") && !normalized.endsWith(".pyc");
    },
  });
}

async function main() {
  log(`Installing to ${targetRoot}`);
  await mkdir(targetRoot, { recursive: true });

  for (const file of rootFiles) {
    await copyFileIfExists(file);
  }
  for (const dir of rootDirs) {
    await copyDirFresh(dir);
  }

  const skillPath = join(targetRoot, "SKILL.md");
  const agentPath = join(targetRoot, "agents", "openai.yaml");
  if (!existsSync(skillPath)) {
    throw new Error(`Install failed: SKILL.md not found at ${skillPath}`);
  }
  if (!existsSync(agentPath)) {
    throw new Error(`Install failed: agents/openai.yaml not found at ${agentPath}`);
  }

  log("Installed successfully.");
  console.log("");
  console.log("Next steps:");
  console.log("1. Restart Codex if the skill list does not refresh automatically.");
  console.log("2. In Codex, try:");
  console.log(
    "   Use $github-commercial-analysis-skill to find GitHub projects that I can turn into a paid MVP and generate an HTML report.",
  );
  console.log("");
  console.log("Optional data source setup:");
  console.log("   gh auth login --web");
}

main().catch((error) => {
  console.error(`[github-commercial-analysis-skill] ${error.message}`);
  process.exit(1);
});
