from __future__ import annotations

import base64
import hashlib
import gzip
import html
import json
import math
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CONFIG_DIR = DATA_DIR / "config"
REPORT_PATH = WORKSPACE / "github-opportunity-daily-report.html"
PROFILE_PATH = CONFIG_DIR / "current-user-profile.json"

for directory in (RAW_DIR, PROCESSED_DIR, CONFIG_DIR):
    directory.mkdir(parents=True, exist_ok=True)


USER_PROFILE: dict | None = None
DISCOVERY_TASK: dict | None = None

REQUIRED_PROFILE_FIELDS = [
    "skill_user_identity",
    "skill_user_goal",
    "project_direction",
    "target_user",
    "target_output",
    "mvp_time_budget",
    "payment_goal",
    "technical_level",
    "risk_boundary",
]

PROFILE_QUESTIONS = {
    "skill_user_identity": "当前使用这个 Skill 的人是谁？例如程序员、运营、内容创作者、创业者、企业负责人、销售、咨询顾问或研究人员。",
    "skill_user_goal": "这次使用 Skill 的目的是什么？例如找项目做产品、找内容选题、做商业调研、找客户方案、学习案例或投资/合作机会。",
    "project_direction": "你想找什么方向的 GitHub 项目？例如 Agent、RAG、浏览器自动化、图片工具、数据分析、营销自动化。",
    "target_user": "最终产品或服务卖给谁？例如个人用户、中小企业、教育机构、运营人员、开发者、咨询客户。",
    "target_output": "你希望做成什么形态？例如 Web 工具站、SaaS、小程序、浏览器插件、API、课程案例、客户方案。",
    "mvp_time_budget": "你希望多久做出 MVP？例如 1 天、3-7 天、2 周、2-4 周。",
    "payment_goal": "你希望怎么收费或验证商业化？例如订阅、按次付费、模板售卖、部署服务、企业定制。",
    "technical_level": "你能承担什么技术复杂度？例如不会代码、只会部署、会基础前后端、能接 API、可找程序员实现。",
    "risk_boundary": "有哪些明确不碰的风险边界？例如 License 不明、隐私数据、爬虫、账号自动化、金融交易、侵权、灰产。",
}

BASE_EXCLUDE_KEYWORDS = [
    "malware",
    "exploit",
    "crack",
    "bypass",
    "phishing",
    "stealer",
    "spam",
    "deepfake",
    "face-swap",
    "torrent",
]


DATA_SOURCE_CONFIG = {
    "allow_network_access": True,
    "save_raw_data": True,
    "sources": [
        {
            "name": "github_rest_search_api",
            "status": "enabled",
            "api_config_required": True,
            "base_url_or_access_method": "https://api.github.com/search/repositories",
            "setup_method": "github_cli",
            "setup_url_or_command": "gh auth login --web",
            "auth_required": True,
            "credential_source": "GitHub CLI",
            "secret_handling": "只记录凭据来源，不写入 Token。",
            "purpose": "搜索候选 GitHub 项目。",
            "fallback": "匿名访问 GitHub Search API，降低请求频率。",
            "confidence_impact": "若降级为匿名访问，候选覆盖率和稳定性下降。",
        },
        {
            "name": "github_repo_api",
            "status": "enabled",
            "api_config_required": True,
            "base_url_or_access_method": "https://api.github.com/repos/{owner}/{repo}",
            "setup_method": "github_cli",
            "setup_url_or_command": "gh auth login --web",
            "auth_required": True,
            "credential_source": "GitHub CLI",
            "secret_handling": "只记录凭据来源，不写入 Token。",
            "purpose": "获取 README、License、Release、Topics、Issues 和项目详情。",
            "fallback": "使用搜索结果中的基础字段。",
            "confidence_impact": "若无法补充详情，License、README 和成熟度判断可信度下降。",
        },
        {
            "name": "gh_archive",
            "status": "enabled",
            "api_config_required": True,
            "base_url_or_access_method": "https://data.gharchive.org/{yyyy-mm-dd-H}.json.gz",
            "setup_method": "public_endpoint",
            "setup_url_or_command": "https://www.gharchive.org/",
            "auth_required": False,
            "credential_source": "不需要 Token",
            "secret_handling": "无敏感凭据。",
            "purpose": "判断近期 GitHub 事件热度。",
            "fallback": "使用 GitHub Repo API 的 pushed_at、stars、forks、open_issues 估算。",
            "confidence_impact": "若降级，近期事件热度置信度下降。",
        },
        {
            "name": "hacker_news_algolia_api",
            "status": "enabled",
            "api_config_required": True,
            "base_url_or_access_method": "https://hn.algolia.com/api/v1/search",
            "setup_method": "public_endpoint",
            "setup_url_or_command": "https://hn.algolia.com/api",
            "auth_required": False,
            "credential_source": "不需要 Token",
            "secret_handling": "无敏感凭据。",
            "purpose": "判断海外技术社区讨论和需求热度。",
            "fallback": "标注海外社区证据不足。",
            "confidence_impact": "若不可用，舆情与需求热度分降权。",
        },
    ],
    "blocked_sources": [],
    "assumptions": [
        "GitHub 使用本地 GitHub CLI 认证。",
        "GH Archive 和 Hacker News Algolia 使用公共 endpoint。",
    ],
}


def missing_required_answers(profile: dict) -> list[str]:
    answers = profile.get("required_answers") or {}
    return [field for field in REQUIRED_PROFILE_FIELDS if not safe_text(answers.get(field)).strip()]


def profile_questions_message(missing: list[str]) -> str:
    lines = [
        "用户画像必达问题未完成，按 Skill 第 2 步要求必须先询问，不能进入 GitHub 搜索。",
        "请先回答以下问题，或把答案写入 data/config/current-user-profile.json：",
    ]
    for index, field in enumerate(missing, 1):
        lines.append(f"{index}. {field}: {PROFILE_QUESTIONS[field]}")
    lines.append("")
    lines.append("推荐 JSON 结构：")
    lines.append(json.dumps({
        "required_answers": {field: "" for field in REQUIRED_PROFILE_FIELDS},
        "target_market": "",
        "target_outputs": [],
        "technical_level": "",
        "time_budget": "",
        "risk_preference": "conservative"
    }, ensure_ascii=False, indent=2))
    return "\n".join(lines)


def load_user_profile_or_exit() -> dict:
    if not PROFILE_PATH.exists():
        print(profile_questions_message(REQUIRED_PROFILE_FIELDS), file=sys.stderr)
        raise SystemExit(2)
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    missing = missing_required_answers(profile)
    if missing:
        print(profile_questions_message(missing), file=sys.stderr)
        raise SystemExit(2)

    answers = profile["required_answers"]
    profile.setdefault("user_type", infer_user_type(answers))
    profile.setdefault("required_answer_sources", {field: "user_provided" for field in REQUIRED_PROFILE_FIELDS})
    profile["missing_required_questions"] = []
    profile.setdefault("target_market", "中文市场为主")
    profile.setdefault("target_outputs", split_outputs(answers["target_output"]))
    profile.setdefault("technical_level", normalize_technical_level(answers["technical_level"]))
    profile.setdefault("time_budget", answers["mvp_time_budget"])
    profile.setdefault("money_budget", "未明确")
    profile.setdefault("content_platforms", [])
    profile.setdefault("monetization_preferences", split_outputs(answers["payment_goal"]))
    profile.setdefault("risk_preference", "conservative")
    profile.setdefault("assumptions", ["未明确的信息按保守商业化验证处理。"])
    return profile


