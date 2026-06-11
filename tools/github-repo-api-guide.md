# GitHub Repo API 使用说明

## 用途

用于补全单个项目详情，包括 README、License、Release、Issues、Topics 和最近提交情况。

## 建议采集内容

- 仓库基础信息
- README 原文和摘要
- License 类型和文件内容
- Release 列表
- Open Issues 数量
- 最近提交时间
- 默认分支
- Topics
- Homepage 或 Demo 地址

## README 处理

1. 优先读取默认分支 README。
2. 如果 README 很长，先提取项目定位、安装方式、使用示例、Demo、License 和限制说明。
3. 如果 README 为空或不可读，将项目降级处理。

## License 处理

- 有 License：记录类型，不直接得出法律结论。
- 无 License：标注商用风险。
- 依赖第三方模型、数据或素材：单独标注来源风险。

## 注意事项

不要只用项目描述判断用途，必须结合 README、Release 或文档证据。
