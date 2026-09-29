# 都市欲望女性原型库

从经典角色中提取可追溯的人物机制，用于现代都市小说的检索、比较与原创设计。

**Urban Desire · Female Archetypes** — source-traceable character mechanisms for fiction writing, with separate fact, interpretation, and adaptation layers.

这里的“欲望”包括归属、尊严、资源、阶层、控制与亲密需求。项目面向都市男频创作，每张卡把人物的匮乏、行动、奖励、加码与代价连成因果链，再提供现代移植和组合接口。

## 从这里开始

| 你想做什么 | 入口 |
|---|---|
| 浏览人物与现有规模 | [人物总索引](indexes/master-index.md) |
| 按剧情问题寻找人物 | [检索导航](indexes/README.md) |
| 第一次使用，理解卡片各层 | [使用指南](docs/guide.md) |
| 看一次完整的检索过程 | [检索示例](examples/retrieval.md) |
| 修订人物、补来源或贡献新卡 | [贡献说明](CONTRIBUTING.md) |
| 交给 AI 协助维护 | [工作技能](SKILL.md) · [仓库规则](AGENTS.md) |
| 判断是否值得公开 | [开源价值与发布条件](docs/open-source-assessment.md) |

只阅读 Markdown 即可使用。维护脚本需要 **Python 3.11 或以上**，仅使用标准库，无需安装第三方依赖，也无需模型 API。

## 人物卡的九层结构

| 层 | 内容 | 性质 |
|---|---|---|
| F | 版本范围内的原著事实与证据 | `FACT` |
| V | 视觉、姿态与出场辨识 | 明确区分事实与 `INTERPRETATION` |
| M | 匮乏 → 诱因 → 越界 → 奖励 → 合理化 → 风险 → 加码 → 代价 | `INTERPRETATION` |
| P | 可反复发动、升级并付出代价的剧情机制 | `ADAPTATION` |
| H | 现代都市容器与需要替换的时代变量 | `ADAPTATION` |
| X | 可组合槽位、冲突与禁止继承项 | 原创设计接口 |
| S | 用于检索排序的数值与理由 | 内部分析坐标 |
| A | 最近邻差异与反克隆审阅 | 内部质量审阅 |
| R | 只压缩已有内容的快速调用胶囊 | 派生摘要 |

先用 R 召回候选，再回读完整卡片和来源。`Gold / Silver / Reference` 是仓库内部的可调用等级；分数、等级与 `PASS` 都不能替代独立读源、文学判断或原创性审查。当前内容的已知问题见[评估中的内容复核清单](docs/open-source-assessment.md)。

## 内容与证据边界

- F、解释和现代设计各有归属；证据不足时保留 `UNKNOWN`。
- 经典角色提供机制分析的样本。原创设计须改变因果组合，避免照搬姓名、台词、专有关系与事件顺序。
- 项目含成年角色的视觉分析。原角色未成年或年龄不明时，V 层只保留非情色辨识；H4 独立标记为现代原创 `ADAPTATION`，不能反向证明原角色成年。
- 本库研究特定创作视角，不把文学人物的机制推广为现实女性的分类或行为规律。
- 本仓库独立维护，现有小说仓库中的正文与设定不受本库修改。

完整约束见[来源规则](references/source-rules.md)、[视觉规范](references/visual-language.md)、[质量门](references/quality-gate.md)和[组合规则](references/hybridization-rules.md)。

## 仓库结构

```text
characters/   按来源传统与作品组织的人物卡
sources/      与 card_id 对应的来源与版本记录
references/   事实、分类、视觉、质量与组合规则
templates/    人物卡模板
data/         字段契约、机器摘要与生成的登记缓存
indexes/      自动生成的十个检索视图与导航
batches/      历史生产、校准与审阅记录
docs/         使用指南与发布评估
examples/     可照着使用的检索示例
scripts/      索引构建与校验工具
```

现有样本来自中国经典、世界经典和神话史诗。影视、动漫与游戏是字段契约支持的来源类别；出现合格人物卡时再创建对应目录。

## 维护命令

先修订卡片和来源，复核机器摘要，再重建索引：

```shell
python scripts/build-indexes.py
python scripts/validate-library.py
```

只检查是否同步，不改写文件：

```shell
python scripts/build-indexes.py --check
python scripts/validate-library.py --json
```

Windows 也可运行 `pwsh -File scripts/validate-library.ps1`。CI 在 Windows 与 Linux 上执行相同检查。校验覆盖结构、关联、枚举、约定与派生视图的一致性；原著事实、分析理由和近义重复仍需人工审阅。

人物卡和来源是内容依据，JSONL 是经过复核的检索摘要，Markdown 索引与登记缓存是生成物。完整维护顺序见[贡献说明](CONTRIBUTING.md)，数据字段见[数据说明](data/README.md)。

## 许可与公开状态

截至 2026-09-29，本项目仍处于私有整理与评估阶段，尚未选定开放许可证。公开发布前需要明确代码、原创分析内容和第三方来源材料各自的授权范围；具体建议及待办见[开源评估](docs/open-source-assessment.md)。