def infer_user_type(answers: dict) -> str:
    identity = safe_text(answers.get("skill_user_identity")).lower()
    goal = safe_text(answers.get("skill_user_goal")).lower()
    if any(word in identity for word in ["程序", "开发", "engineer", "developer"]):
        return "独立开发者"
    if any(word in identity for word in ["运营", "内容", "创作者", "自媒体"]):
        return "内容/运营型商业化用户"
    if any(word in identity for word in ["老板", "创业", "企业", "founder"]):
        return "创业者或企业负责人"
    if any(word in identity for word in ["销售", "咨询", "顾问"]):
        return "销售或咨询顾问"
    if any(word in identity for word in ["研究", "博士", "投资"]):
        return "研究/投资型机会筛选者"
    if "内容" in goal:
        return "内容选题型用户"
    return "商业机会筛选用户"


def split_outputs(value: str) -> list[str]:
    pieces = re.split(r"[、,，/；;和\s]+", safe_text(value))
    return [piece for piece in pieces if piece]


def normalize_technical_level(value: str) -> str:
    text = safe_text(value).lower()
    if any(word in text for word in ["不会", "无代码", "non-code"]):
        return "low_code"
    if any(word in text for word in ["全栈", "前后端", "full"]):
        return "full_stack"
    if any(word in text for word in ["api", "python", "node", "模型"]):
        return "ai_engineering"
    if any(word in text for word in ["找程序员", "外包", "只会部署", "部署"]):
        return "basic_web"
    return "basic_web"


def build_discovery_task(profile: dict) -> dict:
    answers = profile["required_answers"]
    direction = safe_text(answers["project_direction"]).lower()
    output = safe_text(answers["target_output"]).lower()
    target_user = safe_text(answers["target_user"]).lower()
    risk_boundary = safe_text(answers["risk_boundary"]).lower()

    keywords: list[str] = []
    topics: list[str] = []

    if any(word in direction for word in ["agent", "智能体", "workflow", "工作流"]):
        keywords.extend([
            "ai agent web app",
            "agent workflow automation",
            "multi agent framework",
            "low code ai workflow",
        ])
        topics.extend(["ai-agents", "workflow-automation", "agentic-ai"])
    if any(word in direction for word in ["skill", "技能", "codex", "mcp"]):
        keywords.extend([
            "codex skill",
            "ai agent skill",
            "mcp server tools",
            "prompt engineering toolkit",
            "chatgpt plugin open source",
        ])
        topics.extend(["codex", "mcp", "ai-tools", "prompt-engineering"])
    if any(word in direction for word in ["微信", "小程序", "mini program", "miniapp", "weapp"]):
        keywords.extend([
            "wechat mini program ai",
            "weapp ai",
            "taro ai app",
            "uni-app ai tool",
            "miniprogram ai assistant",
        ])
        topics.extend(["wechat-miniprogram", "mini-program", "weapp", "taro", "uni-app"])
    if any(word in direction for word in ["rag", "知识库", "问答"]):
        keywords.extend(["rag web app", "knowledge base chatbot", "document qa agent"])
        topics.extend(["rag", "llm", "chatbot"])
    if any(word in direction for word in ["browser", "浏览器", "网页自动化"]):
        keywords.extend(["browser automation agent", "web agent automation"])
        topics.extend(["browser-automation", "web-automation"])
    if any(word in direction for word in ["image", "图片", "图像", "设计", "design", "editor"]):
        keywords.extend([
            "image editor web",
            "canvas editor design",
            "ai design tool",
            "design to code ai",
            "fabricjs editor",
        ])
        topics.extend(["image-editor", "design-tools", "canvas", "design-to-code"])
    if any(word in direction for word in ["data", "数据", "分析"]):
        keywords.extend(["data analysis dashboard", "ai data analyst", "analytics agent"])
        topics.extend(["data-analysis", "dashboard", "analytics"])

    if "小程序" in output:
        keywords.extend(["mini app open source", "wechat mini program ai", "taro ai app"])
    if any(word in output for word in ["桌面", "desktop", "electron", "tauri"]):
        keywords.extend(["tauri ai app", "electron ai app", "desktop ai agent", "local ai desktop app"])
        topics.extend(["tauri", "electron", "desktop-app"])
    if any(word in output for word in ["web", "saas", "工具站", "网站"]):
        keywords.extend(["web app open source", "self hosted saas"])
    if any(word in target_user for word in ["企业", "business", "公司"]):
        keywords.extend(["small business ai tool", "business workflow automation"])
    if not keywords:
        keywords = ["ai tool web app", "open source saas", "workflow automation"]

    exclude = list(BASE_EXCLUDE_KEYWORDS)
    if any(word in risk_boundary for word in ["法律", "隐私", "爬虫", "账号", "金融", "侵权", "灰产"]):
        exclude.extend(["crawler", "scraper", "trading", "finance", "account automation", "privacy"])
    if any(word in risk_boundary for word in ["法律", "合规", "律师", "合同", "诉讼"]):
        exclude.extend(["law", "legal", "lawyer", "contract", "court", "lawsuit", "legaltech"])

    return {
        "search_keywords": list(dict.fromkeys(keywords))[:12],
        "topics": list(dict.fromkeys(topics))[:10],
        "exclude_keywords": list(dict.fromkeys(exclude)),
        "languages": ["TypeScript", "JavaScript", "Python", "Vue", "Rust"],
        "min_stars": 100,
        "updated_within_days": 180,
        "candidate_limit": 120,
        "shortlist_limit": 20,
        "final_report_limit": 10,
        "checks": {
            "readme": True,
            "license": True,
            "release": True,
            "github_events": True,
            "hacker_news": True,
        },
    }


