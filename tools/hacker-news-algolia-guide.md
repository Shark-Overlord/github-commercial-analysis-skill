# Hacker News Algolia API 使用说明

## 用途

用于判断项目是否在海外技术社区被讨论，以及讨论热度、争议点和传播潜力。

Hacker News Algolia API 的结果属于舆情数据，必须进入最终 `community_demand_heat` 和 `public_opinion_heat` 评分。

## 查询方式

可按以下内容搜索：

- 项目名称
- 仓库地址
- 作者或组织名
- 项目核心关键词

## 相关性过滤

HN Algolia 命中不能直接等同于项目讨论。进入 `community_demand_heat` 前，必须先做相关性判断：

- 强相关：讨论 URL 指向目标 GitHub 仓库、官网、作者组织，或标题明确包含项目名和目标用途。
- 中相关：标题或正文讨论同一产品类别，并且能和项目目标用户或痛点对应。
- 弱相关：只出现同名词、泛词、历史文章、其他同名公司或其他同名项目。
- 弱相关和无关命中不得计入点赞数、评论数和热度分，只能写入排除说明。
- 关键词匹配必须使用完整词组、URL、owner/repo 或域名证据，不能用简单 substring。比如 `browser use` 不能匹配到 `browser user-agent`。

对于 `Graphite`、`browser-use`、`agent`、`canva clone` 这类容易产生歧义的关键词，必须优先使用仓库 URL、owner/repo、官网域名和作者组织名做精确查询。无法确认相关性时，降低置信度。

## 需要记录

- 讨论链接
- 发布时间
- 点赞或评论数量
- 讨论摘要
- 命中相关性
- 被排除的噪声命中
- 正面反馈
- 负面质疑

## 输出字段

- `hn_hits`：原始命中数量。
- `matched_hn_hits`：通过相关性过滤的有效命中数量。
- `excluded_hn_hits`：被排除的噪声命中数量。
- `hn_points`：有效相关讨论总点赞数或代表性点赞数。
- `hn_comments`：有效相关讨论评论数量。
- `discussion_titles`：代表性讨论标题。
- `discussion_summary`：需求、争议和反馈摘要。
- `positive_signals`：正向需求信号。
- `negative_signals`：负向或风险信号。
- `match_confidence`：相关性置信度，可使用 high、medium、low。
- `confidence`：置信度，可使用 high、medium、low。
- `community_demand_heat`：0 到 100 分。

## 解读规则

- 有高质量讨论：说明项目具备技术社区传播证据。
- 有争议：需要判断争议是否会影响商业化。
- 没有讨论：不能直接判定项目无价值，只能说明海外社区证据不足。
- 原始命中多但有效命中少：说明关键词噪声高，不得给高舆情分。
