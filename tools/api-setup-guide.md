# API 配置向导

## 目标

执行 Skill 的第一步必须帮助用户完成 4 个 API 数据源配置。不要只说“请配置 API”，而要明确告诉用户去哪里配置、打开哪个页面或运行哪个命令、复制什么配置给执行者。

## 首选路径：打开浏览器授权

### GitHub REST Search API 和 GitHub Repo API

这两个 API 共用 GitHub REST API 认证。

推荐方式：

```powershell
gh auth login --web
```

执行者运行该命令后，让用户在浏览器中完成 GitHub 授权。授权完成后，配置摘要中写：

```yaml
auth_method: github_cli
credential_source: GitHub CLI
```

备选方式：打开 GitHub Fine-grained personal access token 创建页：

```plain
https://github.com/settings/personal-access-tokens/new
```

建议用户创建只读 Token，优先选择最小权限。用于公开仓库分析时，不要申请写权限。Token 只用于本地请求，不得写入报告。

### GH Archive

GH Archive 默认不需要用户 Token。配置的是访问方式：

```plain
https://www.gharchive.org/
https://data.gharchive.org/{yyyy-mm-dd-H}.json.gz
```

如果用户有 BigQuery 环境，也可以配置 BigQuery 公共数据集访问方式。

### Hacker News Algolia API

Hacker News Algolia API 默认不需要用户 Token。配置公共 endpoint：

```plain
https://hn.algolia.com/api
https://hn.algolia.com/api/v1/search
https://hn.algolia.com/api/v1/search_by_date
```

## 备选路径：用户复制配置粘贴给执行者

如果浏览器授权不方便，给用户下面模板，让用户粘贴回来：

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
  releases_endpoint: /repos/{owner}/{repo}/releases
  topics_endpoint: /repos/{owner}/{repo}/topics

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

## 安全规则

- 优先让用户通过浏览器授权或本地环境变量配置 Token。
- 如果用户粘贴 Token，只能用于本次执行，不得写入 Markdown、JSON、HTML、日志或最终报告。
- 报告中只写 `credential_source`，例如 `GitHub CLI` 或 `env:GITHUB_TOKEN`。
- 不要求 GH Archive 或 HN Algolia 提供 Token；它们配置 endpoint 和访问方式即可。
