# 03 采集任务规划

## 目标

把用户画像转化为可执行的数据采集任务，明确搜索关键词、排除词、数据源、数量限制和筛选门槛。

## 必读资源

- `strategies/search-strategy.md`
- `strategies/data-source-strategy.md`
- `schemas/discovery-task-schema.json`
- `assets/data-source-map.md`

## 执行步骤

1. 根据用户画像生成 5 到 12 个英文搜索关键词，优先覆盖用户目标产出和目标市场。
2. 生成 GitHub Topics、语言偏好、Star 门槛、更新时间范围和候选数量。
3. 设置排除关键词，默认排除恶意软件、破解、钓鱼、绕过限制、隐私侵犯等高风险方向。
4. 决定是否采集 README、License、Release、Issues、近期事件和海外社区讨论。
5. 输出结构化采集任务，字段参考 `schemas/discovery-task-schema.json`。

## 默认参数

- `min_stars`: 100
- `updated_within_days`: 180
- `candidate_limit`: 100
- `shortlist_limit`: 20
- `final_report_limit`: 8

## 质检

- 搜索词必须和用户画像相关，不能只按 GitHub 热度搜索。
- 采集任务必须包含排除规则。
- 任务数量要可执行，避免生成过大的采集范围。
