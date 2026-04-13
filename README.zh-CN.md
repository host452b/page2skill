# bookmark2skill (b2k)

> Chrome 浏览器收藏夹 → Obsidian 本地笔记 + Claude Code skill 文件。

[English](README.md)

**这不是一个 AI 应用。** 它是 AI agent（Claude Code、Codex 等）的下游固定工具——AI agent 是大脑，bookmark2skill 是双手。工具本身不调用任何 LLM API。

```
[AI Agent CLI] ←→ [bookmark2skill CLI] ←→ [Chrome 收藏夹 / 网页 / 本地文件]
     ↓ (大脑：蒸馏、分类)         ↓ (双手：解析、抓取、写入、跟踪)
```

## 为什么需要它

| 问题 | bookmark2skill 怎么解决 |
|---|---|
| **链接会失效** | 抓取 + 本地归档。网站挂了，你的收藏还在。 |
| **摘要丢失质感** | "解构保存，而非总结"——保留逻辑链、精彩原文、叙事手法、具体案例、反对声音、容易忽略的细节。 |
| **AI 不了解你的品味** | `taste_signals` 建模你的审美偏好、思维方式、价值取向，覆盖整个知识库。 |
| **找不到之前存的东西** | `b2k search` 加权关键词匹配所有 skill 文件。分类目录缩小搜索范围。 |
| **处理过程很枯燥** | 增量 Manifest——不重复处理。随时可以中断和恢复。 |

## 快速开始

```bash
# 1. 安装
./build.sh develop

# 2. 配置
mkdir -p ~/.bookmark2skill
cp defaults/config.toml ~/.bookmark2skill/config.toml
cp defaults/taxonomy.toml ~/.bookmark2skill/taxonomy.toml

# 3. 列出所有收藏夹（扫描全部 Chrome Profile）
b2k list --source chrome

# 4. 抓取一个页面
b2k fetch https://example.com/article

# 5. 剩下的交给 AI agent
#    (读内容、蒸馏、写笔记 + skill、标记完成)
```

## 安装

```bash
./build.sh develop    # 开发模式安装（含测试依赖）
# 或
pip install .         # 生产安装
```

可选：Playwright 支持（JS 重页面）：

```bash
pip install ".[browser]"
```

### 构建命令

```bash
./build.sh develop    # 开发模式安装
./build.sh install    # 生产安装
./build.sh test       # 运行 74 个测试
./build.sh dist       # 构建 sdist + wheel
./build.sh check      # 编译检查 + 测试
./build.sh clean      # 清理构建产物
```

## 配置

```bash
mkdir -p ~/.bookmark2skill
cp defaults/config.toml ~/.bookmark2skill/config.toml
cp defaults/taxonomy.toml ~/.bookmark2skill/taxonomy.toml
```

编辑 `~/.bookmark2skill/config.toml`：

```toml
[paths]
vault_path = "/你的/obsidian/vault/路径"
skill_dir = "/你的/skill/输出/路径"
```

**配置优先级：** `config.toml` < `BOOKMARK2SKILL_*` 环境变量 < 命令行参数

**文件说明：**

| 文件 | 位置 | 用途 |
|---|---|---|
| `config.toml` | `~/.bookmark2skill/` | 路径和设置 |
| `taxonomy.toml` | `~/.bookmark2skill/` | 推荐的 skill 分类体系 |
| `manifest.json` | `~/.bookmark2skill/` | 处理状态跟踪（自动创建） |
| `manifest.json.bak` | `~/.bookmark2skill/` | 每次写入前自动备份 |

## 工作流

AI agent 编排以下流程（人类也可以手动执行）。`b2k` 是 `bookmark2skill` 的缩写别名：

```
┌─────────────┐    ┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐
│  b2k list   │ →  │  b2k fetch  │ →  │  AI agent    │ →  │  b2k write-  │ →  │ b2k mark-  │
│  --source   │    │  <url>      │    │  蒸馏内容     │    │  obsidian +  │    │ done <url> │
│  chrome     │    │             │    │              │    │  write-skill │    │            │
└─────────────┘    └─────────────┘    └──────────────┘    └──────────────┘    └────────────┘
   解析 &              抓取 &            生成结构化           渲染到本地           更新
   注册到 manifest      清洗页面           JSON                文件              manifest
```

### 逐步说明

