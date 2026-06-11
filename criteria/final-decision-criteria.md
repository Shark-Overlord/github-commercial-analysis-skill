# 最终决策标准

## 目标

最终推荐结果必须由明确评分公式和硬性降级规则共同决定，不能只依赖 Star 数、主观偏好或单一商业潜力判断。

## 最终评分公式

最终分 `final_score` 按 100 分制计算：

| 维度 | 权重 | 说明 |
| --- | ---: | --- |
| 用户匹配 `user_fit` | 20% | 是否匹配当前 Skill 使用者身份、目的、目标用户、时间预算和技术条件。 |
| 商业潜力 `commercial_potential` | 20% | 是否有清晰痛点、付费理由、中文市场适配和可包装产品形态。 |
| MVP 可行性 `mvp_feasibility` | 15% | 是否能在用户时间预算内做出可验证版本。分数越高表示越容易落地。 |
| 内容传播价值 `content_virality` | 15% | 是否适合图文、短视频、课程案例或公开展示。 |
| 风险可控 `risk_control` | 15% | License、合规、隐私、品牌、平台规则和技术风险是否可控。 |
| 舆情与需求热度 `public_opinion_heat` | 15% | GH Archive 的近期 GitHub 事件热度 + Hacker News Algolia 的社区讨论和需求信号。 |

如果上游数据仍使用旧字段 `mvp_difficulty`，必须在最终排序前转换为 `mvp_feasibility`。本规则中的 MVP 分数含义始终是“分数越高越容易落地”，不得把高难度项目误算为高可行性项目。

计算方式：

```plain
final_score =
  user_fit * 0.20 +
  commercial_potential * 0.20 +
  mvp_feasibility * 0.15 +
  content_virality * 0.15 +
  risk_control * 0.15 +
  public_opinion_heat * 0.15
```

## 舆情与需求热度

`public_opinion_heat` 由两个子项组成：

```plain
public_opinion_heat = github_event_heat * 0.50 + community_demand_heat * 0.50
```

### GitHub 事件热度 `github_event_heat`

来源：GH Archive。

用于判断项目近期是否有真实 GitHub 行为热度，重点看：

- 最近 7 天 Star 事件；
- 最近 30 天 Fork 事件；
- 最近 30 天 Issue、PR、Watch 事件；
- 是否出现异常增长；
- 近期热度是否和项目当前阶段一致。

解释规则：

- 高热度说明项目近期被开发者关注，可提升传播和机会优先级。
- 无热度不等于没有价值，但会降低舆情分和置信度。
- 如果 GH Archive 不可用，只能降级使用 GitHub Repo API 的更新时间、Issue、Release、Star 等信息，并在报告中标注数据缺口。

### 社区需求热度 `community_demand_heat`

来源：Hacker News Algolia API。

用于判断项目是否在海外技术社区出现讨论和需求信号，重点看：

- HN 命中数量；
- 有效命中数量，而不是原始命中数量；
- 讨论发布时间；
- 点赞和评论数量；
- 讨论中出现的痛点、质疑、替代方案和真实使用反馈；
- 项目名称、仓库链接、作者组织名和核心关键词是否被反复提及。

解释规则：

- 高质量讨论说明项目具备社区传播或需求验证证据。
- 有争议不一定扣分，但必须判断争议是否影响商业化。
- 没有 HN 讨论不代表项目无价值，只代表海外技术社区证据不足。
- 同名项目、泛词、历史文章或其他公司/产品的误命中不得计入 `community_demand_heat`。
- 原始命中很多但有效命中很少时，必须降低社区需求热度和置信度。

## 推荐等级

| 最终分 | 推荐等级 |
| ---: | --- |
| 85-100 | 强烈推荐 |
| 75-84 | 推荐 |
| 65-74 | 谨慎推荐 |
| 50-64 | 降级为内容/学习/风险案例 |
| 0-49 | 不推荐 |

## 硬性降级规则

以下规则优先于最终分：

- License 高风险、不明确或 API 返回 `NOASSERTION`：最高只能为“谨慎推荐”。
- 涉及法律、隐私、侵权、灰产、破解、绕过限制、敏感数据或平台滥用风险：不得进入商业推荐，只能降级为学习/风险案例。
- 用户时间预算内无法做出可验证 MVP：不得进入前 3。
- 明显不符合当前 Skill 使用者身份、目的或目标市场：不得进入“推荐”及以上。
- GH Archive 和 HN Algolia 均不可用：舆情分最高 50，并且必须在报告标注数据缺口。
- 只有 Star 高但缺少用户场景、商业包装和近期需求证据：不得进入前 5。

## 输出要求

每个最终项目必须输出：

- `final_score`；
- 六个维度分数；
- `github_event_heat` 和 `community_demand_heat`；
- 舆情证据摘要；
- 推荐等级；
- 降级规则是否触发；
- 最终决策理由。
