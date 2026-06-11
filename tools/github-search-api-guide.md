# GitHub REST Search API 使用说明

## 用途

用于根据关键词、Topics、语言、Star 和更新时间搜索候选项目。

## 查询字段

常用限定条件：

- `stars:>100`
- `pushed:>2026-01-01`
- `language:Python`
- `topic:ai-agent`

## 查询策略

1. 每个关键词单独查询，避免查询条件过宽。
2. 使用 `sort=stars` 获取成熟项目，使用 `sort=updated` 获取活跃项目。
3. 对同一仓库去重，保留来源关键词。
4. 记录查询语句、返回数量和失败原因。

## 需要保留的字段

- `full_name`
- `html_url`
- `description`
- `stargazers_count`
- `forks_count`
- `language`
- `topics`
- `pushed_at`
- `updated_at`
- `license`

## 注意事项

- GitHub Search API 有速率限制，失败时应重试或缩小范围。
- Search API 返回的信息不够完整，进入短名单前必须用 Repo API 补全。
