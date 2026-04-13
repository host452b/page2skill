# bookmark2skill 设计文档

> **日期:** 2026-04-13
> **状态:** 已批准，待实现

## 概述

bookmark2skill 是一个 Python CLI 工具，将 Chrome 浏览器收藏夹转化为双重本地输出：
1. **Obsidian 笔记**（人类阅读）— 完整的六维知识解构
2. **Claude Code skill 文件**（AI agent 复用）— 紧凑的结构化元数据

工具本身不调用任何 LLM API。它是 AI agent（Claude Code、Codex 等）的下游固定工具，提供原子操作供 agent 编排使用。

## 架构

```
[AI Agent CLI] ←→ [bookmark2skill CLI] ←→ [Chrome Bookmarks / Web / Local Files]
     ↓ (大脑：蒸馏、分类)         ↓ (双手：解析、抓取、写入、跟踪)
```

AI agent 编排工作流：`list → fetch → (agent 蒸馏) → write-obsidian + write-skill → mark-done`

## CLI 命令

| 命令 | 用途 |
|---|---|
| `list --source chrome\|file.html` | 解析书签源，输出 JSON |
| `fetch <url>` | 抓取并清洗页面，输出 Markdown |
| `write-obsidian --url <url> --data <json> [--raw <md>]` | 写 Obsidian 笔记 |
| `write-skill --url <url> --data <json> --category <x/y> [--raw <md>]` | 写 skill 文件 |
| `status` | 查询处理状态 |
| `mark-done <url>` | 标记完成 |
| `mark-failed <url> --reason <text>` | 标记失败 |

## 结构化 JSON Schema

**必填：** `url`, `title`, `date_processed`

**可选字段（均可为 null/空数组/省略）：**

```json
{
  "url": "string (required)",
  "title": "string (required)",
  "date_processed": "ISO8601 (required)",
  "original_title": "string",
  "author": ["string"],
  "date_published": "string",
  "language": "string",
  "category": "string (e.g. engineering/system-design)",

  "layers": {
    "distillation": {
      "logic_chain": ["string"],
      "brilliant_quotes": [{"text": "string", "why": "string"}],
      "narrative_craft": ["string"],
      "concrete_examples": ["string"],
      "counterpoints": ["string"],
      "overlooked_details": ["string"]
    },
    "agent_metadata": {
      "tags": ["string"],
      "content_type": "string",
      "key_claims": ["string"],
      "taste_signals": {
        "aesthetic": ["string"],
        "intellectual": ["string"],
        "values": ["string"]
      },
      "reuse_contexts": [{"situation": "string", "how": "string"}],
      "related_concepts": ["string"],
      "quality_score": {
        "depth": "1-5",
        "originality": "1-5",
        "practicality": "1-5",
        "writing": "1-5"
      }
    }
  }
}
```

## 输出格式

### Obsidian 笔记
- 路径：`{vault_path}/bookmark2skill/{folder}/{title}.md`
- YAML frontmatter + 六维解构正文
- 空字段对应章节省略

### Claude Code Skill
- 路径：`{skill_dir}/{category}/{slug}.md`
- 重 frontmatter（taste_signals, reuse_contexts, quality_score）
- 轻正文（key insights, quotes, examples, when-to-reference）

## Manifest（增量跟踪）

- 路径：`~/.bookmark2skill/manifest.json`
- 每个 URL 一条记录，status: pending → done / failed
- `list` 命令自动检测新增书签，跳过已有（增量识别）

## Taxonomy（分类体系）

- 路径：`~/.bookmark2skill/taxonomy.toml`
- 推荐分类：engineering, thinking, design, writing, product
- AI agent 参考但不受约束，可自由扩展

## 配置

三层覆盖：`config.toml` → 环境变量 → CLI flags

## 依赖

- **核心：** click, httpx, readability-lxml, jinja2, tomli
- **可选：** playwright（JS 重页面抓取）

## 设计原则

1. 工具是双手，AI agent 是大脑
2. 不绑定任何特定 AI agent
3. 解构保存，而非总结
4. Schema 灵活——最少必填，其余可空
5. 分类存储，便于精准复用
6. 一致性为默认（模板），灵活性为逃生舱（raw 模式）