def task_cache_slug(task: dict) -> str:
    payload = json.dumps(
        {
            "search_keywords": task.get("search_keywords", []),
            "required_topics": task.get("required_topics", []),
            "exclude_keywords": task.get("exclude_keywords", []),
            "updated_within_days": task.get("updated_within_days"),
            "min_stars": task.get("min_stars"),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:10]


RISK_WORDS = [
    "malware",
    "exploit",
    "crack",
    "bypass",
    "phishing",
    "stealer",
    "spam",
    "deepfake",
    "face swap",
    "faceswap",
    "scrape private",
    "captcha",
    "trading",
    "stock trading",
    "financial trading",
    "crypto trading",
    "legal",
    "lawyer",
    "lawsuit",
    "court",
    "legaltech",
]

AGENT_TERMS = [
    "agent",
    "agents",
    "workflow",
    "automation",
    "rag",
    "chatbot",
    "llm",
    "browser",
    "multi-agent",
    "memory",
]

DESIGN_TERMS = [
    "image",
    "editor",
    "canvas",
    "design",
    "graphics",
    "vector",
    "fabric",
    "photo",
    "background",
    "svg",
    "design-to-code",
    "poster",
]

SKILL_TERMS = [
    "codex skill",
    "agent skill",
    "mcp",
    "prompt engineering",
    "prompt template",
    "tool calling",
    "workflow template",
]

MINIAPP_TERMS = [
    "wechat",
    "weixin",
    "weapp",
    "mini program",
    "miniprogram",
    "小程序",
    "taro",
    "uni-app",
]

DESKTOP_TERMS = [
    "desktop",
    "tauri",
    "electron",
    "native app",
    "tray app",
]


def run_gh_api(path: str, params: dict[str, str] | None = None) -> dict:
    url = path
    if params:
        url = f"{path}?{urllib.parse.urlencode(params)}"
    cmd = [
        "gh",
        "api",
        "-H",
        "Accept: application/vnd.github+json",
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return json.loads(result.stdout)


def get_url_json(url: str, timeout: int = 20) -> dict:
    response = requests.get(url, timeout=timeout, headers={"User-Agent": "github-commercial-analysis-skill"})
    response.raise_for_status()
    return response.json()


def safe_text(value: object) -> str:
    return "" if value is None else str(value)


def compact_text(value: object, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", safe_text(value)).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "..."


def repo_text(repo: dict) -> str:
    fields = [
        repo.get("name"),
        repo.get("full_name"),
        repo.get("description"),
        repo.get("language"),
        " ".join(repo.get("topics") or []),
        repo.get("readme_excerpt"),
    ]
    return " ".join(safe_text(x) for x in fields).lower()


def has_any(text: str, words: list[str]) -> bool:
    return any(word in text for word in words)


def word_has(text: str, phrase: str) -> bool:
    if not phrase:
        return False
    return re.search(r"(?<![a-z0-9])" + re.escape(phrase.lower()) + r"(?![a-z0-9])", text.lower()) is not None


def domain_of(url: str | None) -> str:
    if not url:
        return ""
    try:
        return urllib.parse.urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def project_category(repo: dict) -> str:
    text = repo_text(repo)
    agent_hits = sum(1 for word in AGENT_TERMS if word in text)
    design_hits = sum(1 for word in DESIGN_TERMS if word in text)
    skill_hits = sum(1 for word in SKILL_TERMS if word in text)
    miniapp_hits = sum(1 for word in MINIAPP_TERMS if word in text)
    desktop_hits = sum(1 for word in DESKTOP_TERMS if word in text)
    if miniapp_hits > 0:
        return "miniapp"
    if desktop_hits > 0 and agent_hits > 0:
        return "desktop"
    if skill_hits > 0:
        return "skill"
    if design_hits > agent_hits + 1:
        return "design"
    if agent_hits > 0:
        return "agent"
    if design_hits > 0:
        return "design"
    return "other"


def is_browser_automation_project(repo: dict) -> bool:
    text = repo_text(repo)
    name = (repo.get("name") or repo.get("full_name") or "").lower()
    topics = {safe_text(topic).lower() for topic in (repo.get("topics") or [])}
    if "browser-automation" in topics or "browser-use" in topics:
        return True
    if "browser" in name:
        return True
    browser_phrases = [
        "browser automation",
        "web agent",
        "web agents",
        "automate websites",
        "browser agent",
        "websites accessible for ai agents",
    ]
    return any(phrase in text for phrase in browser_phrases)


def decode_readme(readme_json: dict) -> str:
    content = readme_json.get("content") or ""
    if readme_json.get("encoding") == "base64":
        try:
            return base64.b64decode(content).decode("utf-8", errors="replace")
        except Exception:
            return ""
    return content


def search_candidates() -> list[dict]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=DISCOVERY_TASK["updated_within_days"])).date().isoformat()
    seen: dict[str, dict] = {}
    for keyword in DISCOVERY_TASK["search_keywords"]:
        query = f"{keyword} stars:>{DISCOVERY_TASK['min_stars']} pushed:>{cutoff} archived:false"
        try:
            data = run_gh_api(
                "search/repositories",
                {
                    "q": query,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": "12",
                },
            )
        except Exception as exc:
            print(f"GitHub search failed for {keyword}: {exc}", file=sys.stderr)
            continue
        for item in data.get("items", []):
            full_name = item.get("full_name")
            if not full_name or full_name in seen:
                continue
            text = repo_text(item)
            if has_any(text, RISK_WORDS):
                continue
            seen[full_name] = item
        time.sleep(0.2)
    candidates = list(seen.values())
    candidates.sort(key=lambda x: int(x.get("stargazers_count") or 0), reverse=True)
    return candidates[: DISCOVERY_TASK["candidate_limit"]]


def candidate_relevance(repo: dict) -> float:
    text = repo_text(repo)
    agent_hits = sum(1 for word in AGENT_TERMS if word in text)
    design_hits = sum(1 for word in DESIGN_TERMS if word in text)
    skill_hits = sum(1 for word in SKILL_TERMS if word in text)
    miniapp_hits = sum(1 for word in MINIAPP_TERMS if word in text)
    desktop_hits = sum(1 for word in DESKTOP_TERMS if word in text)
    output_hits = 0
    for word in ("web", "app", "saas", "template", "editor", "dashboard", "self-hosted", "low-code"):
        if word in text:
            output_hits += 1
    score = min(35, (agent_hits + design_hits + skill_hits + miniapp_hits + desktop_hits) * 5) + min(15, output_hits * 3)
    recency = 0
    pushed_at = repo.get("pushed_at")
    if pushed_at:
        try:
            days = (datetime.now(timezone.utc) - datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))).days
            recency = 20 if days <= 14 else 15 if days <= 60 else 10 if days <= 180 else 4
        except Exception:
            recency = 0
    stars = int(repo.get("stargazers_count") or 0)
    star_score = min(20, math.log10(max(stars, 1)) * 4)
    return score + recency + star_score


def enrich_repo(repo: dict) -> dict:
    full_name = repo["full_name"]
    enriched = dict(repo)
    try:
        detail = run_gh_api(f"repos/{full_name}")
        enriched.update(detail)
    except Exception as exc:
        enriched["repo_api_error"] = str(exc)
    try:
        readme = run_gh_api(f"repos/{full_name}/readme")
        readme_text = decode_readme(readme)
        enriched["readme_available"] = True
        enriched["readme_excerpt"] = readme_text[:4000]
    except Exception as exc:
        enriched["readme_available"] = False
        enriched["readme_error"] = str(exc)
        enriched["readme_excerpt"] = ""
    try:
        releases = run_gh_api(f"repos/{full_name}/releases", {"per_page": "3"})
        enriched["latest_releases"] = [
            {
                "name": item.get("name") or item.get("tag_name"),
                "published_at": item.get("published_at"),
            }
            for item in releases[:3]
        ]
    except Exception as exc:
        enriched["latest_releases"] = []
        enriched["releases_error"] = str(exc)
    license_obj = enriched.get("license") or {}
    enriched["license_key"] = license_obj.get("spdx_id") or license_obj.get("key") or "NOASSERTION"
    enriched["stars"] = enriched.get("stargazers_count") or enriched.get("stars") or 0
    enriched["forks"] = enriched.get("forks_count") or enriched.get("forks") or 0
    enriched["open_issues"] = enriched.get("open_issues_count") or enriched.get("open_issues") or 0
    return enriched


def shortlist(candidates: list[dict]) -> list[dict]:
    ranked = []
    for repo in candidates:
        score = candidate_relevance(repo)
        text = repo_text(repo)
        if not has_any(text, AGENT_TERMS + DESIGN_TERMS + SKILL_TERMS + MINIAPP_TERMS + DESKTOP_TERMS):
            score -= 20
        if has_any(text, RISK_WORDS):
            score -= 50
        ranked.append((score, repo))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [repo for _, repo in ranked[: DISCOVERY_TASK["shortlist_limit"]]]


