# AI 接入与调用

本库提供三条接入路径：浏览公开原文、克隆后调用命令行、通过本地 MCP stdio 调用只读工具。内容主要为中文；稳定主键是 `card_id`。`v0.1.0` 为 `research-preview`，检索结果适合研究和创作比较，引用事实仍需回读人物卡与来源。

## 选择路径

| AI 可用能力 | 入口 | 适合做什么 |
|---|---|---|
| 能读取网页或公开文件 | [llms.txt](../llms.txt) 与 [manifest](../data/library-manifest.json) | 找到规则、机器数据、卡片与来源 |
| 能执行本地命令 | `scripts/archetypes.py` | 按机制词查候选，按 ID 读卡，列登记与规则 |
| 支持 MCP stdio | `scripts/mcp-server.py` | 用四个只读工具完成同样的查询 |
| 支持目录式 Agent Skills | 根目录 [SKILL.md](../SKILL.md) | 按任务加载规则与资源，执行检索或维护流程 |

CLI 与 MCP 使用 Python 3.11+ 标准库；检索按本地字段匹配，未使用向量、联网抓取或生成模型。MCP 在本地进程中读取仓库，不要求当前工作目录、不监听 HTTP，也没有托管调用地址。

## 只用浏览能力

将以下入口交给 AI：

```text
https://raw.githubusercontent.com/jsfgmkg95d-source/urban-desire-female-archetypes/main/llms.txt
```

可直接使用这段提示：

```text
读取该库的 llms.txt 和 SKILL.md，遵守事实、解释、现代设计的分层。
我需要一个通过规则掌权、掌握秘密、但害怕退出失控的都市人物机制。
从 catalog.json 或 characters.jsonl 找 3 个候选；
按 card_id 打开对应人物卡和 sources 记录再比较。
列出各候选的机制差异、证据缺口和适合借用的槽位；
不要把 Gold/PASS 当事实认证，不复制原作专有剧情。
```

