---
name: urban-desire-female-archetypes
description: Create, audit, index, retrieve, or hybridize source-traceable female archetype cards for modern Chinese urban male-oriented fiction. Use for this library's F/V/M/P/H/X/S/A/R workflow; do not use it to copy original plots or eroticize minors or age-unknown characters.
---

# 都市欲望女性原型库

把经典女性角色转换为可检索、可审计、可杂交的人物机制资产，而不是文学百科或原剧情复刻。

## 先读规则

始终先读 `AGENTS.md`。再按任务读取：

- 新建或修订人物卡：读 `templates/character-card.md`、`references/source-rules.md`、`references/archetype-taxonomy.md`、`references/visual-language.md`、`references/quality-gate.md`。
- 只做事实审计：读 `references/source-rules.md` 和 `references/quality-gate.md`。
- 只做视觉层：读 `references/source-rules.md` 和 `references/visual-language.md`；必须先通过年龄门。
- 人物杂交：在上述规则外，再读 `references/hybridization-rules.md`。
- 建索引或检索：读 `indexes/README.md`，并以 `data/archetypes.json` 的 ID、枚举和字段约定为准。

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
