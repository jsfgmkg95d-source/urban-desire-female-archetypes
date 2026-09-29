# 数据说明

本目录保存检索所需的数据。卡片与来源记录承载内容依据；这里的摘要和登记不能覆盖原始内容。

| 文件 / 字段 | 作用 | 维护方式 |
|---|---|---|
| `archetypes.json` 的分类、枚举与约束 | 项目字段契约与 24 个一级原型 | 修改规则时人工修订并记录兼容性影响 |
| `characters.jsonl` | 一行一张卡的机器检索摘要 | 从卡片压缩，人工复核后同步 |
| `archetypes.json.character_records` | ID、姓名、等级、主原型的登记缓存 | 从 JSONL 自动生成 |
| `catalog.json` | AI 可遍历的卡片目录、来源 URL、检索字段与质量状态 | 由 `scripts/build-discovery.py` 生成 |
| `library-manifest.json` | 发布版本、入口、许可证范围、统计与文本哈希 | 由 `scripts/build-discovery.py` 生成 |

`schema_version` 标记项目契约版本。`archetypes.json` 本身不是标准 JSON Schema 文件；完整字段要求由契约和校验工具共同表达。原型名称与机制解释见[分类法](../references/archetype-taxonomy.md)。

## 稳定键与数据类型

- `card_id` 创建后保持稳定，用来关联人物卡、来源和最近邻。
- `source_ids` 对应 `sources/<card_id>_sources.md` 中的来源登记。
- 主、次原型使用契约中的 ID，译名和别名不充当主键。
- 现有 `adult_adaptation_age` 用数字保存具体年龄；工具也接受明确闭区间字符串，如 `25-30`，下限须满足成年设计门。R5 与卡片 H4 必须表达同一年龄或区间。
- 未设计 H4 的 Reference 可将年龄写为 `null`、角色写 `UNKNOWN`，并保持 H4 视觉数组与相关对象为空；不凭字段占位开启成年视觉检索。
- `adult_status` 描述原著版本中的年龄状态；现代设计中的年龄不能覆盖它。
- S 分数与 `evidence_confidence` 是内部分析坐标，其理由保存在卡片中。
- `retrieval_capsule` 对应 R1—R8，只能压缩卡片已有信息。

## 派生顺序

```mermaid
flowchart LR
    E[来源与版本记录] --> C[人物卡]
    C --> J[人工复核的 JSONL 摘要]
    K[分类与字段契约] --> J
    J --> I[十个 Markdown 索引]
    J --> R[character_records 登记缓存]
```

构建器只更新索引和登记缓存，不生成事实、不修订 JSONL、不重算等级、评分或最近邻。卡片内容改变后，维护者必须先复核 JSONL，再运行构建器。

```shell
python scripts/build-indexes.py
python scripts/build-discovery.py
python scripts/build-indexes.py --check
python scripts/build-discovery.py --check
```

`--check` 以现有输入重新计算生成物并比较，发现过期时返回失败。使用与维护过程见[贡献说明](../CONTRIBUTING.md)。

发布元数据的哈希和字节数采用 `utf8-lf-text`：读取 UTF-8 文本，将 CRLF / CR 规范为 LF 后计算。它们验证指定文本版本的一致性，不能证明来源事实。`main` URL 用于最新内容，`v0.1.0` URL 用于固定发布；复现研究应记录所用版本。

只读检索和 MCP 调用见[AI 接入指南](../docs/ai-integration.md)。返回值中的 `research-preview` 与内部等级是不同维度；派生目录与摘要不会提升原卡的证据质量或扩大第三方授权。