```bash
# 1. 解析收藏夹，注册新 URL 到 manifest（扫描所有 Chrome Profile）
b2k list --source chrome

# 2. 查看待处理状态
b2k status
# → {"pending": 15, "done": 42, "failed": 3, "total": 60}

# 3. 抓取单个页面（自动选择最佳方式）
b2k fetch https://example.com/article > /tmp/raw.md

# 4. AI agent 阅读 raw.md，生成结构化 JSON
#    （完整 schema 见 docs/agent-guide.md）

# 5. 写入 Obsidian 笔记（人类阅读）
b2k write-obsidian \
  --url https://example.com/article \
  --data /tmp/distilled.json
# → {"path": "./bookmark2skill/article-title.md"}

# 6. 写入 skill 文件（AI agent 复用，按类别存储）
b2k write-skill \
  --url https://example.com/article \
  --data /tmp/distilled.json \
  --category engineering/system-design
# → {"path": "./engineering/system-design/article-title.md"}

# 7. 标记完成
b2k mark-done https://example.com/article \
  --obsidian-path ./bookmark2skill/article-title.md \
  --skill-path ./engineering/system-design/article-title.md
```

抓取失败时：

```bash
b2k mark-failed https://example.com/dead --reason "HTTP 404"
```

### 过滤收藏夹

```bash
# 只处理特定文件夹中的书签
b2k list --source chrome --include-folder "正在学的"

# 跳过某些文件夹
b2k list --source chrome --exclude-folder "Work" --exclude-folder "Personal"

# 组合：先 include，再从中 exclude
b2k list --source chrome --include-folder "Tech" --exclude-folder "Archive"

# 只显示新增（未处理过的）书签
b2k list --source chrome --only-new
```

### 搜索 skill

```bash
# 在所有生成的 skill 文件中搜索
b2k search "系统设计" --skill-dir ./skills

# 加权匹配：name(5) > description(4) > tags(3) = key_claims(3) > body(1)
b2k search "simplicity" --limit 5
```

## 命令一览

| 命令 | 作用 | 输入 | 输出 |
|---|---|---|---|
| `list` | 解析书签源，注册新 URL | `--source chrome` 或 `.html` 文件 | JSON 数组 → stdout |
| `fetch` | 抓取并清洗单个页面 | URL | Markdown → stdout |
| `write-obsidian` | 渲染结构化 JSON 为 Obsidian 笔记 | `--data` JSON 或 `--raw` MD | 写文件，路径 → stdout |
| `write-skill` | 渲染结构化 JSON 为 skill 文件 | `--data` JSON + `--category` | 写文件，路径 → stdout |
| `status` | 查询 manifest 处理状态 | — | JSON 计数 → stdout |
| `mark-done` | 标记 URL 为已完成 | URL + 输出路径 | 更新 manifest |
| `mark-failed` | 标记 URL 为失败 | URL + 原因 | 更新 manifest |
| `search` | 搜索 skill 文件 | 关键词 | JSON 结果 → stdout |

执行 `b2k <command> --help` 查看详细参数说明和使用示例。

## 书签输入源

| 来源 | 用法 | 说明 |
|---|---|---|
| Chrome（所有 Profile） | `--source chrome` | 自动扫描所有 Chrome Profile，合并去重 |
| HTML 导出文件 | `--source bookmarks.html` | Netscape 格式，支持所有浏览器导出 |
| Chrome JSON 文件 | `--source /path/to/Bookmarks` | 直接指定单个 Chrome JSON 文件 |

## 输出格式

### Obsidian 笔记（人类阅读）

写入 `{vault-path}/bookmark2skill/{folder}/{slug}.md`：

```yaml
---
url: "https://example.com/article"
original_title: "原文标题"
author: ["作者"]
date_processed: 2026-04-13T12:00:00Z
tags: ["system-design", "simplicity"]
---

# 蒸馏后的标题（核心主张，而非原标题）

## 摘要
2-4 句话概括...

## 逻辑推导链
- A → B → 结论

## 精彩表达
> "原文精彩句子" — *为什么精彩*

## 叙事手法 / 具体案例与数据 / 反对声音与局限性 / 容易忽略的细节
（空章节自动跳过）
```

### Claude Code Skill（AI agent 复用）

写入 `{skill-dir}/{category}/{slug}.md`：

