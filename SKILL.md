---
name: urban-desire-female-archetypes
description: Retrieve and compare source-linked female character mechanisms for Chinese urban fiction, or create and audit cards in this library. Use for character design, archetype search, and controlled hybridization; keep source facts, interpretation, and modern adaptation separate.
---

# 都市欲望女性原型库

把经典女性角色转换为可检索、可审计、可杂交的人物机制资产，而不是文学百科或原剧情复刻。

本目录是自包含技能；相对路径均以技能所在目录为根。保留整个仓库及引用资源，不能只复制本文件。数据以中文为主，`v0.1.0` 为研究预览。入口与版本见 `data/library-manifest.json`，浏览或接入方法见 `docs/ai-integration.md`。

## 检索与调用

先读 `AGENTS.md` 和 `references/source-rules.md`。从 `data/catalog.json`、`data/characters.jsonl` 或下列只读命令找候选，按 `card_id` 回读人物卡与 `sources/<card_id>_sources.md`；筛选摘要不能代替读源。

```shell
python scripts/archetypes.py search --query "秘密 退出" --limit 3
python scripts/archetypes.py get --id CN-HLM-001
python scripts/archetypes.py list --limit 30 --offset 0
python scripts/archetypes.py rules --name hybridization-rules
```

可用等价的 MCP 工具 `search_archetypes`、`get_archetype`、`list_archetypes` 和 `read_rules`。没有命令执行能力时，按 `llms.txt` 与 catalog 的完整 URL 浏览相关文件；不得假装已经运行工具或读过原作。

示例命令在技能根目录执行；跨目录调用时用脚本的绝对路径。

比较候选时说明长期匮乏、奖励、权力接口、升级与代价的差异，附 `card_id` 和卡片/来源定位。机制借用遵循 `references/hybridization-rules.md`：选择互补槽位，重新设计人物身份、关系、事件和解决路径，明确哪些内容是 `ADAPTATION`。

`Gold / Silver / PASS`、评分及置信度都是内部评估，不是独立核验或原创性认证；部分事实定位与现代设计仍待复核，见 `docs/open-source-assessment.md`。原角色的年龄未知或未成年时，不做情色化身体分析；现代成年设计不能覆盖原角色年龄证据。源作品、译文与摘录的权利不由本库许可覆盖，见 `COPYRIGHT.md` 和 `THIRD_PARTY_NOTICES.md`。

## 先读规则

始终先读 `AGENTS.md`。再按任务读取：

- 新建或修订人物卡：读 `templates/character-card.md`、`references/source-rules.md`、`references/archetype-taxonomy.md`、`references/visual-language.md`、`references/quality-gate.md`。
- 只做事实审计：读 `references/source-rules.md` 和 `references/quality-gate.md`。
- 只做视觉层：读 `references/source-rules.md` 和 `references/visual-language.md`；必须先通过年龄门。
- 人物杂交：在上述规则外，再读 `references/hybridization-rules.md`。
- 建索引或维护接入：读 `indexes/README.md`、`CONTRIBUTING.md`，并以 `data/archetypes.json` 的 ID、枚举和字段约定为准。llms.txt、catalog、manifest 与索引均是派生视图，不能手改。

引用的文件缺失时停止生产并报告，不得凭记忆补出规范。

## 单卡工作流

1. 建立来源记录和版本边界，先判定角色年龄状态。
2. 依次完成 `F → V → M → P → H → X → S → A → R`，不得用后层推断倒填 `F`。
3. `F` 只写可验证事实；不确定项写 `UNKNOWN`。
4. `V` 中的“现代男性视觉翻译”始终标为 `INTERPRETATION`。仅 `CONFIRMED_ADULT` 可做直白身体分析；未成年或年龄未知者只保留非情色辨识信息。
5. `M` 必须写成“长期匮乏 → 诱因 → 第一次越界 → 即时奖励 → 自我合理化 → 风险提高 → 继续加码 → 最终代价”的因果链，不能拿性格标签代替机制。
6. `P` 给出可重复发动、会升级且会付代价的剧情发动机；`H` 区分必须保留的机制与需要替换的时代变量。
7. `X` 只暴露可杂交槽位，不移植原作专有剧情；`S` 是检索坐标，不冒充事实测量。
8. `A` 必须寻找库内最近邻并写出最大差异；做不到时不得定为 `Gold`。
9. `R` 只压缩本卡已有内容，不得增加事实、机制、身体特征或分数；Gold 必须有完整 R1—R8。
10. 按 `Gold / Silver / Reference` 门槛定级。缺字段时降级，不得为了升级而脑补。

## 写入与批次规则

- 人物卡写入对应的 `characters/` 分类；来源证据写入 `sources/`；机器记录写入 `data/`；索引写入 `indexes/`；批次审计写入 `batches/`。
- 文件名和结构化 ID 必须稳定、唯一、可跨文件关联。
- 每批完成后执行事实、成人视觉、重复度、反克隆、R 压缩忠实度、机器字段和杂交接口审计。
- 未经明确授权，不开始人物批量生产；第一阶段不得直接生产 500 人。
- 任一事实来源、年龄门或质量门失败时停止升级等级，保留 `UNKNOWN` 或降级记录。
- 同步卡片与人工复核摘要后，运行 `python scripts/build-indexes.py`、`python scripts/build-discovery.py` 与 `python scripts/validate-library.py`；用两个构建器的 `--check` 确认没有过期生成物。结构与字节检查只验证同步，不能代替事实审计。
