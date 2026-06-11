# 06 短名单项目信息补全

## 目标

为进入短名单的项目补全深度信息，避免后续分析建立在不完整资料上。

## 必读资源

- `tools/github-repo-api-guide.md`
- `tools/gh-archive-guide.md`
- `tools/hacker-news-algolia-guide.md`
- `schemas/project-info-schema.json`

## 补全字段

- README 摘要
- 核心功能
- 技术栈
- 部署方式
- Demo 或在线体验
- 文档完整度
- Release 情况
- License 类型
- Issues 活跃情况
- 最近提交情况
- GitHub 近期事件热度
- Hacker News 讨论情况
- 舆情与需求热度分
- 舆情数据缺口
- 可能竞品或替代方案

## 执行步骤

1. 优先补全最终可能进入报告的项目。
2. 对缺失字段标注 `未知` 或 `未发现`，不要编造。
3. 记录证据来源，例如 README、Release、License、Issues 或社区讨论链接。
4. 将 GH Archive 和 Hacker News Algolia API 的舆情信号写入 `public_opinion_signals`。
5. 将补全结果更新到项目结构化对象中。

## 建议输出

- `data/processed/enriched-shortlist-projects.json`

## 质检

- 每个推荐项目至少应有 README 摘要、核心功能、部署难度、License 和风险备注。
- 不能把“未采集到”写成“没有”。
- 每个进入最终排序的项目必须有 `public_opinion_signals`；如果舆情数据缺失，必须写明缺口和置信度影响。
