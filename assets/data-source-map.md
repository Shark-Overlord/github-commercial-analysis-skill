# 数据源地图

| 数据源 | 用户去哪里配置 | 推荐配置方式 | 主要用途 | 需要用户粘贴什么 | 降级方案 |
| --- | --- | --- | --- | --- | --- |
| GitHub REST Search API | GitHub CLI 浏览器授权，或 `https://github.com/settings/personal-access-tokens/new` | `gh auth login --web` 或 Fine-grained PAT | 按关键词、Star、更新时间搜索候选项目 | `auth_method`、`api_base_url=https://api.github.com`、`search_endpoint=/search/repositories`；不要把 Token 写入报告 | 缩小关键词范围、降低候选数量或匿名低频访问 |
| GitHub Repo API | 同 GitHub REST Search API，共用 GitHub 授权 | `gh auth login --web` 或 Fine-grained PAT | 获取项目详情、README、Release、License、Topics | `auth_method`、`repo_endpoint=/repos/{owner}/{repo}`、`readme_endpoint=/repos/{owner}/{repo}/readme` | 使用已采集仓库信息降级分析，并标注字段缺口 |
| GH Archive | `https://www.gharchive.org/` 或 BigQuery 公共数据集 | 配置 HTTP 小时归档 URL 模板或 BigQuery 访问方式 | 判断近期 GitHub 事件热度，进入 `github_event_heat` 舆情分 | `access_method`、`archive_url_template=https://data.gharchive.org/{yyyy-mm-dd-H}.json.gz`、`event_window_days` | 改用 Repo API 的更新时间、Issue、Release 和 Star 信息，并降低舆情分置信度 |
| Hacker News Algolia API | `https://hn.algolia.com/api` | 配置公共 API endpoint | 判断项目是否有海外技术社区讨论，进入 `community_demand_heat` 需求热度分 | `api_base_url=https://hn.algolia.com/api/v1`、`search_endpoint=/search`、`search_by_date_endpoint=/search_by_date` | 标注海外社区讨论证据不足，并降低舆情分置信度 |

## 默认组合

- 单项目：GitHub Repo API。
- 批量日报：GitHub REST Search API + GitHub Repo API。
- 热度分析：GH Archive。
- 海外讨论分析：Hacker News Algolia API。
- 风险分析：GitHub Repo API 中的 License、README 限制说明和依赖来源。

## 舆情数据用途

GH Archive 和 Hacker News Algolia API 的结果必须进入最终 `public_opinion_heat` 评分。它们不只是报告参考信息，而是最终 10 个项目排序的一部分。

## 配置要求

分析开始前必须先输出 4 个 API 数据源的配置摘要，说明每个 API 的启用状态、认证方式、访问方式、降级策略以及对报告可信度的影响。
