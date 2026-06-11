# 01 数据源配置

## 目标

在用户画像和项目搜索之前，先帮助用户配置本 Skill 必需的 4 个 API 数据源。执行者必须告诉用户去哪里配置、需要复制什么配置给执行者，或在本地直接打开浏览器完成授权。

## 必读资源

- `strategies/data-source-strategy.md`
- `schemas/data-source-config-schema.json`
- `assets/data-source-map.md`
- `tools/api-setup-guide.md`

## 必须确认的问题

- 是否允许联网访问 4 个 API 数据源：GitHub REST Search API、GitHub Repo API、GH Archive、Hacker News Algolia API。
- GitHub 授权采用哪种方式：浏览器授权、用户复制配置、环境变量或匿名低频访问。
- GH Archive 使用哪种公开访问方式：小时归档 HTTP 下载或 BigQuery。
- Hacker News Algolia API 使用哪个 endpoint 和查询方式。
- 是否需要保存原始采集结果到本地 `data/` 目录。
- 是否有不能访问或不能使用的数据源。

## 必需配置的数据源

1. GitHub REST Search API：用于搜索候选项目。
2. GitHub Repo API：用于获取项目详情、README、Release、License 和 Topics。
3. GH Archive：用于判断近期 GitHub 事件热度。
4. Hacker News Algolia API：用于判断项目是否有海外技术社区讨论。

这 4 个数据源都必须先完成配置记录。某个 API 当前不可用时，不能跳过配置阶段，而是要记录为 `degraded` 或 `disabled`，并说明对后续分析的影响。

## 用户配置方式

### 方式 A：打开浏览器授权

优先用于 GitHub API。执行者可以引导用户通过 GitHub CLI 或 GitHub Token 创建页完成授权：

- GitHub CLI：运行 `gh auth login --web`，让用户在浏览器中完成授权。
- GitHub Fine-grained token：打开 `https://github.com/settings/personal-access-tokens/new`，让用户创建只读 Token。

授权完成后，执行者只记录凭据来源，例如 `GitHub CLI`、`GITHUB_TOKEN` 环境变量或“用户已在本地配置”。不要把真实 Token 写入报告。

### 方式 B：用户复制配置粘贴给执行者

当用户不方便浏览器授权时，执行者给用户一段配置模板，让用户填写后粘贴回来。模板中不要要求用户把 Token 明文放进最终报告；如必须临时提供 Token，只能用于本次执行，不能写入文件、日志或 HTML 报告。

推荐粘贴模板：

```yaml
github_rest_search_api:
  status: enabled
  auth_method: github_cli | env:GITHUB_TOKEN | pasted_token | anonymous
  api_base_url: https://api.github.com
  search_endpoint: /search/repositories

github_repo_api:
  status: enabled
  auth_method: github_cli | env:GITHUB_TOKEN | pasted_token | anonymous
  api_base_url: https://api.github.com
  repo_endpoint: /repos/{owner}/{repo}
  readme_endpoint: /repos/{owner}/{repo}/readme

gh_archive:
  status: enabled
  access_method: hourly_archive_http | bigquery
  archive_url_template: https://data.gharchive.org/{yyyy-mm-dd-H}.json.gz
  event_window_days: 7

hacker_news_algolia_api:
  status: enabled
  api_base_url: https://hn.algolia.com/api/v1
  search_endpoint: /search
  search_by_date_endpoint: /search_by_date
```

## 执行步骤

1. 读取 `tools/api-setup-guide.md` 和 `assets/data-source-map.md`，向用户说明 4 个 API 的配置入口。
2. 优先尝试浏览器授权路径：GitHub 使用 `gh auth login --web` 或 GitHub Token 创建页；公共 API 配置 endpoint。
3. 如果用户选择复制粘贴配置，提供上面的 YAML 模板，并要求用户只提供配置方式和 endpoint，避免把 Token 写进报告。
4. 检查本地环境是否已有 GitHub CLI、`GITHUB_TOKEN` 环境变量或可用 Token。
5. 生成数据源配置对象，字段参考 `schemas/data-source-config-schema.json`。
6. 对不可用 API 设置 `status=disabled` 或 `status=degraded`，并写明降级策略。
7. 将 4 个 API 的配置状态写入最终 HTML 报告的“数据来源和默认假设”模块。

## 输出

输出一份数据源配置摘要，至少包含：

- 数据源名称
- 启用状态
- API 地址或访问方式
- 用户配置入口
- 授权或复制粘贴方式
- 是否需要认证
- 可采集内容
- 降级方案
- 对报告可信度的影响

## 质检

- 不得在未确认数据源的情况下直接进入用户画像和项目搜索。
- 不得在报告中暴露 Token、Cookie 或其他敏感凭据。
- 数据源配置摘要必须包含 4 个 API 数据源，不能新增“项目官网、Demo、竞品网站”等独立数据源。
- 必须告诉用户每个 API 去哪里配置，不能只写“请配置 API”。
- 数据源不可用时必须说明影响，不能假装已采集。
