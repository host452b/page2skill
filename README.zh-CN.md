# bookmark2skill

[English](README.md)

Chrome 浏览器收藏夹 → Obsidian 本地笔记 + Claude Code skill 文件。

**这不是一个 AI 应用。** 它是 AI agent（Claude Code、Codex 等）的下游固定工具——AI agent 是大脑，bookmark2skill 是双手。工具本身不调用任何 LLM API。

## 为什么需要它

1. **防止链接腐烂** — 收藏夹里的链接随时可能失效，本地归档是唯一可靠的保底
2. **解构保存，而非总结** — 提取逻辑链、精彩原文、叙事手法、反对声音、容易忽略的细节，保留原文质感
3. **让 AI agent 理解你的品味** — 通过 `taste_signals` 建模你的审美偏好、思维方式、价值取向
4. **AI 摘要** — 每篇内容必须生成 2-4 句摘要，作为知识库的快速入口
5. **增量处理** — Manifest 跟踪哪些书签已处理、哪些新增、哪些失败

## 安装

```bash
pip install -e .
```

可选：安装 Playwright 支持（JS 重页面抓取）：

```bash
pip install -e ".[browser]"
```

## 配置

首次使用前，创建配置文件：

```bash
mkdir -p ~/.bookmark2skill
cp defaults/config.toml ~/.bookmark2skill/config.toml
cp defaults/taxonomy.toml ~/.bookmark2skill/taxonomy.toml
```

编辑 `~/.bookmark2skill/config.toml`，设置：

```toml
[paths]
vault_path = "/你的/obsidian/vault/路径"
skill_dir = "/你的/skill/输出/路径"
```

配置优先级：`config.toml` < `BOOKMARK2SKILL_*` 环境变量 < 命令行参数

## 工作流

AI agent 编排以下流程（人类也可以手动执行）。`b2k` 是 `bookmark2skill` 的缩写别名：

```bash
# 1. 解析收藏夹，注册新 URL 到 manifest
b2k list --source chrome

# 2. 查看待处理状态
bookmark2skill status

# 3. 抓取单个页面内容
bookmark2skill fetch https://example.com/article > /tmp/raw.md

# 4. AI agent 阅读 raw.md，生成结构化 JSON（见 docs/agent-guide.md）

# 5. 写入 Obsidian 笔记
bookmark2skill write-obsidian \
  --url https://example.com/article \
  --data /tmp/distilled.json \
  --vault-path /你的/vault

# 6. 写入 skill 文件（按类别分目录存储）
bookmark2skill write-skill \
  --url https://example.com/article \
  --data /tmp/distilled.json \
  --category engineering/system-design \
  --skill-dir /你的/skills

# 7. 标记完成
bookmark2skill mark-done https://example.com/article \
  --obsidian-path /vault/bookmark2skill/article.md \
  --skill-path /skills/engineering/system-design/article.md
```

抓取失败时：

```bash
bookmark2skill mark-failed https://example.com/dead --reason "HTTP 404"
```

## 命令一览

| 命令 | 作用 | 输出 |
|---|---|---|
| `list` | 解析书签源，注册新 URL 到 manifest | JSON 数组 → stdout |
| `fetch` | 抓取并清洗单个页面 | Markdown → stdout |
| `write-obsidian` | 渲染结构化 JSON 为 Obsidian 笔记 | 写文件，路径 → stdout |
| `write-skill` | 渲染结构化 JSON 为 skill 文件 | 写文件，路径 → stdout |
| `status` | 查询 manifest 处理状态 | JSON 计数 → stdout |
| `mark-done` | 标记 URL 为已完成 | 更新 manifest |
| `mark-failed` | 标记 URL 为失败 | 更新 manifest |

每个命令支持 `--help` 查看详细参数说明。

## 书签输入源

- **Chrome 本地 JSON** — `--source chrome`，自动检测 `~/Library/Application Support/Google/Chrome/Default/Bookmarks`
- **HTML 导出文件** — `--source bookmarks.html`，支持所有浏览器导出的 Netscape 格式

## 输出格式

### Obsidian 笔记（人类阅读）

写入 `{vault_path}/bookmark2skill/{folder}/{slug}.md`，包含：
- YAML frontmatter（url, author, tags, dates）
- 六维解构正文：逻辑推导链、精彩表达、叙事手法、具体案例、反对声音、容易忽略的细节
- 空字段自动跳过

### Claude Code Skill（AI agent 复用）

写入 `{skill_dir}/{category}/{slug}.md`，包含：
- 重 frontmatter：taste_signals, reuse_contexts, quality_score, key_claims
- 轻正文：关键洞察、金句、案例、适用场景
- 按 taxonomy 分类存储，便于精准检索

## 分类体系

默认分类见 `~/.bookmark2skill/taxonomy.toml`：

- `engineering/` — 系统设计、前端、后端、DevOps
- `thinking/` — 心智模型、决策、问题解决
- `design/` — UI/UX、视觉、交互
- `writing/` — 技术写作、叙事、说服力
- `product/` — 产品策略、用户研究、增长

AI agent 可以遵循现有分类，也可以自由创建新类别。

## 给 AI Agent 的说明

详见 [`docs/agent-guide.md`](docs/agent-guide.md)，包含：
- 完整工作流编排指南
- 结构化 JSON Schema（所有字段说明）
- 蒸馏指南（"解构保存"六维度）
- Skill 消费最佳实践

## 技术栈

- Python 3.10+
- click（CLI）、httpx（HTTP）、readability-lxml（内容提取）、jinja2（模板）、tomli（TOML 配置）
- Playwright（可选，JS 重页面）