def hn_relevance(repo: dict, hit: dict) -> float:
    full_name = (repo.get("full_name") or "").lower()
    owner, _, name = full_name.partition("/")
    title = (hit.get("title") or "").lower()
    url = (hit.get("url") or "").lower()
    joined = f"{title} {url}"
    homepage_domain = domain_of(repo.get("homepage"))
    homepage_url = (repo.get("homepage") or "").lower().rstrip("/")
    repo_url = (repo.get("html_url") or "").lower()
    phrase = name.replace("-", " ")
    text = repo_text(repo)
    markers = [word for word in AGENT_TERMS + DESIGN_TERMS + SKILL_TERMS + MINIAPP_TERMS + DESKTOP_TERMS if word in text]
    if full_name and full_name in joined:
        return 1.0
    if repo_url and repo_url in joined:
        return 1.0
    if homepage_url and len(homepage_url) > 12 and homepage_url in joined:
        return 1.0
    generic_domains = {"github.com", "github.io", "raw.githubusercontent.com", "twitter.com", "x.com"}
    if homepage_domain and homepage_domain not in generic_domains and homepage_domain in url:
        return 1.0
    ambiguous = name in {"agent", "agents", "graphite", "browser-use", "canva-clone"} or len(name) <= 7
    if name and word_has(title, name):
        if not ambiguous:
            return 0.85
        if any(word_has(title, marker) for marker in markers):
            return 0.75
        return 0.0
    if phrase and word_has(title, phrase):
        if name == "browser-use" and not ("agent" in title or "automation" in title or full_name in url):
            return 0.0
        return 0.7
    return 0.0


def collect_hn(repo: dict) -> dict:
    full_name = repo.get("full_name") or ""
    name = repo.get("name") or full_name.split("/")[-1]
    queries = [full_name, name]
    homepage_domain = domain_of(repo.get("homepage"))
    if homepage_domain:
        queries.append(homepage_domain)
    hits_by_id: dict[str, dict] = {}
    errors = []
    for query in queries:
        if not query:
            continue
        url = "https://hn.algolia.com/api/v1/search?" + urllib.parse.urlencode(
            {"query": query, "tags": "story", "hitsPerPage": 3}
        )
        try:
            data = get_url_json(url, timeout=3)
            for hit in data.get("hits", []):
                object_id = str(hit.get("objectID") or hit.get("story_id") or len(hits_by_id))
                hits_by_id[object_id] = hit
        except Exception as exc:
            errors.append(str(exc))
        time.sleep(0.1)
    raw_hits = list(hits_by_id.values())
    matched = []
    excluded = []
    for hit in raw_hits:
        weight = hn_relevance(repo, hit)
        item = {
            "title": hit.get("title"),
            "url": hit.get("url"),
            "points": hit.get("points") or 0,
            "comments": hit.get("num_comments") or 0,
            "created_at": hit.get("created_at"),
            "weight": weight,
        }
        if weight > 0:
            matched.append(item)
        else:
            excluded.append(item)
    weighted_points = sum(float(hit["points"]) * float(hit["weight"]) for hit in matched)
    weighted_comments = sum(float(hit["comments"]) * float(hit["weight"]) for hit in matched)
    if errors and not raw_hits:
        score = 20.0
        confidence = "low"
    elif not matched:
        score = 10.0 if not raw_hits else 15.0
        confidence = "low"
    else:
        score = min(
            100.0,
            sum(float(hit["weight"]) for hit in matched) * 10
            + min(45.0, weighted_points / 15.0)
            + min(25.0, weighted_comments / 8.0),
        )
        confidence = "high" if len(matched) >= 2 else "medium"
    return {
        "hn_hits": len(raw_hits),
        "matched_hn_hits": len(matched),
        "excluded_hn_hits": len(excluded),
        "hn_points": round(weighted_points),
        "hn_comments": round(weighted_comments),
        "discussion_titles": [safe_text(hit.get("title")) for hit in matched[:3]],
        "matched_discussions": matched[:5],
        "excluded_examples": excluded[:3],
        "discussion_summary": make_hn_summary(matched, excluded, weighted_points, weighted_comments),
        "positive_signals": make_positive_signals(repo, matched),
        "negative_signals": make_negative_signals(repo, matched, excluded),
        "match_confidence": confidence,
        "confidence": confidence,
        "score": round(score, 1),
        "errors": errors,
    }


def make_hn_summary(matched: list[dict], excluded: list[dict], points: float, comments: float) -> str:
    if not matched:
        return f"HN 无有效相关命中，排除噪声 {len(excluded)} 条，海外社区需求证据不足。"
    title = matched[0].get("title") or "未命名讨论"
    return (
        f"HN 有效命中 {len(matched)} 条，排除噪声 {len(excluded)} 条；"
        f"加权点赞 {round(points)}，加权评论 {round(comments)}。代表讨论：{title}。"
    )


def make_positive_signals(repo: dict, matched: list[dict]) -> list[str]:
    signals = []
    if matched:
        signals.append("海外技术社区出现相关讨论，可作为内容传播证据。")
    if int(repo.get("stars") or 0) > 5000:
        signals.append("Star 基数较高，说明开发者关注度已形成。")
    if repo.get("pushed_at"):
        signals.append("项目近期仍在更新，可作为 MVP 选型参考。")
    return signals or ["暂无明显正向社区信号。"]


def make_negative_signals(repo: dict, matched: list[dict], excluded: list[dict]) -> list[str]:
    signals = []
    if excluded:
        signals.append("HN 原始命中存在同名或泛词噪声，已从热度分中排除。")
    if not matched:
        signals.append("缺少有效 HN 讨论，海外社区需求验证不足。")
    license_key = repo.get("license_key") or "NOASSERTION"
    if license_key in {"NOASSERTION", "AGPL-3.0", "GPL-3.0"}:
        signals.append(f"License 为 {license_key}，商业化前需要谨慎处理。")
    return signals


def scan_gh_archive(repos: list[dict], hours: int = 6) -> dict[str, dict]:
    if "--full-gh-archive" not in sys.argv:
        return {
            safe_text(repo.get("full_name")): {
                "event_window_hours": hours,
                "star_events": 0,
                "fork_events": 0,
                "issue_events": 0,
                "pull_request_events": 0,
                "watch_events": 0,
                "total_events": 0,
                "source": "repo_api_fallback",
                "confidence": "low",
                "data_gaps": ["GH Archive 小时归档全量扫描在交互执行中降级，使用 Repo API 估算近期 GitHub 热度。"],
                "score": repo_api_heat_score(repo),
                "trend_summary": "GH Archive 本次未做小时级事件深扫，使用 Repo API 的 pushed_at、stars、forks、open_issues 估算近期热度。",
            }
            for repo in repos
        }
    names = [safe_text(repo.get("full_name")) for repo in repos]
    byte_names = {name.encode("utf-8"): name for name in names if name}
    counts = {
        name: {
            "event_window_hours": hours,
            "star_events": 0,
            "fork_events": 0,
            "issue_events": 0,
            "pull_request_events": 0,
            "watch_events": 0,
            "total_events": 0,
            "source": "gh_archive",
            "confidence": "medium",
            "data_gaps": [],
        }
        for name in names
    }
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    attempted = 0
    success = 0
    for offset in range(1, hours + 1):
        ts = now - timedelta(hours=offset)
        url = f"https://data.gharchive.org/{ts.strftime('%Y-%m-%d')}-{ts.hour}.json.gz"
        attempted += 1
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "github-commercial-analysis-skill"})
            with urllib.request.urlopen(req, timeout=45) as response:
                with gzip.GzipFile(fileobj=response) as gz:
                    for line in gz:
                        matched_name = None
                        for byte_name, name in byte_names.items():
                            if byte_name in line:
                                matched_name = name
                                break
                        if not matched_name:
                            continue
                        try:
                            event = json.loads(line.decode("utf-8"))
                        except Exception:
                            continue
                        repo_name = (event.get("repo") or {}).get("name")
                        if repo_name not in counts:
                            continue
                        event_type = event.get("type")
                        counts[repo_name]["total_events"] += 1
                        if event_type == "WatchEvent":
                            counts[repo_name]["star_events"] += 1
                            counts[repo_name]["watch_events"] += 1
                        elif event_type == "ForkEvent":
                            counts[repo_name]["fork_events"] += 1
                        elif event_type == "IssuesEvent":
                            counts[repo_name]["issue_events"] += 1
                        elif event_type == "PullRequestEvent":
                            counts[repo_name]["pull_request_events"] += 1
            success += 1
        except Exception as exc:
            for item in counts.values():
                item["data_gaps"].append(f"{url} 读取失败：{exc}")
    for repo in repos:
        name = repo.get("full_name")
        item = counts[name]
        if success == 0:
            item["source"] = "repo_api_fallback"
            item["confidence"] = "low"
            item["data_gaps"].append("GH Archive 小时归档未成功读取，改用 Repo API 估算。")
            item["score"] = repo_api_heat_score(repo)
        else:
            event_score = (
                min(45, item["star_events"] * 4)
                + min(20, item["fork_events"] * 5)
                + min(20, (item["issue_events"] + item["pull_request_events"]) * 3)
                + min(15, item["total_events"])
            )
            if item["total_events"] == 0:
                fallback = repo_api_heat_score(repo) * 0.45
                item["score"] = round(max(10.0, fallback), 1)
                item["confidence"] = "low"
                item["data_gaps"].append("GH Archive 窗口内未捕获该仓库事件，使用 Repo API 低权重补足。")
            else:
                item["score"] = round(min(100.0, event_score), 1)
        item["trend_summary"] = (
            f"最近 {hours} 小时 GH Archive 捕获事件 {item['total_events']} 个，"
            f"Star/Watch {item['star_events']}，Fork {item['fork_events']}，"
            f"Issue {item['issue_events']}，PR {item['pull_request_events']}。"
        )
    return counts


