# CHANGELOG

## [Unreleased] — 2026-04-13 设计阶段

### 项目定位与调性

**bookmark2skill 是什么：** 一个 Python CLI 工具，把 Chrome 浏览器收藏夹转化为双重输出——Obsidian 本地笔记（人类阅读）和 Claude Code skill 文件（AI agent 复用）。

**bookmark2skill 不是什么：** 不是一个 AI 应用，不调用任何 LLM API。它是 AI agent 的下游固定工具——AI agent 是大脑，bookmark2skill 是双手。

**为什么做这个：**
1. **防止链接腐烂。** 收藏夹里的链接随时可能失效。本地归档是唯一可靠的保底。
2. **知识不是"收藏了什么"，是"为什么收藏它"。** 普通收藏夹只有 URL 和标题。bookmark2skill 通过 AI 蒸馏，提取逻辑链、精彩原文、叙事手法、反对声音、容易忽略的细节——保留原文的质感，而非压缩成无味的摘要。
3. **让 AI agent 理解你的品味。** 通过 `taste_signals`（审美偏好、思维方式、价值取向），AI agent 不仅知道你收藏了什么，还能推断你为什么收藏——你的判断力和偏好会随着知识库增长而被越来越精准地建模。
4. **增量处理，不重复劳动。** Manifest 跟踪哪些书签已经处理过，哪些是新增的，哪些失败了。

---

### 核心设计决策与理由

#### 1. 工具不绑定任何特定 AI agent

**决策：** bookmark2skill 是独立 CLI，不依赖 Claude Code、Codex 或任何特定 AI 工具。

**为什么：** AI agent 生态在快速变化。今天用 Claude Code，明天可能换 Codex 或其他工具。工具应该提供原子操作，让任何 AI agent 都能编排使用。绑定 = 技术债。

#### 2. 工具不调用 LLM API

**决策：** 蒸馏工作由 AI agent 完成，不由工具完成。

**为什么：** 用户通常已经在 AI agent CLI 环境里工作。让 AI agent 自己做蒸馏，意味着：不需要额外的 API key 配置、不需要管理 token 成本、可以利用 agent 的上下文理解能力、蒸馏质量随 agent 能力提升自动提升。工具只需要告诉 agent 怎么用自己（通过 agent-guide.md）。

#### 3. Hybrid 模式：模板默认 + Raw 覆盖

**决策：** `write-obsidian` 和 `write-skill` 默认使用内置 Jinja2 模板渲染结构化 JSON 数据，但支持 `--raw` 模式直接写入原始 markdown。

**为什么：** 模板保证输出一致性（不同 agent 产出格式统一），raw 模式留出灵活性（特殊情况 agent 可以完全控制输出）。一致性是默认，灵活性是逃生舱。

#### 4. 双书签源：Chrome JSON + HTML 导入

**决策：** 自动检测 Chrome 本地 JSON 书签文件，同时支持导入 HTML 书签文件。

**为什么：** Chrome JSON 是最直接的方式（无需手动导出），但 HTML 导入支持跨浏览器、跨机器场景。两者都支持，覆盖所有情况。

#### 5. 分层抓取策略

**决策：** 先用 httpx + readability-lxml（轻量快速），失败时回退到 Playwright（完整浏览器渲染）。

**为什么：** 80% 的文章是静态内容，不需要浏览器渲染。Playwright 是重型依赖，只在必要时启用。快的先来，重的兜底。

#### 6. Schema 灵活性：最少必填，其余可空

**决策：** 只有 `url`、`title`、`date_processed` 是必填。所有其他字段允许为 null、空数组或省略。

**为什么：** 真实数据是混乱的。不是每篇文章都有明确的反对声音、清晰的品味信号或单一作者。强制填值会产生低质量数据。模板优雅地跳过空字段，而不是渲染空白占位符。

#### 7. Skill 分类存储（Triage）

**决策：** Skill 文件按类别存储到子目录（如 `engineering/system-design/`、`thinking/mental-models/`）。工具附带 `taxonomy.toml` 作为推荐分类参考，AI agent 可以遵循或自创新类别。

**为什么：** 扁平目录在规模增长后对 AI agent 不友好。分类目录让 agent 能快速缩小搜索范围，精准复用相关经验。taxonomy 是指导而非约束——知识库会有机生长出新分类。

