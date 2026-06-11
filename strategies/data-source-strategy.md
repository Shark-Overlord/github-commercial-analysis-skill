# 数据源策略

## 必需 API 数据源

- GitHub REST Search API：搜索候选项目。
- GitHub Repo API：获取项目详情、README、Release、License 和 Topics。
- GH Archive：判断近期 GitHub 事件热度。
- Hacker News Algolia API：判断项目是否有海外技术社区讨论。

本 Skill 的数据源只包含以上 4 个 API。项目 Demo、官网和竞品信息只能作为 GitHub Repo API、README、Release 或人工补充材料中的项目线索，不作为独立数据源配置项。

GH Archive 和 Hacker News Algolia API 属于舆情数据源。它们采集的不是项目基础信息，而是近期热度和需求热度，必须进入最终 `public_opinion_heat` 评分。

## 配置顺序

1. 先告诉用户 4 个 API 分别去哪里配置或授权。
2. 优先给出浏览器授权方式；如果不可行，再给出复制粘贴配置模板。
3. GitHub REST Search API 和 GitHub Repo API 共用 GitHub 认证方式：GitHub CLI、`GITHUB_TOKEN` 环境变量、用户临时粘贴 Token 或匿名低频访问。
4. GH Archive 配置公开访问方式：小时归档 HTTP 下载或 BigQuery。
5. Hacker News Algolia API 配置公共 endpoint 和查询方式。
6. 配置 GitHub REST Search API 的查询方式、限流处理和候选数量。
7. 配置 GitHub Repo API 的 README、Release、License、Topics 和仓库详情采集方式。
8. 记录不可用数据源、降级策略和可信度影响。

## 数据源状态

- `enabled`：本次分析会使用。
- `degraded`：可用性受限，只能用替代方式采集。
- `disabled`：用户禁止或当前环境不可用。

## 使用优先级

1. 单项目分析：优先 GitHub Repo API。
2. 批量日报：优先 GitHub REST Search API，再用 GitHub Repo API 补全短名单。
3. 热度判断：使用 GH Archive。
4. 海外讨论判断：使用 Hacker News Algolia API。
5. 商业化判断：基于 Repo API 采集到的 README、License、Release、Topics 和项目说明进行推断。

## 失败处理

- GitHub API 限流时，可降级为低频访问、缩小采集范围或使用已有采集数据，但必须标注数据不完整。
- GH Archive 不可用时，可降级为 GitHub Repo API 中的更新时间、Issue、Release 和 Star 信息，但要标注热度证据不足。
- HN Algolia 没有讨论不代表项目无价值，只代表海外社区传播证据不足。
- License 缺失时不能默认可商用，应标注为风险。
- 数据源未配置或不可用时，必须在最终报告中写入数据缺口。