def repo_api_heat_score(repo: dict) -> float:
    pushed_at = repo.get("pushed_at")
    if pushed_at:
        try:
            days = (datetime.now(timezone.utc) - datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))).days
        except Exception:
            days = 9999
    else:
        days = 9999
    recency = 45 if days <= 7 else 35 if days <= 30 else 25 if days <= 120 else 12
    stars = int(repo.get("stars") or 0)
    issues = int(repo.get("open_issues") or 0)
    return round(min(70.0, recency + min(15.0, math.log10(max(stars, 1)) * 3) + min(10.0, issues / 100)), 1)


def score_repo(repo: dict) -> dict:
    text = repo_text(repo)
    category = project_category(repo)
    license_key = repo.get("license_key") or "NOASSERTION"
    stars = int(repo.get("stars") or 0)
    forks = int(repo.get("forks") or 0)
    agent_hits = sum(1 for word in AGENT_TERMS if word in text)
    design_hits = sum(1 for word in DESIGN_TERMS if word in text)
    skill_hits = sum(1 for word in SKILL_TERMS if word in text)
    miniapp_hits = sum(1 for word in MINIAPP_TERMS if word in text)
    desktop_hits = sum(1 for word in DESKTOP_TERMS if word in text)
    web_hits = sum(1 for word in ("web", "app", "saas", "api", "template", "editor", "dashboard") if word in text)

    user_fit = 45 + min(25, (agent_hits + skill_hits + miniapp_hits + desktop_hits + design_hits) * 4) + min(12, web_hits * 2)
    if design_hits > 0 and agent_hits > 0:
        user_fit += 8
    if skill_hits > 0:
        user_fit += 8
    if miniapp_hits > 0 or desktop_hits > 0:
        user_fit += 6
    if "course" in text or "example" in text:
        user_fit += 4
    if license_key in {"NOASSERTION", "AGPL-3.0", "GPL-3.0"}:
        user_fit -= 12
    if repo.get("language") in {"Swift", "Kotlin", "Objective-C"}:
        user_fit -= 15
    if "awesome" in text:
        user_fit -= 18

    commercial = 45 + min(18, math.log10(max(stars, 1)) * 4) + min(15, web_hits * 3)
    if any(word in text for word in ("template", "editor", "workflow", "automation", "business", "marketing", "mini program", "desktop")):
        commercial += 12
    if "framework" in text and "app" not in text:
        commercial -= 5
    if "awesome" in text or "learning-resources" in text:
        commercial -= 25

    mvp = 55
    if any(word in text for word in ("self-hosted", "web", "nextjs", "vue", "react", "typescript", "python")):
        mvp += 15
    if any(word in text for word in ("framework", "sdk", "library")):
        mvp += 5
    if stars > 50000:
        mvp -= 6
    if any(word in text for word in ("desktop", "rust", "native", "3d", "video")):
        mvp -= 10
    if "editor" in text:
        mvp -= 4
    if repo.get("language") in {"Swift", "Kotlin", "Objective-C"}:
        mvp -= 18
    if "awesome" in text:
        mvp -= 20

    content = 45 + min(18, math.log10(max(stars, 1)) * 4)
    if any(word in text for word in ("agent", "browser", "design", "image", "editor", "visual", "automation")):
        content += 20
    if repo.get("homepage"):
        content += 8

    risk = 82
    if license_key in {"MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "ISC"}:
        risk += 8
    elif license_key in {"NOASSERTION", ""}:
        risk -= 28
    elif license_key in {"AGPL-3.0", "GPL-3.0", "GPL-2.0"}:
        risk -= 38
    if has_any(text, RISK_WORDS):
        risk -= 45
    if is_browser_automation_project(repo):
        risk -= 18
    if "scrap" in text or "crawler" in text:
        risk -= 20
    if "canva" in text or "clone" in text:
        risk -= 25
    if "face" in text:
        risk -= 20
    if "trading" in text or "stock" in text or "financial" in text:
        risk -= 45
    if category == "other":
        user_fit -= 10

    scores = {
        "user_fit": clamp(user_fit),
        "commercial_potential": clamp(commercial),
        "mvp_feasibility": clamp(mvp),
        "content_virality": clamp(content),
        "risk_control": clamp(risk),
    }
    return scores


def clamp(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 1)


def recommendation_level(score: float) -> str:
    if score >= 85:
        return "强烈推荐"
    if score >= 75:
        return "推荐"
    if score >= 65:
        return "谨慎推荐"
    if score >= 50:
        return "降级为内容/学习/风险案例"
    return "不推荐"


def apply_decision_gates(repo: dict, scores: dict, final_score: float, base_level: str) -> tuple[str, list[str], int]:
    level = base_level
    gates: list[str] = []
    max_rank = 999
    license_key = repo.get("license_key") or "NOASSERTION"
    text = repo_text(repo)
    if license_key in {"NOASSERTION", ""}:
        gates.append("License 不明确，最高只能谨慎推荐。")
        if level in {"强烈推荐", "推荐"}:
            level = "谨慎推荐"
    if license_key in {"AGPL-3.0", "GPL-3.0", "GPL-2.0"}:
        gates.append(f"{license_key} 对闭源订阅或 SaaS 不友好，商业化前必须做合规评估。")
        level = "降级为内容/学习/风险案例"
    if scores["risk_control"] < 50:
        gates.append("风险可控分低于 50，不进入商业推荐。")
        level = "降级为内容/学习/风险案例"
    elif scores["risk_control"] < 65:
        gates.append("存在法律、隐私、平台规则或自动化边界风险，不做高推荐。")
        if level in {"强烈推荐", "推荐"}:
            level = "谨慎推荐"
    if is_browser_automation_project(repo):
        gates.append("浏览器自动化涉及平台规则、账号和敏感数据边界，最高只能谨慎推荐。")
        if level in {"强烈推荐", "推荐"}:
            level = "谨慎推荐"
    if scores["mvp_feasibility"] < 65:
        gates.append("2 周内不适合做出可验证 MVP，不进入前 3。")
        max_rank = 4
    if scores["user_fit"] < 65:
        gates.append("用户画像匹配不足，不进入推荐及以上。")
        if level in {"强烈推荐", "推荐"}:
            level = "谨慎推荐"
    if has_any(text, RISK_WORDS) or "face" in text or "deepfake" in text:
        gates.append("触及用户明确不碰的风险边界，只能作为风险案例。")
        level = "降级为内容/学习/风险案例"
    if "clone" in text or "canva" in text:
        gates.append("存在 clone 或品牌联想风险，必须差异化命名和定位。")
        if level in {"强烈推荐", "推荐"}:
            level = "谨慎推荐"
    return level, gates, max_rank


def product_direction(repo: dict) -> str:
    text = repo_text(repo)
    name = repo.get("full_name")
    category = project_category(repo)
    direction = USER_PROFILE["required_answers"]["project_direction"] if USER_PROFILE else "本轮关注方向"
    output = USER_PROFILE["required_answers"]["target_output"] if USER_PROFILE else "MVP"
    if category == "miniapp":
        return f"{name} 适合优先验证微信小程序形态，围绕个人用户或中小企业的轻量 AI 助手场景做订阅入口。"
    if category == "desktop":
        return f"{name} 适合包装成桌面端 AI 工具，重点验证本地效率、隐私感和个人订阅价值。"
    if category == "skill":
        return f"{name} 适合做 Agent/Skill 模板、工作流资产或教程案例，再沉淀为可订阅的工具包。"
    if category == "design":
        return f"{name} 适合包装成中文图片/设计/素材编辑工具，优先做模板、导出、品牌物料和课程案例。"
    if "browser" in text and "automation" in text:
        return f"{name} 适合做公开网页任务助手，但必须避开账号、验证码、敏感爬取和平台规则风险。"
    if category == "agent" or "workflow" in text or "low-code" in text:
        return f"{name} 适合包装成中小企业 AI 工作流或垂直 Agent 模板库。"
    if "memory" in text:
        return f"{name} 适合做客户记忆、学习记录或客服记忆层工具。"
    return f"{name} 可作为“{direction}”方向的研究、内容和“{output}”MVP 候选。"


def project_intro(repo: dict) -> str:
    full_name = safe_text(repo.get("full_name"))
    name = safe_text(repo.get("name") or full_name.split("/")[-1])
    text = repo_text(repo)
    category = project_category(repo)

    known_intros = {
        "triggerdotdev/trigger.dev": "这是一个用来构建、部署和调度后台任务、AI Agent 与自动化工作流的平台，核心价值是把复杂任务变成可监控、可复用的执行流程。",
        "openai/openai-agents-python": "这是 OpenAI 提供的 Python 多 Agent 开发框架，用来编排多个智能体、工具调用和任务交接，适合作为 Agent 应用的底层开发框架。",
        "bytedance/deer-flow": "这是一个面向长任务研究、写代码和内容生成的开源 SuperAgent 项目，重点是用工具、记忆、技能和子智能体完成复杂任务。",
        "steel-dev/steel-browser": "这是一个给 AI Agent 使用的浏览器自动化基础设施，让智能体可以在受控浏览器环境中打开网页、读取页面并执行公开网页任务。",
        "nexu-io/open-design": "这是一个本地优先的 AI 设计工具，目标是把编码智能体变成设计引擎，用来生成网页、桌面端、移动端原型和设计素材。",
        "solacelabs/solace-agent-mesh": "这是一个事件驱动的多 Agent 编排框架，用来把不同智能体、真实业务数据和外部系统连接成可协作的 Agent 网络。",
        "zhayujie/cowagent": "这是一个开源超级 AI 助手项目，支持工具、技能、记忆和多渠道接入，适合做微信生态或轻量助手场景的 Agent 底座。",
        "langgenius/dify": "这是一个面向生产环境的 Agent 和工作流开发平台，用可视化方式搭建、测试和发布大模型应用。",
        "volcengine/openviking": "这是一个为 AI Agent 管理上下文的数据底座，用来统一保存和调用记忆、资源与技能，让 Agent 在长任务中保持上下文。",
        "enescingoz/awesome-n8n-templates": "这是一个 n8n 自动化工作流模板集合，提供大量现成的 AI Agent、RAG、消息通知和业务自动化案例。",
    }
    known = known_intros.get(full_name.lower())
    if known:
        return known

    if "browser" in text and ("automation" in text or "web agent" in text):
        return f"这是一个让 AI 操作网页或浏览器任务的开源项目，主要用于公开网页信息处理、流程自动化和 Agent 浏览器执行环境。"
    if category == "miniapp":
        return f"这是一个适合接入微信或聊天入口的 AI 助手项目，主要用于把 Agent 能力包装成个人用户和小企业能直接使用的轻量服务。"
    if category == "desktop":
        return f"这是一个桌面端 AI 工具项目，主要用于把 Agent、设计或效率能力包装成可本地运行的客户端应用。"
    if category == "skill":
        return f"这是一个围绕 Agent Skill、工具调用或工作流模板的项目，主要用于把复杂任务沉淀成可复用的技能、案例和自动化流程。"
    if category == "design":
        return f"这是一个设计或图像编辑相关的开源项目，主要用于生成、编辑或管理视觉素材和产品原型。"
    if category == "agent" and "workflow" in text:
        return f"这是一个 Agent 工作流项目，主要用于把大模型、工具调用和多步骤任务编排成可运行的业务流程。"
    if category == "agent":
        return f"这是一个 AI Agent 项目，主要用于让大模型调用工具、记忆和外部系统来完成更复杂的自动化任务。"
    if "rag" in text or "knowledge" in text:
        return f"这是一个知识库或 RAG 项目，主要用于让用户基于文档、资料和业务知识进行问答或信息整理。"
    return f"这是一个与“{USER_PROFILE['required_answers']['project_direction']}”相关的开源项目，需要结合 README 进一步确认具体用途。"


def project_meta(repo: dict) -> str:
    language = safe_text(repo.get("language")).strip() or "未标注"
    license_key = safe_text(repo.get("license_key") or repo.get("license")).strip() or "NOASSERTION"
    stars = int(repo.get("stars") or repo.get("stargazers_count") or 0)
    topics = [safe_text(topic) for topic in (repo.get("topics") or [])[:4] if safe_text(topic)]
    topic_text = "、".join(topics) if topics else "未标注"
    return f"语言/技术栈：{language}；Stars：{stars}；License：{license_key}；Topics：{topic_text}。"


def mvp_plan(repo: dict, scores: dict) -> str:
    text = repo_text(repo)
    category = project_category(repo)
    if category == "design":
        return "2 周内聚焦一个窄场景：模板列表、画布编辑、上传素材、导出 PNG/PDF、登录和付费墙；不要复刻完整 Canva/Figma。"
    if category == "miniapp":
        return "14 天内只做一个微信小程序核心场景：授权登录、一个高频 AI 任务、结果保存、订阅入口和简单后台；先验证个人或小企业是否愿意付费。"
    if category == "desktop":
        return "14 天内做桌面端最小版本：本地配置、一个核心 Agent 任务、历史记录、订阅校验和更新说明；不要先做复杂插件生态。"
    if category == "skill":
        return "14 天内做 5-10 个可复用 Skill/Agent 模板，加示例数据、运行说明、案例页和订阅入口；先卖模板和案例，再扩展平台化。"
    if "browser" in text and "automation" in text:
        return "2 周内只做公开网页低敏任务：公开资料整理、竞品价格汇总、网页摘要；不做登录、验证码、账号代操作。"
    if category == "agent" or "workflow" in text:
        return "2 周内做 3-5 个中文模板：资料问答、销售线索整理、课程内容生成、客服知识库、营销选题生成，并加登录和支付。"
    return "2 周内选择一个明确业务场景做 Web Demo，先验证用户是否愿意付费，再扩展功能。"


def monetization(repo: dict) -> str:
    text = repo_text(repo)
    category = project_category(repo)
    if category == "design":
        return "个人订阅解锁模板、高清导出和素材包；企业按品牌模板包、私有化部署和设计流程定制收费。"
    if category == "miniapp":
        return "个人用户按月订阅高频任务额度；中小企业按账号数、模板包或轻定制收费。"
    if category == "desktop":
        return "个人订阅解锁本地效率功能和模板库；企业按部署、授权席位和定制工作流收费。"
    if category == "skill":
        return "先用 Skill 模板包、课程案例和订阅制更新收费；企业侧可卖定制 Agent 工作流和内部培训。"
    if category == "agent" or "workflow" in text:
        return "个人按模板库或任务次数订阅；企业按工作流定制、部署、培训和维护收费。"
    return "优先课程案例和企业方案咨询，成熟后再做订阅或按次付费。"


def topic_ideas(repo: dict) -> list[str]:
    text = repo_text(repo)
    name = repo.get("name") or repo.get("full_name")
    category = project_category(repo)
    if category == "design":
        return [
            f"用开源项目 {name} 做一个中文设计工具 MVP",
            "2 周能不能做出一个轻量版 Canva？",
            "图像设计工具商业化时最容易踩的 License 和素材风险",
        ]
    if "browser" in text and "automation" in text:
        return [
            "AI 真的能替你操作网页吗？边界在哪里",
            "公开网页任务自动化的商业机会和风险边界",
            f"拆解 {name}：从演示爆点到可卖产品",
        ]
    if category == "miniapp":
        return [
            f"用 {name} 做一个 14 天微信小程序 AI MVP",
            "个人用户会为哪类小程序 AI 助手订阅？",
            "中小企业适合购买的小程序 Agent 场景清单",
        ]
    if category == "desktop":
        return [
            f"把 {name} 包装成桌面端 AI 工具的可行路径",
            "桌面端 Agent 工具比 Web 工具更适合哪些场景？",
            "14 天做一个可收费桌面 AI MVP 的取舍",
        ]
    if category == "skill":
        return [
            f"拆解 {name}：能不能做成可卖的 Skill 模板包？",
            "程序员博主如何用 Agent Skill 做内容和订阅产品",
            "从开源 Skill 项目到付费案例库的 14 天路径",
        ]
    return [
        f"拆解 {name}：它适合做产品还是课程案例？",
        "中小企业最愿意付费的 AI Agent 模板是什么？",
        "从开源 Agent 项目到可收费 Web 工具的 2 周路径",
    ]


def risk_notes(repo: dict, gates: list[str]) -> list[str]:
    notes = list(gates)
    license_key = repo.get("license_key") or "NOASSERTION"
    if not notes:
        notes.append(f"当前 License 为 {license_key}，仍需在商业化前复核仓库 LICENSE 文件和依赖协议。")
    return notes


def make_report_rows(projects: list[dict]) -> str:
    rows = []
    for idx, project in enumerate(projects, 1):
        repo = project["repo"]
        rows.append(
            "<tr>"
            f"<td>{idx}</td>"
            f"<td><a href=\"{escape_attr(repo['html_url'])}\">{escape(repo['full_name'])}</a></td>"
            f"<td>{escape(project['recommendation_level'])}</td>"
            f"<td data-field=\"final_score\">{project['scores']['final_score']}</td>"
            f"<td>{project['scores']['user_fit']}</td>"
            f"<td>{project['scores']['commercial_potential']}</td>"
            f"<td data-field=\"public_opinion_heat\">{project['scores']['public_opinion_heat']}</td>"
            f"<td>{escape('；'.join(project['risk_notes'][:2]))}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def make_project_cards(projects: list[dict]) -> str:
    cards = []
    for idx, project in enumerate(projects, 1):
        repo = project["repo"]
        scores = project["scores"]
        hn = project["public_opinion_signals"]["community_demand_heat"]
        gh = project["public_opinion_signals"]["github_event_heat"]
        gates = project["decision_gates"] or ["未触发硬性降级规则。"]
        topics = "".join(f"<span class=\"tag\">{escape(topic)}</span>" for topic in project["content_topics"][:3])
        cards.append(
            f"<article class=\"card\" data-repo=\"{escape_attr(repo['full_name'])}\">"
            f"<h3><span class=\"rank\">{idx}</span> "
            f"<a class=\"repo-title\" href=\"{escape_attr(repo['html_url'])}\" target=\"_blank\" rel=\"noopener noreferrer\">"
            f"{escape(repo['full_name'])}</a></h3>"
            f"<p><strong>项目简介：</strong>{escape(project['project_intro'])}</p>"
            f"<p class=\"meta-line\"><strong>基础信息：</strong>{escape(project['project_meta'])}</p>"
            f"<p><strong>商业化判断：</strong>{escape(project['summary'])}</p>"
            f"<p><strong>最终分：</strong><span class=\"score\" data-field=\"final_score\">{scores['final_score']}</span> ｜ "
            f"<strong>舆情热度：</strong><span class=\"score\" data-field=\"public_opinion_heat\">{scores['public_opinion_heat']}</span></p>"
            f"<p><strong>GitHub 事件热度：</strong><span data-field=\"github_event_heat\">{scores['github_event_heat']}</span>；"
            f"<strong>社区需求热度：</strong><span data-field=\"community_demand_heat\">{scores['community_demand_heat']}</span></p>"
            f"<p><strong>近期热度与需求信号：</strong>{escape(gh['trend_summary'])} {escape(hn['discussion_summary'])}</p>"
            f"<p><strong>决策理由：</strong>{escape(project['decision_reason'])}</p>"
            f"<p><strong>MVP 计划：</strong>{escape(project['mvp_plan'])}</p>"
            f"<p><strong>变现路径：</strong>{escape(project['monetization'])}</p>"
            f"<p><strong>内容选题：</strong>{topics}</p>"
            f"<p class=\"risk\"><strong>降级/数据缺口：</strong>{escape('；'.join(gates))}</p>"
            "</article>"
        )
    return "\n".join(cards)


def escape(value: object) -> str:
    return html.escape(safe_text(value), quote=False)


def escape_attr(value: object) -> str:
    return html.escape(safe_text(value), quote=True)


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_report(projects: list[dict], data_gaps: list[str]) -> None:
    template = (ROOT / "templates" / "daily-html-report.html").read_text(encoding="utf-8")
    profile = USER_PROFILE["required_answers"]
    direction_label = profile["project_direction"]
    user_profile_summary = (
        f"使用者是{profile['skill_user_identity']}，目标是{profile['skill_user_goal']}；"
        f"方向为{profile['project_direction']}，面向{profile['target_user']}，"
        f"产出为{profile['target_output']}，MVP 时间预算为{profile['mvp_time_budget']}，"
        f"变现偏好是{profile['payment_goal']}。风险边界：{profile['risk_boundary']}。"
    )
    executive_summary = (
        "本报告按最终决策规则重跑：用户匹配 20%、商业潜力 20%、MVP 可行性 15%、"
        "内容传播价值 15%、风险可控 15%、舆情与需求热度 15%。"
        "GH Archive 和 HN Algolia 均进入最终分，HN 命中先做相关性过滤。"
    )
    public_opinion_summary = (
        "舆情热度 = GH Archive 近期 GitHub 事件热度 50% + HN Algolia 社区需求热度 50%。"
        "HN 只统计有效相关命中，被排除的同名或泛词噪声不进入热度分。"
        + (" 数据缺口：" + "；".join(sorted(set(data_gaps))) if data_gaps else "")
    )
    assumptions = "；".join(USER_PROFILE["assumptions"])
    data_sources = (
        "GitHub REST Search API：已启用；GitHub Repo API：已启用；"
        "GH Archive：本次交互执行采用 Repo API 低置信度估算，可用 --full-gh-archive 执行小时归档深扫；"
        "Hacker News Algolia API：已启用并过滤相关性。"
    )
    replacements = {
        "{{report_title}}": f"{direction_label} GitHub 商业化机会日报",
        "{{generated_at}}": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "{{user_profile_summary}}": user_profile_summary,
        "{{executive_summary}}": executive_summary,
        "{{project_ranking_rows}}": make_report_rows(projects),
        "{{project_cards}}": make_project_cards(projects),
        "{{public_opinion_summary}}": public_opinion_summary,
        "{{assumptions}}": assumptions,
        "{{data_sources}}": data_sources,
    }
    html_text = template
    for key, value in replacements.items():
        html_text = html_text.replace(key, value)
    REPORT_PATH.write_text(html_text, encoding="utf-8")


def validate_report() -> list[str]:
    text = REPORT_PATH.read_text(encoding="utf-8")
    problems = []
    required = ["<meta charset=\"utf-8\">", "最终分", "舆情热度", "github_event_heat", "community_demand_heat"]
    for marker in required:
        if marker not in text:
            problems.append(f"报告缺少 {marker}")
    for marker in ["????", "锟斤拷", "���", "鎴", "涓"]:
        if marker in text:
            problems.append(f"报告疑似乱码：{marker}")
    for marker in ["<script", "rel=\"stylesheet\"", "rel='stylesheet'", "@import", "cdn."]:
        if marker in text:
            problems.append(f"报告包含外部或脚本依赖：{marker}")
    return problems


def main() -> None:
    global USER_PROFILE, DISCOVERY_TASK

    USER_PROFILE = load_user_profile_or_exit()
    DISCOVERY_TASK = build_discovery_task(USER_PROFILE)

    write_json(CONFIG_DIR / "data-source-config.json", DATA_SOURCE_CONFIG)
    write_json(PROCESSED_DIR / "fresh-user-profile.json", USER_PROFILE)
    write_json(PROCESSED_DIR / "fresh-discovery-task.json", DISCOVERY_TASK)

    cache_slug = task_cache_slug(DISCOVERY_TASK)
    candidates_path = RAW_DIR / f"fresh-candidates-{cache_slug}.json"
    enriched_path = PROCESSED_DIR / f"fresh-shortlist-enriched-{cache_slug}.json"
    if candidates_path.exists() and "--force" not in sys.argv:
        candidates = json.loads(candidates_path.read_text(encoding="utf-8"))
    else:
        candidates = search_candidates()
    write_json(candidates_path, candidates)
    if enriched_path.exists() and "--force" not in sys.argv:
        enriched = json.loads(enriched_path.read_text(encoding="utf-8"))
    else:
        short = shortlist(candidates)
        enriched = [enrich_repo(repo) for repo in short]
    write_json(enriched_path, enriched)

    analysis_repos = enriched[:10]
    gh_signals = scan_gh_archive(analysis_repos, hours=3)
    projects = []
    data_gaps = []
    for repo in analysis_repos:
        print(f"Analyzing {repo.get('full_name')}...", flush=True)
        hn_signal = collect_hn(repo)
        gh_signal = gh_signals.get(repo["full_name"]) or {
            "score": repo_api_heat_score(repo),
            "trend_summary": "GH Archive 未返回数据，使用 Repo API 估算。",
            "confidence": "low",
            "data_gaps": ["GH Archive 未返回数据。"],
        }
        data_gaps.extend(gh_signal.get("data_gaps") or [])
        scores = score_repo(repo)
        public_opinion_heat = round((float(gh_signal["score"]) + float(hn_signal["score"])) / 2.0, 1)
        scores.update(
            {
                "public_opinion_heat": public_opinion_heat,
                "github_event_heat": round(float(gh_signal["score"]), 1),
                "community_demand_heat": round(float(hn_signal["score"]), 1),
            }
        )
        final_score = round(
            scores["user_fit"] * 0.20
            + scores["commercial_potential"] * 0.20
            + scores["mvp_feasibility"] * 0.15
            + scores["content_virality"] * 0.15
            + scores["risk_control"] * 0.15
            + scores["public_opinion_heat"] * 0.15,
            1,
        )
        scores["final_score"] = final_score
        base_level = recommendation_level(final_score)
        level, gates, max_rank = apply_decision_gates(repo, scores, final_score, base_level)
        project = {
            "repo": {
                "full_name": repo.get("full_name"),
                "html_url": repo.get("html_url"),
                "description": repo.get("description"),
                "stars": repo.get("stars"),
                "forks": repo.get("forks"),
                "language": repo.get("language"),
                "topics": repo.get("topics") or [],
                "license": repo.get("license_key"),
                "pushed_at": repo.get("pushed_at"),
                "homepage": repo.get("homepage"),
            },
            "recommendation_level": level,
            "rank_gate_max_rank": max_rank,
            "scores": scores,
            "project_intro": project_intro(repo),
            "project_meta": project_meta(repo),
            "summary": product_direction(repo),
            "decision_reason": (
                f"匹配本轮方向：{USER_PROFILE['required_answers']['project_direction']}，相关度 {scores['user_fit']}；"
                f"商业潜力 {scores['commercial_potential']}；"
                f"MVP 可行性 {scores['mvp_feasibility']}；风险可控 {scores['risk_control']}；"
                f"舆情热度 {scores['public_opinion_heat']}。"
            ),
            "decision_gates": gates,
            "public_opinion_signals": {
                "github_event_heat": gh_signal,
                "community_demand_heat": hn_signal,
                "public_opinion_heat_score": public_opinion_heat,
                "data_gaps": gh_signal.get("data_gaps") or [],
            },
            "mvp_plan": mvp_plan(repo, scores),
            "monetization": monetization(repo),
            "content_topics": topic_ideas(repo),
            "risk_notes": risk_notes(repo, gates),
        }
        projects.append(project)

    projects.sort(key=lambda item: (item["scores"]["final_score"], item["scores"]["risk_control"]), reverse=True)
    top3_locked = []
    others = []
    for item in projects:
        if item["rank_gate_max_rank"] <= 3:
            others.append(item)
        else:
            if len(top3_locked) < 3:
                top3_locked.append(item)
            else:
                others.append(item)
    final_projects = (top3_locked + others)[: DISCOVERY_TASK["final_report_limit"]]
    write_json(PROCESSED_DIR / "fresh-commercial-analysis.json", final_projects)
    generate_report(final_projects, data_gaps)
    problems = validate_report()
    if problems:
        raise SystemExit("\n".join(problems))
    print(json.dumps({
        "candidates": len(candidates),
        "shortlist": len(enriched),
        "final_projects": len(final_projects),
        "report": str(REPORT_PATH),
        "top_projects": [item["repo"]["full_name"] for item in final_projects[:5]],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
