# 检索导航与索引规范

十个视图从 `data/characters.jsonl` 自动生成，只提供召回与比较，不新增事实。命中后回读完整人物卡和来源。

总索引登记所有等级。应用视图显示等级，只收录 Gold / Silver 的相关已完成层；Reference 保留为资料条目，未设计 H4 或未完成 R 的记录不进入相应视图。

## 选择入口

| 视图 | 适合回答的问题 | 主要字段 / 所属层 |
|---|---|---|
| [人物总索引](master-index.md) | 库里有什么？等级、来源和最近邻是什么？ | 稳定 ID、Metadata、A |
| [一级原型](by-archetype.md) | 哪些人物以同类机制持续行动？ | 主原型、R1 |
| [视觉签名](by-visual-hook.md) | 现代设计如何被辨识或误读？ | H4 / R2，`ADAPTATION` |
| [身份反差](by-identity.md) | 哪种公共位置与私人需求形成张力？ | 来源边界、H4 |
| [欲望机制](by-desire-mechanism.md) | 匮乏怎样变成奖励与加码？ | M 的机器摘要 |
| [权力方式](by-power-method.md) | 她如何改变关系中的选项？ | M 的机器摘要 |
| [秘密杠杆](by-secret-method.md) | 信息如何成为要价、解释或退出工具？ | F / M 的机器摘要 |
| [现代角色](by-modern-role.md) | 哪个都市职业和资源容器适合该机制？ | H4 / R5，`ADAPTATION` |
| [关系机制](by-relationship-mechanism.md) | 亲密、控制和最怕失去的资源如何关联？ | R1 / R4 |
| [剧情发动机](by-plot-engine.md) | 哪张卡包含可继续读的 P 发动机？ | 发动机 ID、都市冲突、R3 |

剧情视图合并同一卡的发动机 ID；完整触发、行动、阻力、收益、升级、代价与重复条件保存在卡片 P 层。表中的都市冲突和欲望链是卡片摘要，不冒充逐发动机内容。

## 内容依据与稳定标识

人物卡与来源记录是内容依据，JSONL 是人工复核的机器摘要，索引与 `character_records` 登记缓存是生成物。派生内容与卡片冲突时，先查卡片和来源，再修订摘要并重建。

| 标识 | 规则 |
|---|---|
| `card_id` | 全库唯一，改名或换译名时保持稳定 |
| `source_id` | 回链对应来源记录 |
| `archetype_id` | 使用 `data/archetypes.json` 的分类 ID |
| `engine_id` | 卡内唯一，通常为 `<card_id>-P01` |
| `hybrid_id` | 新的组合设计另建 ID，不复用来源卡 ID |

别名用于查询，不作主键。机器字段、枚举和层约定见[数据说明](../data/README.md)及[字段契约](../data/archetypes.json)。未来若新增 JSON 视图或第三方导出，先明确用途与生成方式；当前不创建空的计划产物。

## 查询与返回规则

1. 默认返回 `card_id`、姓名、内部等级、匹配字段、匹配原因、所属层与来源入口。
2. R 用于首轮召回；选中后回读 F / V / M / P / H / X / S / A，R 不能覆盖完整卡。
3. `UNKNOWN` 不等于否定值。未知是否有秘密的卡不能被当成“没有秘密”。
4. 原角色视觉查询应用成年状态限制；`CONFIRMED_MINOR` 和 `UNKNOWN` 的 V 不进入情色身体检索。
5. H4 查询独立返回明确的现代年龄、角色、视觉签名、身份与衣着反差、剧情功能，并标为 `ADAPTATION`；不得合并成原角色事实。
6. S 数值只供排序，展示机制理由；Gold 与 `PASS` 只表示内部审阅结论。
7. 新卡可能改变最近邻。机器索引不会重算语义相似度，需要另做反克隆审阅。

## 重建与检查

```shell
python scripts/build-indexes.py
python scripts/build-indexes.py --check
python scripts/validate-library.py
```

构建器更新十个 Markdown 视图与 `archetypes.json.character_records` 缓存，不改写人物、来源、JSONL、评分或等级。`--check` 只比较输入和生成物，发现过期时返回失败。

内容更新顺序为：人物卡与来源 → 质量和最近邻审阅 → JSONL 摘要 → 重建 → 校验 → 人工回读抽查。完整要求见[贡献说明](../CONTRIBUTING.md)，第一次使用见[指南](../docs/guide.md)与[检索示例](../examples/retrieval.md)。
