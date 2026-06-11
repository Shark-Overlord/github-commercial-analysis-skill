# 04 脚本与 API 数据采集

## 目标

从 4 个已配置 API 数据源获取候选项目和补充信号，形成可被后续分析使用的结构化数据。

## 必读资源

- `tools/github-search-api-guide.md`
- `tools/github-repo-api-guide.md`
- `tools/gh-archive-guide.md`
- `tools/hacker-news-algolia-guide.md`
- `schemas/project-info-schema.json`
- `schemas/data-source-result-schema.json`

## 执行步骤

1. 使用 GitHub REST Search API 根据关键词、Topics、Star 和更新时间获取候选仓库。
2. 使用 GitHub Repo API 补充 README、License、Release、Topics、语言、Star、Fork、Issue、最近提交等信息。
3. 对短名单候选补充 GH Archive 事件热度信息，形成 `github_event_heat`。
4. 查询 Hacker News Algolia API，判断海外技术社区讨论度，形成 `community_demand_heat`。
5. 记录采集失败、限流、缺失字段和重试结果。

## 舆情数据输出

GH Archive 和 Hacker News Algolia API 采集结果属于舆情数据，不得只作为备注。后续最终排序必须使用它们计算 `public_opinion_heat`。

GH Archive 至少输出：

- 事件时间窗口；
- Star、Fork、Issue、PR、Watch 事件数量；
- 事件总数；
- 近期热度摘要；
- `github_event_heat` 分数；
- 置信度和数据缺口。

Hacker News Algolia API 至少输出：

- HN 原始命中数量；
- 有效命中数量和被排除噪声数量；
- 相关讨论的点赞数和评论数；
- 代表性讨论标题；
- 命中相关性说明；
- 正向需求信号；
- 负向或争议信号；
- `community_demand_heat` 分数；
- 置信度和数据缺口。

## 建议输出

- `data/raw/candidate-projects.json`
- `data/processed/enriched-projects.json`

## 质检

- 不用项目名称直接推断用途，必须保留 README 或项目描述证据。
- API 失败时要记录失败原因，不得静默丢弃。
- 输出字段应尽量符合 `project-info-schema.json`。
- GH Archive 或 HN Algolia 不可用时，必须标注舆情数据缺口，并降低 `public_opinion_heat` 置信度。
