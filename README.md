# GitHub Commercial Analysis Skill

一个用于筛选 GitHub 开源项目商业化机会的 Codex Skill。它会基于用户画像、项目数据、舆情热度、MVP 可行性和风险规则，生成可直接打开的单文件 HTML 项目机会日报。

默认输出文件：

```text
github-opportunity-daily-report.html
```

## 适合谁使用

- 程序员、独立开发者、博主、自媒体创作者
- 想从 GitHub 找可复刻、可包装、可做内容、可商业化验证项目的人
- 想每天自动发现 Agent、AI 工具、SaaS、小程序、桌面工具等机会的人
- 想把开源项目转成 MVP、课程案例、订阅产品或企业定制方案的人

## 核心能力

- 搜索 GitHub 候选项目
- 获取 Repo、README、Release、License、Topics 等项目详情
- 用 GH Archive 判断近期 GitHub 行为热度
- 用 Hacker News Algolia 判断海外技术社区讨论和需求信号
- 按明确公式生成最终 10 个推荐项目
- 输出手机友好的 HTML 卡片报告
- 对 License、法律、隐私、侵权、灰产等风险做硬性降级

## 数据源

本 Skill 默认使用 4 个数据源：

| 数据源 | 用途 | 配置方式 |
| --- | --- | --- |
| GitHub REST Search API | 搜索候选项目 | 推荐使用 GitHub CLI 登录 |
| GitHub Repo API | 获取 README、License、Release、Topics、项目详情 | 推荐使用 GitHub CLI 登录 |
| GH Archive | 判断近期 GitHub 事件热度 | 公共 endpoint，无需 token |
| Hacker News Algolia API | 判断海外技术社区讨论和需求热度 | 公共 endpoint，无需 token |

GitHub 登录：

```powershell
gh auth login --web
gh auth status
```

## 一键安装

### 推荐：npx 安装

不需要手动 clone 仓库，直接运行：

```bash
npx --yes github:Shark-Overlord/github-commercial-analysis-skill
```

这个命令会把 Skill 安装到：

```text
~/.codex/skills/github-commercial-analysis-skill
```

如果以后发布到 npm，命令可以进一步缩短为：

```bash
npx github-commercial-analysis-skill
```

### Windows PowerShell 备用方式

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/Shark-Overlord/github-commercial-analysis-skill/main/install.ps1 | iex"
```

### macOS / Linux 备用方式

```bash
curl -fsSL https://raw.githubusercontent.com/Shark-Overlord/github-commercial-analysis-skill/main/install.sh | bash
```

安装后在 Codex 中这样调用：

```text
Use $github-commercial-analysis-skill to find GitHub projects that I can turn into a paid MVP and generate an HTML report.
```

## 手动安装

安装到 Codex skills 目录：

```powershell
cd $env:USERPROFILE\.codex\skills
git clone https://github.com/Shark-Overlord/github-commercial-analysis-skill.git
```

作为普通项目运行：

```powershell
git clone https://github.com/Shark-Overlord/github-commercial-analysis-skill.git
cd github-commercial-analysis-skill
```

可选依赖：

```powershell
D:\anaconda3\python.exe -m pip install requests
```

如果你的 Python 不在 `D:\anaconda3\python.exe`，换成自己的 Python 3 路径即可。

## 配置用户画像

运行脚本前，需要创建：

```text
data/config/current-user-profile.json
```

示例：

```json
{
  "required_answers": {
    "skill_user_identity": "程序员 + 博主",
    "skill_user_goal": "通过 Skill 找到适合自己做产品和内容的项目机会",
    "project_direction": "Agent、微信小程序、Skill 相关内容",
    "target_user": "个人用户或中小企业",
    "target_output": "桌面端和微信小程序",
    "mvp_time_budget": "14 天",
    "payment_goal": "订阅制",
    "technical_level": "本身是程序员，技术能力较强",
    "risk_boundary": "所有和法律相关的都不要碰"
  },
  "risk_preference": "conservative"
}
```

如果没有这个文件，脚本会停止并输出 9 个必答问题，不会直接进入 GitHub 搜索。

## 运行

```powershell
$env:PYTHONUTF8='1'
D:\anaconda3\python.exe .\scripts\run_daily_analysis.py --force
```

生成的 HTML 报告会写到当前目录的上一级工作区中：

```text
github-opportunity-daily-report.html
```

如果你把 Skill 放在独立目录中运行，也可以根据脚本输出中的 `report` 字段找到报告路径。

## 检索流程简版

1. 配置 4 个数据源：GitHub Search、GitHub Repo、GH Archive、HN Algolia。
2. 询问用户画像必答问题：用户是谁、目的是什么、方向是什么、卖给谁、做成什么、多久做 MVP、怎么收费、技术能力、风险边界。
3. 根据画像生成搜索关键词、排除词、语言、时间窗口和候选数量。
4. 采集候选项目并补全 README、License、Release、Topics、热度和社区讨论。
5. 按项目价值、用户匹配、商业潜力、MVP 可行性、内容传播、风险和舆情热度评分。
6. 应用硬性降级规则，输出最终 10 个项目。
7. 生成单文件 HTML 日报。

## 最终评分公式

| 维度 | 权重 |
| --- | ---: |
| 用户匹配 | 20% |
| 商业潜力 | 20% |
| MVP 可行性 | 15% |
| 内容传播价值 | 15% |
| 风险可控 | 15% |
| 舆情与需求热度 | 15% |

硬性规则优先于分数：

- License 高风险或不明确：最高只能谨慎推荐
- 法律、隐私、侵权、灰产风险：不得进入商业推荐
- 用户时间预算内不可落地：不得进入前 3
- 不符合用户画像：不得高推荐
- GH Archive 或 HN Algolia 不可用：舆情分降权，并在报告中标注数据缺口

## 验证闭环

运行校验脚本：

```powershell
$env:PYTHONUTF8='1'
D:\anaconda3\python.exe .\scripts\validate_skill_package.py
```

报告生成后至少检查：

- `SKILL.md` frontmatter 只有 `name` 和 `description`
- `SKILL.md` 引用文件全部存在
- JSON schema 能 UTF-8 读取并解析
- HTML 包含 `<meta charset="utf-8">`
- HTML 无 `????`、`锟斤拷`、`���` 等乱码
- HTML 无外部 CSS、JS、CDN 依赖
- 移动端使用按顺序排列的项目卡片，不依赖表格
- 每张卡片标题能点击跳转到 GitHub 仓库
- 每张卡片包含中文项目简介、基础信息、商业化判断、最终分和舆情分
- 风险降级、数据缺口和 License 问题必须显示在报告中

## 目录结构

```text
github-commercial-analysis-skill/
├── SKILL.md
├── README.md
├── agents/
├── sop/
├── strategies/
├── criteria/
├── schemas/
├── tools/
├── templates/
├── prompts/
├── assets/
├── examples/
└── scripts/
```

## 不会上传的本地文件

`.gitignore` 默认排除：

- `data/`：用户画像、采集缓存、分析结果
- `github-opportunity-daily-report.html`：生成的日报
- `__pycache__/` 和 Python 缓存
- `.env` 等本地配置

## 免责声明

本 Skill 只用于商业化机会初筛，不构成法律、投资、财务或合规意见。对开源许可证和风险的判断只是初步筛查，正式商业化前仍需要人工复核。
