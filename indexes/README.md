# 索引规范

本目录保存从人物卡派生的检索索引，不保存新的事实。索引值必须能回到人物卡、来源记录和稳定 `card_id`；索引不允许修正或补写人物卡。

Stage 3B 起加入 R 快速调用胶囊。`data/characters.jsonl` 是机器摘要；本目录中的 Markdown 文件是人工可读派生索引。二者都不得补写人物卡没有的事实，R 也只能压缩卡片已有层。

## 1. 稳定标识

- `card_id`：全库唯一、创建后不因改名或译名变化而改变。
- `source_id`：定位一条来源记录。
- `archetype_id`：使用 `data/archetypes.json` 中的一级原型 ID。
- `engine_id`：人物卡内部唯一，推荐 `<card_id>-P01`。
- `hybrid_id`：杂交结果唯一，不复用来源卡 ID。
- 别名只用于查询，不作为主键。

## 2. 未来索引产物

| 文件 | 用途 | 主键/粒度 |
|---|---|---|
| `characters.jsonl` | 一行一张卡的机器检索摘要 | `card_id` |
| `by-archetype.json` | 一级/次级原型到人物卡 | `archetype_id` |
| `by-visual-function.json` | 身份反差、欲望、误会、竞争、权力、危险、剧情推进 | `visual_plot_function` |
| `by-mechanism.json` | 匮乏、越界、奖励、权力、秘密、加码和代价 | 规范化机制词 |
| `by-source.json` | 来源作品、版本、媒介和分类 | 来源键 |
| `hybridization-pool.json` | 已通过质量门的可输出槽位 | `card_id + slot_id` |
| `nearest-neighbors.json` | Anti-Clone 最近邻和差异 | `card_id` |

当前人工可读索引为：`master-index.md`、`by-archetype.md`、`by-visual-hook.md`、`by-modern-role.md`、`by-relationship-mechanism.md`、`by-plot-engine.md`。首批只有两张卡时，最近邻互指；后续入库必须重算。

上述文件只有出现合格人物卡后才创建，不为保持目录好看而生成空伪数据。

## 3. `characters.jsonl` 最小字段

每行是一个 JSON 对象，至少包含：

```json
{
  "card_id": "stable-id",
  "tier": "Silver",
  "name_zh": "示意值，不是实际人物",
  "aliases": [],
  "source_category": "world-classics",
  "source_work": "work-id-or-title",
  "primary_archetype_id": "identity-contrast",
  "secondary_archetype_ids": [],
  "adult_status": "UNKNOWN",
  "layer_completion": {"F": true, "V": false, "M": true, "P": true, "H": true, "X": true, "S": true, "A": false, "R": false},
  "visual_signature": [],
  "visual_plot_functions": [],
  "long_term_lack": "normalized phrase",
  "first_crossing": "normalized phrase",
  "immediate_reward": "normalized phrase",
  "power_method": "normalized phrase",
  "jealous_resource": "normalized phrase",
  "secret_leverage": "normalized phrase",
  "escalation_logic": "normalized phrase",
  "fatal_miscalculation": "normalized phrase",
  "plot_engine_ids": [],
  "urban_preserve": [],
  "adult_adaptation_age": "21+ explicit age or range",
  "adult_adaptation_role": "modern original role",
  "adult_visual_signature": [],
  "adult_low_register_first_glance": "adult adaptation only",
  "adult_identity_body_contrast": [],
  "adult_clothing_contrast": {},
  "adult_visual_plot_functions": [],
  "hybridization_slots": [],
  "scores": {},
  "nearest_neighbor_card_id": null,
  "anti_clone_result": "REVISE",
  "archetype_uniqueness_statement": "Gold only, max 60 Chinese characters",
  "retrieval_capsule": {
    "one_line_archetype": "max 40 Chinese characters",
    "visual_signature": {"memory_points": [], "identity_body_contrast": "", "clothing_effect": ""},
    "desire_chain": "lack → first crossing → reward → escalation → cost",
    "power_interface": {"power_method": "", "secret_use": "", "feared_resource_loss": ""},
    "best_urban_container": {"age": 28, "identity": "", "marital_status": "", "class_position": "", "core_conflict": ""},
    "hybrid_recommendation": {"inherit": "", "conflict": "", "never_copy_together": ""},
    "forbidden_as": ["", "", ""],
    "machine_call_string": ""
  },
  "source_ids": []
}
```

该代码块只说明字段，不构成已生产人物。

## 4. 检索维度

### 来源与可信度

按来源类别、作品、版本、事实截止点、来源可靠性、成年状态和卡片等级筛选。

### 视觉辨识

按 `body_focus`、视觉签名轴、七类剧情功能和年龄门筛选。查询身体特征时必须同时返回它服务的剧情功能，禁止只输出身体目录。

### 人物机制

按一级/次级原型、长期匮乏、诱因、第一次越界、即时奖励、自我合理化、权力方法、嫉妒资源、秘密杠杆、加码和最终代价筛选。

### 都市剧情

按2020年代必须保留项、职业/城市容器、三个剧情发动机、危险等级和可移植性筛选。H4 成人视觉检索必须同时返回 `adult_adaptation_age`、`adult_adaptation_role`、视觉签名、身份身体反差、穿衣反差和剧情功能，并明确标记为 `ADAPTATION`。

### 杂交

按可输出槽位、兼容原型、冲突原型、禁止继承项和克隆风险筛选。检索结果必须带槽位来源，不返回不可追溯的“混合灵感”。

### R 快速调用

R 默认用于首轮召回：返回一句话母体、视觉签名、欲望链、权力接口、最佳都市容器、三槽杂交建议、三项禁止写法和机器调用串。命中后必须回读完整卡片；R 不得作为事实来源，也不得覆盖 F/V/M/H/X/S/A。

## 5. 查询返回规则

1. 默认返回 `card_id`、名称、tier、匹配字段、匹配原因、事实/解释类型和来源定位。
2. 查询 Gold 时必须确认最近邻审计仍有效；库新增卡后可能需要重算。
3. `UNKNOWN` 不得当作否定值。例如“未知是否有秘密”不能进入“没有秘密”结果。
4. 视觉查询必须应用成年状态过滤；`CONFIRMED_MINOR` 和 `UNKNOWN` 不进入情色化身体检索。
   H4 是独立例外路径：只检索 `DESIGNATED_ADULT` 且明确 21+ 的现代原创移植，不得把结果合并为原角色 V 事实。
5. S 分值只用于排序，最终结果必须同时展示机制理由。
6. 索引与卡片冲突时，以卡片和来源为准，索引标记过期并重建。

## 6. 更新顺序

1. 人物卡通过对应等级质量门；
2. 来源记录已落盘；
3. 生成或更新 `characters.jsonl`；
4. 更新原型、视觉、机制、来源和杂交索引；
5. 重算最近邻并运行 Anti-Clone；
6. 抽查索引值能回链到卡片字段；
7. 保存批次审计结果。

禁止手工只改索引而不改权威人物卡。
