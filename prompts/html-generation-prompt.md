# HTML 报告生成提示词

请根据最终分析结果生成单文件 HTML 报告。

必须遵守：

1. 默认文件名为 `github-opportunity-daily-report.html`。
2. HTML 文件必须使用 UTF-8 编码保存，`<head>` 中必须包含 `<meta charset="utf-8">`。
3. 使用内联 CSS。
4. 不默认依赖外部 CDN。
5. 报告结构清晰，适合浏览器阅读、截图和转 PDF。
6. 必须包含用户画像、今日结论、按最终排序排列的单项目机会卡、MVP、变现、内容传播、风险和数据来源。
7. 必须展示最终分 `final_score`、舆情热度 `public_opinion_heat`、GitHub 事件热度 `github_event_heat`、社区需求热度 `community_demand_heat`。
8. 推荐等级和排序必须遵循 `criteria/final-decision-criteria.md` 的评分公式和硬性降级规则。
9. 报告必须手机优先。移动端可以不展示排行表，项目卡片的 DOM 顺序就是最终推荐顺序。

输出要求：

- 不输出 Markdown 摘要替代 HTML。
- 不为了桌面排行表牺牲手机阅读；卡片必须单列适配手机屏幕，长项目名和链接必须自动换行。
- 所有中文文案应可直接给用户阅读。
- 风险和默认假设必须清楚显示。
- GH Archive 和 Hacker News Algolia API 的结果必须作为舆情数据展示，不得只写成“参考信号”。
- 如果舆情数据缺失，必须显示缺失来源和对最终分的影响。
- 写入文件时显式指定 UTF-8 编码。PowerShell 使用 `-Encoding UTF8`；Python 使用 `encoding="utf-8"`。
- 写入后重新读取 HTML 文件，检查是否存在 `锟斤拷`、`���`、`鎴`、`涓` 等乱码特征。
- 写入后检查是否存在连续问号，例如 `????`。如果存在，说明中文可能在生成阶段已丢失，必须重新生成，不能把该文件交付给用户。
- 在 Windows PowerShell 环境中，不要用管道传递含中文的大段脚本生成 HTML；使用 UTF-8 编码的脚本文件或模板文件生成。
- 如果报告应该是中文报告，写入后统计中文字符数量；中文字符过少或标题大面积是问号时，视为交付失败。