#### 8. "解构保存"而非"总结"

**决策：** 蒸馏层不做摘要。做六维解构：逻辑推导链、精彩原文（带为什么精彩的标注）、叙事手法分析、具体案例与数据、反对声音与局限性、容易忽略的细节。

**为什么：** 总结会把文章压成一坨无味的要点。解构保留了每个零件的原始质感——未来你需要的可能不是"核心观点"，而是文章里顺口提到的一个配置参数、一个边缘案例、甚至是评论区某个反对意见。你今天不知道明天需要什么。

#### 9. taste_signals 的意义

**决策：** AI agent 元数据层包含 `taste_signals`（aesthetic、intellectual、values），每个字段是数组。

**为什么：** 收藏 200 篇文章本身没有价值。价值在于从中归纳出："这个人倾向于实用主义的技术方案"、"这个人喜欢用第一性原理分析问题"、"这个人欣赏简洁有力的写作风格"。taste_signals 是这种归纳的结构化起点。久而久之，agent 对你的品味理解会越来越精准。

---

### 约束

- **Python 3.10+**
- **核心依赖最小化：** click, httpx, readability-lxml, jinja2, tomli
- **Playwright 为可选依赖：** `pip install bookmark2skill[browser]`
- **不写数据库，只用 JSON 文件（manifest）**
- **Obsidian 兼容：** 输出必须是标准 Markdown + YAML frontmatter，不依赖任何 Obsidian 插件
- **所有输出 UTF-8 编码**
- **CLI 输出对 AI agent 友好：** 结构化输出用 JSON（可加 `--format json` flag），人类可读用默认文本格式

---

### CLI 命令一览

| 命令 | 用途 | 输入 | 输出 |
|---|---|---|---|
| `list` | 解析书签源 | `--source chrome` 或 `--source file.html` | JSON 数组 |
| `fetch <url>` | 抓取并清洗单个页面 | URL | 干净的 Markdown (stdout) |
| `write-obsidian` | 写 Obsidian 笔记 | `--url --data file.json` 或 `--raw file.md` | .md 文件 |
| `write-skill` | 写 skill 文件 | `--url --data file.json --category x/y` 或 `--raw file.md` | .md 文件 |
| `status` | 查询处理状态 | (无) | JSON 摘要 |
| `mark-done <url>` | 标记完成 | URL | 更新 manifest |
| `mark-failed <url>` | 标记失败 | URL + `--reason` | 更新 manifest |

### 配置层级

1. `~/.bookmark2skill/config.toml` — 持久默认值
2. `BOOKMARK2SKILL_*` 环境变量 — 中间层覆盖
3. CLI flags (`--vault-path`, `--skill-dir`, etc.) — 最高优先级

### 结构化数据 Schema（AI agent 填充）

**必填：** `url`, `title`, `date_processed`

**可选（均可为 null/空数组/省略）：**
- `original_title`, `author[]`, `date_published`, `language`, `category`
- `layers.distillation`: `logic_chain[]`, `brilliant_quotes[{text, why}]`, `narrative_craft[]`, `concrete_examples[]`, `counterpoints[]`, `overlooked_details[]`
- `layers.agent_metadata`: `tags[]`, `content_type`, `key_claims[]`, `taste_signals{aesthetic[], intellectual[], values[]}`, `reuse_contexts[{situation, how}]`, `related_concepts[]`, `quality_score{depth, originality, practicality, writing}`

### 输出格式

**Obsidian 笔记** → `{vault_path}/bookmark2skill/{folder}/{title}.md`
- 完整、保留所有质感、六维解构、人类友好
- 空字段对应的章节直接省略

**Claude Code Skill** → `{skill_dir}/{category}/{slug}.md`
- 紧凑、frontmatter 为主、优化 AI agent 检索和相关性匹配
- 包含 reuse_contexts 指导 agent 何时引用

### Manifest

路径：`~/.bookmark2skill/manifest.json`
- 每个 URL 一条记录：status (pending/done/failed), timestamps, output paths
- `list` 命令自动将新书签标记为 pending，跳过已存在的 URL（增量检测）

### Taxonomy

路径：`~/.bookmark2skill/taxonomy.toml`
- 推荐分类体系，AI agent 作为参考
- 不是硬约束——agent 可自由创建新类别
- 初始类别：engineering, thinking, design, writing, product
