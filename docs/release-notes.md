# v0.1.0 — research-preview

首次公开版本包含 30 张人物研究卡，以及对应来源记录、九层模板、十个检索视图和只读 AI 接口。定位是可追溯的人物机制研究与原创设计参考；当前版本适合探索、比较与继续校准。

## AI 可以怎样使用

- 从根目录的 [`llms.txt`](../llms.txt) 找到阅读顺序与稳定入口。
- 用 [`data/library-manifest.json`](../data/library-manifest.json) 和 [`data/catalog.json`](../data/catalog.json) 获取版本、卡片 ID、来源路径及哈希。
- 通过标准库 CLI 返回 JSON，或连接本地 stdio MCP 的四个只读工具。
- 将整个仓库作为技能目录使用，入口是 [`SKILL.md`](../SKILL.md)；安装与调用见[AI 接入指南](ai-integration.md)。

```shell
git clone --branch v0.1.0 https://github.com/jsfgmkg95d-source/urban-desire-female-archetypes.git
cd urban-desire-female-archetypes
python scripts/archetypes.py search --query "秘密 退出" --limit 3
```

## 质量状态

30 张卡的 `Gold / Silver` 是内部评级，审阅记录也属于项目内部流程。现有 190 条事实记录中，有 100 条仍使用笼统的“对应来源定位”表达；部分评分理由、功能标签及现代移植的剧情距离需要复核。工具与机器清单明确返回 `research-preview` 状态，供使用者决定是否继续读源。

结构校验、索引一致性和协议测试验证的是可读取、可检索和数据关系。它们不替代来源事实审查、独立原创性审查或作品权利判断。完整证据与优先事项保存在[开源价值评估](open-source-assessment.md)。

## 许可与版本

原创内容采用 [CC BY 4.0](../LICENSE)，代码采用 [MIT](../LICENSES/MIT.txt)。第三方表达不包含在本库授权中，见[授权范围](../COPYRIGHT.md)与[第三方说明](../THIRD_PARTY_NOTICES.md)。

`main` 随维护更新；`v0.1.0` 用于复现本次发布。机器清单中的文本哈希统一按 UTF-8 与 LF 换行计算，避免操作系统换行差异造成误判。`llms.txt` 提供公开导航；它不能保证任何外部 AI 或搜索引擎自动收录。
