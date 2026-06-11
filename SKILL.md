---
name: github-commercial-analysis-skill
description: 分析 GitHub 开源项目的商业化包装价值、用户匹配度、MVP 可行性、内容传播价值、舆情热度和风险等级，并生成可直接打开的单文件 HTML 项目机会日报。适用于筛选 GitHub 项目机会、分析开源项目商业化价值、制定中文市场包装策略、输出 MVP 计划、内容选题或每日项目机会报告。
---

# GitHub 商业化分析 Skill

## 何时使用

当用户想从 GitHub 开源项目中寻找可包装、可复刻、可传播、可商业化验证的项目机会时使用本 Skill。默认最终产物是 `github-opportunity-daily-report.html` 单文件 HTML 日报。

## 执行原则

- 先确认数据源，再建立用户画像，不得跳过必达问题直接搜索。
- 不假设用户是程序员；必须先识别当前使用者身份、目的、目标用户、产品形态、时间预算、收费方式、技术能力和风险边界。
- 当用户要求重新开始、重新测试或忘记旧画像时，必须重新询问第 2 步必达问题，不得复用旧画像、旧日报或旧缓存结论。
- 最终 10 个项目必须按 `criteria/final-decision-criteria.md` 的评分公式排序，并应用硬性降级规则。
- GH Archive 与 Hacker News Algolia 属于舆情数据源，必须进入最终评分，不只是备注。
- 高风险项目只输出风险说明，不输出具体复刻路线。
- HTML 必须 UTF-8、单文件、内联 CSS、无默认 CDN 依赖、手机端以排序卡片为主。

## 检索流程

1. **配置数据源**：读取 `sop/01-data-source-configuration.md`、`strategies/data-source-strategy.md`、`tools/api-setup-guide.md`。确认 GitHub CLI 或 API 访问可用，并检查 GH Archive、Hacker News Algolia endpoint。
2. **建立用户画像**：读取 `sop/02-user-communication-and-profile.md`、`schemas/user-profile-schema.json`。必达问题缺失时停止流程并补问。
3. **生成搜索任务**：读取 `sop/03-discovery-task-planning.md`、`strategies/search-strategy.md`、`schemas/discovery-task-schema.json`。根据画像生成关键词、排除词、语言、时间窗口和 shortlist 数量。
4. **采集候选项目**：读取 `sop/04-script-data-collection.md` 与 `tools/` 下的数据源指南。默认可运行 `scripts/run_daily_analysis.py` 采集 GitHub Search、Repo 详情、README、License、Release、Topics、GH 热度和 HN 讨论。
5. **筛选和补全**：读取 `sop/05-candidate-project-filtering.md`、`sop/06-project-info-enrichment.md`。过滤无 README、低维护、风险高、License 不适合或不匹配画像的项目。
6. **理解和评分**：读取 `sop/07-project-understanding.md` 到 `sop/14-risk-analysis.md`，并按用户匹配、商业潜力、MVP 可行性、内容传播、风险可控、舆情热度评分。
7. **生成报告**：读取 `sop/15-html-report-generation.md`、`criteria/final-decision-criteria.md`、`templates/daily-html-report.html`、`schemas/html-report-schema.json`，输出最终 HTML。

## 最终评分

最终分使用 `criteria/final-decision-criteria.md`：

- 用户匹配：20%
- 商业潜力：20%
- MVP 可行性：15%
- 内容传播价值：15%
- 风险可控：15%
- 舆情与需求热度：15%

硬性规则优先于分数：License 高风险或不明确、法律/隐私/侵权/灰产风险、2 周内不可落地、用户画像不匹配、舆情数据缺失等情况必须影响推荐等级。

## 报告要求

HTML 项目卡片必须包含：

- 可点击跳转到 GitHub 仓库的项目标题
- 简明中文项目简介
- 基础信息：语言/技术栈、Stars、License、Topics
- 商业化判断
- 最终分、推荐等级、舆情热度、GitHub 事件热度、社区需求热度
- 决策理由、MVP 计划、变现路径、内容选题
- 降级原因、风险提示和数据缺口

## 验证闭环

生成报告后必须完成以下检查：

1. `SKILL.md` frontmatter 只包含 `name` 和 `description`。
2. `SKILL.md` 中引用的资源文件真实存在。
3. 所有 JSON schema 能用 UTF-8 读取并解析。
4. HTML 包含 `<meta charset="utf-8">`，无 `????`、`锟斤拷`、`���` 等乱码。
5. HTML 不依赖外部 CSS、JS 或 CDN。
6. 移动端不强依赖表格，项目卡片按最终排序展示。
7. 每张卡片标题可点击，链接到对应 GitHub 仓库。
8. 每张卡片包含中文项目简介、基础信息、商业化判断、最终分和舆情分。
9. 高风险、License 不明确、数据源缺失的项目在报告中明确标注并降级。

可优先运行：

```powershell
$env:PYTHONUTF8='1'
D:\anaconda3\python.exe .\scripts\validate_skill_package.py
D:\anaconda3\python.exe .\scripts\run_daily_analysis.py --force
```

## 资源导航

- `sop/`：15 步执行流程
- `criteria/`：评分、MVP、License、最终决策标准
- `strategies/`：用户画像、搜索、筛选、包装、变现、传播、风险策略
- `schemas/`：用户画像、采集任务、项目详情、数据源结果、HTML 报告结构
- `tools/`：GitHub Search、Repo、GH Archive、HN Algolia 使用指南
- `templates/`：单文件 HTML 报告模板
- `scripts/`：自动采集、报告生成和基础校验脚本