```yaml
---
name: "蒸馏标题"
description: "一句话描述，用于 AI agent 判断相关性"
url: "https://example.com/article"
category: "engineering/system-design"
tags: ["system-design", "simplicity"]
key_claims:
  - "可以被同意或反对的核心主张"
taste_signals:
  aesthetic: ["极简主义", "清晰"]
  intellectual: ["第一性原理", "经验主义"]
  values: ["反复杂性", "实用主义"]
reuse_contexts:
  - situation: "做架构决策时"
    how: "用作支持简单方案的论据"
quality_score:
  depth: 4
  originality: 3
  practicality: 5
  writing: 4
---

## 摘要 / Key Insights / 精彩金句 / 具体案例 / 适用场景
```

## 三层抓取策略

```
第 1 层：httpx + readability       快速，适合静态页面（~80% 的文章）
  ↓ 内容 < 200 字符
第 2 层：Jina Reader API           JS 渲染页面，零本地依赖
  ↓ Jina 失败
第 3 层：Playwright                本地无头 Chrome（可选依赖）
```

强制指定：`b2k fetch <url> --renderer direct|jina|playwright`

## 分类体系

默认分类见 `~/.bookmark2skill/taxonomy.toml`：

| 类别 | 子类别 |
|---|---|
| `engineering/` | system-design, frontend, backend, devops, testing, performance, security |
| `thinking/` | mental-models, decision-making, problem-solving, first-principles, cognitive-biases |
| `design/` | ui-ux, visual, interaction, typography, accessibility |
| `writing/` | technical, narrative, persuasion, clarity, editing |
| `product/` | strategy, user-research, growth, metrics, prioritization |
| `culture/` | leadership, collaboration, hiring, remote-work |

AI agent 可以遵循现有分类，也可以自由创建新类别。Taxonomy 是指导，不是约束。

## 结构化 JSON Schema

AI agent 蒸馏后产出此 JSON。必填字段：`url`、`title`、`summary`、`date_processed`。其余均可选。

```json
{
  "url": "https://example.com/article",
  "title": "核心主张（不是原标题）",
  "summary": "2-4 句话：讲了什么、关键证据、为什么重要。",
  "date_processed": "2026-04-13T12:00:00Z",
  "category": "engineering/system-design",
  "layers": {
    "distillation": {
      "logic_chain": ["A → B", "B → C"],
      "brilliant_quotes": [{"text": "原文金句", "why": "为什么精彩"}],
      "narrative_craft": ["叙事手法观察"],
      "concrete_examples": ["具体案例"],
      "counterpoints": ["局限性或反对观点"],
      "overlooked_details": ["工具名、配置项、版本号"]
    },
    "agent_metadata": {
      "tags": ["标签1", "标签2"],
      "key_claims": ["可以被同意或反对的主张"],
      "taste_signals": {
        "aesthetic": ["极简主义"],
        "intellectual": ["第一性原理"],
        "values": ["实用主义"]
      },
      "reuse_contexts": [{"situation": "什么时候用", "how": "怎么用"}],
      "quality_score": {"depth": 4, "originality": 3, "practicality": 5, "writing": 4}
    }
  }
}
```

完整 schema 文档：[`docs/agent-guide.md`](docs/agent-guide.md)

## 安全

- **路径穿越防护** — `--folder` 和 `--category` 拒绝 `../` 逃逸
- **YAML 注入防护** — 所有用户数据通过 `tojson` 转义
- **SSRF 防护** — 仅接受 `http://` 和 `https://` URL
- **Manifest 自动备份** — 每次写入前自动生成 `.json.bak`
- **无密钥泄露** — `.gitignore` 覆盖 manifest、.env、IDE 文件

## 给 AI Agent 的说明

详见 [`docs/agent-guide.md`](docs/agent-guide.md)：
- 完整工作流编排指南
- 结构化 JSON Schema（所有字段说明）
- 蒸馏指南：摘要（必填）+ 六维解构
- Skill 消费最佳实践：发现、相关性匹配、品味聚合
- 批量处理策略和错误恢复

## 技术栈

| 组件 | 技术 | 用途 |
|---|---|---|
| CLI 框架 | click | 子命令、选项、帮助文本 |
| HTTP 客户端 | httpx | 三层网页抓取 |
| 内容提取 | readability-lxml | HTML → 文章正文 |
| JS 渲染 | Jina Reader API | 远程浏览器渲染（第 2 层） |
| JS 渲染 | Playwright（可选） | 本地无头 Chrome（第 3 层） |
| 模板 | Jinja2 | Obsidian + skill 输出渲染 |
| 配置 | tomli | TOML 配置解析 |
| 语言 | Python 3.10+ | — |

## 许可证

MIT
