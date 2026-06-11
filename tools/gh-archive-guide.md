# GH Archive 使用说明

## 用途

用于判断项目近期 GitHub 事件热度，包括 Star、Fork、Issue、PR、Watch 等行为。

GH Archive 的结果属于舆情数据，必须进入最终 `github_event_heat` 和 `public_opinion_heat` 评分。

## 使用场景

- 批量日报需要判断项目是否近期被关注。
- Star 数很高但维护不确定时，用近期事件辅助判断。
- 新项目 Star 不高但增长快时，用事件热度作为补充信号。

## 建议指标

- 最近 7 天 Star 事件
- 最近 30 天 Fork 事件
- 最近 30 天 Issue 或 PR 活跃度
- 是否出现异常增长

## 输出字段

- `event_window_days`：统计窗口，例如 7 或 30 天。
- `star_events`：Star 事件数量。
- `fork_events`：Fork 事件数量。
- `issue_events`：Issue 事件数量。
- `pull_request_events`：PR 事件数量。
- `watch_events`：Watch 事件数量。
- `total_events`：事件总数。
- `trend_summary`：近期热度摘要。
- `confidence`：置信度，可使用 high、medium、low。
- `github_event_heat`：0 到 100 分。

## 解读规则

- 近期活跃不等于商业价值高。
- 事件热度可作为传播潜力和维护活跃度的证据。
- 无事件不一定排除，但要降低热度判断置信度。
