# 05 候选项目初筛

## 目标

排除明显不适合当前用户分析、包装或商业化验证的项目，形成短名单。

## 必读资源

- `strategies/project-filter-strategy.md`
- `criteria/project-value-criteria.md`
- `criteria/open-source-license-criteria.md`
- `assets/risk-checklist.md`

## 初筛维度

- 是否公开可访问
- 是否最近仍在维护
- README 是否清晰
- 是否有明确用户场景
- 是否具备可理解的产品价值
- 是否存在 License 信息
- 是否部署成本明显过高
- 是否偏底层库、论文复现或纯研究原型
- 是否涉及明显高风险用途
- 是否符合用户画像目标

## 执行步骤

1. 为每个候选项目给出 `保留`、`降级`、`排除` 三类判断。
2. 排除项目必须写明原因。
3. 许可证不清晰、维护不足或场景模糊的项目可降级，不必立即排除。
4. 涉及违法、攻击、隐私侵犯或绕过限制的项目直接排除或只保留风险说明。
5. 按综合价值和用户匹配度形成短名单。

## 建议输出

- `data/processed/shortlist-projects.json`

## 质检

- 不允许只按 Star 数排序。
- 不允许把高风险项目推进到 MVP 复刻方案。
- 短名单项目数量默认不超过 20 个。