`llms.txt` 按 [llms.txt 提案](https://llmstxt.org/)组织简短背景和按需链接。它帮助已经到达仓库的 AI 快速定位资料；公开文件与该提案并不保证各家 AI 自动搜索、收录或安装。本库没有提交到第三方技能市场或 MCP 目录。

Raw 链接适合直接读纯文本，GitHub 链接适合人阅读。相对链接要相对当前文件 URL 解析；catalog 中每张卡的 `card` 和 `source_record` 已给出完整 URL。浏览端若无法读取 raw 域名，可从对应 GitHub 文件页读取。

## 克隆后用命令行

```shell
git clone https://github.com/jsfgmkg95d-source/urban-desire-female-archetypes.git
cd urban-desire-female-archetypes
python scripts/archetypes.py search --query "秘密 退出" --limit 3
python scripts/archetypes.py get --id CN-HLM-001
python scripts/archetypes.py list --limit 30 --offset 0
python scripts/archetypes.py rules --name source-rules
```

工具向标准输出返回 UTF-8 JSON，错误时返回非零状态。每个查询结果保留内部等级、`quality_status`、回读链接与使用限制；`get` 返回卡片和来源记录全文。搜索命中只表示与查询字段匹配，不表示事实置信度提高。

返回的 `library_version` 与 `release_tag` 标记实现版本；`github_url` / `raw_url` 是 main 链接，`release_github_url` / `release_raw_url` 是 v0.1.0 链接。它们提供远程定位，不证明本地未提交修改已存在于远程。运行时的 `sha256` 和 `summary_sha256` 按 `raw-local-bytes` 计算，只标识实际读到的本地文件；换行不同时，它们可能与下方清单的规范文本哈希不同。

| 命令 | 参数与范围 |
|---|---|
| `search` | `--query` 1—200 字符；`--limit` 1—20，默认 5；可加 `--tier Gold` 或 `Silver`、`--archetype <ID>`、`--source-category <类别>` |
| `get` | `--id <card_id>`；按稳定 ID 获取当前卡和来源全文 |
| `list` | `--limit` 1—100，默认 30；`--offset` 0—10000；支持同样过滤，`--tier` 也可取 `Reference` |
| `rules` | `--name` 使用下表白名单，避免随意读取路径 |

| `rules --name` / `read_rules(name)` 值 | 文件 |
|---|---|
| `source-rules` | `references/source-rules.md` |
| `quality-gate` | `references/quality-gate.md` |
| `archetype-taxonomy` | `references/archetype-taxonomy.md` |
| `hybridization-rules` | `references/hybridization-rules.md` |
| `visual-language` | `references/visual-language.md` |
| `agents` | `AGENTS.md` |
| `skill` | `SKILL.md` |

`Reference` 记录用于登记与待研究材料，不进入 `search` 推荐。原型与类别的可取值见 [字段契约](../data/archetypes.json)。用脚本绝对路径执行时，它自行定位仓库，可从其他工作目录调用。

## 接入 MCP stdio

在支持启动本地 stdio 进程的客户端中新增服务器。以下是常见 `mcpServers` 配置形状；字段放置位置和添加方式以客户端文档为准：

```json
{
  "mcpServers": {
    "urban-desire-female-archetypes": {
      "command": "python",
      "args": ["/absolute/path/urban-desire-female-archetypes/scripts/mcp-server.py"]
    }
  }
}
```

将 `args` 改为实际绝对路径，Windows 例如 `C:/Libraries/urban-desire-female-archetypes/scripts/mcp-server.py`。`command` 可以使用 Python 可执行文件的绝对路径。整个克隆目录必须保留；配置只引用服务器入口，不会复制卡片或调用远程服务。

| 工具 | 主要参数 | 返回内容 |
|---|---|---|
| `search_archetypes` | `query`、`limit`，可选 `tier`、`archetype`、`source_category` | 匹配候选、命中理由、卡片与来源链接 |
| `get_archetype` | `card_id` | 摘要、卡片与来源记录全文 |
| `list_archetypes` | `limit`、`offset` 与可选过滤 | 分页登记，包含可明确筛选的 Reference |
| `read_rules` | `name`，使用上方白名单 | 当前规则原文 |

本实现支持 `2025-11-25` 与 `2025-06-18` 的初始化协商，UTF-8 换行分隔的 JSON-RPC、工具列表与调用；不声称实现所有 MCP 能力或所有协议版本。工具只读本地受约束的文件。客户端若要求 HTTP 服务器、OAuth 或其他传输，需要另行实现接入层。

## 作为目录式技能使用

仓库根目录就是一个自包含的 Agent Skill：`SKILL.md` 包含名称和触发范围，`agents/openai.yaml` 提供显示名称和默认提示。目录需要一起分发，至少保留 `AGENTS.md`、`references/`、`templates/`、`scripts/`、`data/`、`characters/`、`sources/` 及技能引用的文档；建议保留整个克隆目录。单独复制 `SKILL.md` 会丢失规则和可调用资料。

对于 Codex，按 [官方 Agent Skills 文档](https://developers.openai.com/codex/skills/)把完整目录放到仓库的 `.agents/skills/urban-desire-female-archetypes/` 或用户的 `~/.agents/skills/urban-desire-female-archetypes/`；官方文档也说明支持指向技能目录的符号链接。根据宿主环境选择复制、克隆或链接，并确认宿主能读到全部资源。这里不自动安装到任何用户配置。

显式调用示例：

```text
$urban-desire-female-archetypes
找三个“能调动规则、持有秘密、升级后失去退路”的机制候选，
回读卡片与来源，比较后设计一个原创都市角色。
```

技能保留宿主默认的隐式匹配行为。根目录中的技能文件不会因 GitHub 公开自动出现在每个 AI 的技能列表；需要宿主加载目录或用户提供入口。

## 版本与机器清单

`main` 是维护中的内容，`v0.1.0` 指向首个研究预览版本。需要复现时使用发布标签或核验后的提交号，所有链接与数据保持同一 ref：

```shell
git clone --branch v0.1.0 --depth 1 https://github.com/jsfgmkg95d-source/urban-desire-female-archetypes.git
```

- [library-manifest.json](../data/library-manifest.json)：版本、字段契约版本、计数、能力、入口、权利范围和哈希。
- [catalog.json](../data/catalog.json)：按稳定 ID 登记，每张卡包含人物路径、来源路径、main 与 release URL 和机器摘要定位。
- [characters.jsonl](../data/characters.jsonl)：人工复核的检索摘要，按 `card_id` 关联；catalog 从它与现有卡片路径派生。

manifest 与 catalog 的 `sha256` 基于 UTF-8 文本，将 CRLF 或 CR 规范为 LF 后计算；`hash_basis` 固定为 `utf8-lf-text`，`byte_size` 是同一规范文本的字节数。哈希检查资料字节是否一致，不能核验原著事实、评分理由或第三方许可。llms.txt、manifest 与 catalog 均由同一构建器生成，不能手改：

```shell
python scripts/build-discovery.py
python scripts/build-discovery.py --check
```

## 常见问题

**能直接把全部数据塞给 AI 吗？** 可以读取，但按“清单 → 候选 → 卡片 → 来源”的顺序更节省上下文，也更容易解释具体选择。原作事实归 `FACT`；机制、评分和分类归 `INTERPRETATION`；现代职业、成年年龄与原创组合归 `ADAPTATION`。

**Gold 是否可当作已经核验？** 它是当前内部评估。公开版本仍有定位占位、理由错位与改编接近原作等已知问题，详见 [开源评估](open-source-assessment.md)。`last_verified`、source_id 或 PASS 的存在也不证明本次调用已经读过原著。

**未确认成年的原角色能用成年现代设计解锁视觉层吗？** 不能。原角色的 `adult_status` 与现代 `adult_adaptation_age` 分开；后者只属于明确标注的原创设计。

**能用于商业作品吗？** 自有原创表达和代码按 [许可与署名范围](../COPYRIGHT.md)使用；源作品、现代译本、短摘录和链接页面按 [第三方说明](../THIRD_PARTY_NOTICES.md)保留其权利。生成的新人物仍需重新设计关系、事件和解决方式，内部反克隆通过不等于法律或原创性认证。

**怎么让更多 AI 发现？** 可分享仓库名、README、raw `llms.txt` 和版本链接；GitHub 描述与主题帮助用户搜索。能否被特定搜索引擎或 AI 目录收录由对应服务决定，本库不宣称获得收录或平台认证。
