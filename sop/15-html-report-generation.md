# 15 HTML 日报生成

## 目标

把用户画像、项目分析、排序、MVP、变现、传播和风险结果整合成单文件 HTML 日报。

## 必读资源

- `schemas/html-report-schema.json`
- `criteria/final-decision-criteria.md`
- `templates/daily-html-report.html`
- `templates/single-project-html-report.html`
- `templates/project-comparison-html-report.html`
- `templates/content-topic-html-report.html`
- `prompts/html-generation-prompt.md`

## 输出要求

- 默认文件名：`github-opportunity-daily-report.html`
- 单文件可打开
- 文件必须使用 UTF-8 编码保存，避免中文乱码
- `<head>` 中必须包含 `<meta charset="utf-8">`
- 内联 CSS
- 不默认依赖外部 CDN
- 适合浏览器阅读
- 手机优先阅读，移动端以项目卡片为主
- 适合归档保存
- 适合截图传播
- 适合后续转 PDF

## 报告模块

- 报告标题和生成日期
- 用户画像摘要
- 今日结论
- 项目机会卡片，卡片展示顺序就是最终推荐排序
- 项目简介，用简明中文说明仓库本身是干什么的、解决什么问题、主要适用场景
- 基础信息，单独展示语言/技术栈、Stars、License 和核心 topics
- 商业化判断，说明该项目为什么适合当前用户包装、复刻、做内容或变现
- MVP 建议
- 变现路径
- 内容传播建议
- 风险提示
- 数据来源和默认假设
- 最终分和推荐等级
- 舆情与需求热度
- GH Archive 近期 GitHub 事件热度
- Hacker News Algolia 社区需求热度
- 硬性降级规则和数据缺口

## 质检

- 不得只输出 Markdown 摘要。
- 所有推荐等级、分数和风险必须能从前面分析中追溯。
- 最终排序必须使用 `criteria/final-decision-criteria.md` 的公式。
- 报告必须展示 `final_score`、`public_opinion_heat`、`github_event_heat`、`community_demand_heat`。
- 每张项目卡片的标题必须是可点击链接，点击后跳转到对应 GitHub 仓库地址。
- 每张项目卡片必须先展示“项目简介”，再展示“基础信息”和“商业化判断”；不得只给推荐理由而不解释项目本身是什么。
- “项目简介”必须是中文自然语言说明，不得直接粘贴英文 README/description，也不得把语言、Stars、License、Topics 堆在简介里。
- 移动端可以不展示排行表；不得为了表格牺牲手机阅读体验。
- 如果存在排行表，只能作为桌面端辅助信息；项目卡片必须按最终排序从高到低排列。
- 若 GH Archive 或 HN Algolia 不可用，必须在项目卡片和数据来源模块标注数据缺口。
- HTML 中不放远程字体、远程脚本或默认外部 CSS。
- 生成文件后必须重新用 UTF-8 读取一次，检查中文是否正常显示。
- 如果在 Windows PowerShell 中写 HTML，必须显式使用 `-Encoding UTF8`，不要依赖默认编码。
- 如果使用 Python 写 HTML，必须使用 `write_text(..., encoding="utf-8")` 或等效写法。
- 不允许出现 `锟斤拷`、`���`、`鎴`、`涓`、`乱码` 等疑似编码损坏字符。
- 不允许出现大量连续问号，例如 `????`；这通常说明中文在生成阶段已经被系统编码替换，单纯加 UTF-8 meta 无法修复。
- 在 Windows PowerShell 中，不要通过管道或 here-string 传递包含大量中文的 Python/Node 脚本来生成 HTML；应使用 UTF-8 源文件、模板文件或明确 `encoding="utf-8"` 的写入脚本。
- 如果报告正文预期包含中文，生成后应统计中文字符数量；如果中文段落大面积变成问号，必须重新生成报告。
