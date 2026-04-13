---
name: distill
description: Distill a fetched bookmark into structured Obsidian note + Claude Code skill. Use when processing bookmarks with b2k.
---

# Bookmark Distillation Skill

You are distilling a web page into a structured knowledge entry. This is NOT summarization — it is deconstruction that preserves the original texture, opinions, and value.

## When to Use

When orchestrating the `b2k` (bookmark2skill) pipeline:
```
b2k fetch <url> → (YOU distill here) → b2k write-obsidian + b2k write-skill
```

## Two-Phase Pipeline

```
Phase 1 (batch): b2k fetch <url> --save-raw ./b2k-raw    ← 批量抓取，保存原始内容
Phase 2 (AI):    读 b2k-raw/*.md → 蒸馏 → b2k write       ← 逐篇 AI 蒸馏
```

Phase 1 可以自动化批量跑（保底防链接腐烂）。Phase 2 必须由 AI 逐篇完成。

## Process

### Step 1: Fetch the content (Phase 1)

```bash
# 单个 URL — 保存原始内容到 b2k-raw/
b2k fetch <url> --save-raw ./b2k-raw

# 或直接读取已保存的原始内容
cat ./b2k-raw/<slug>.md
```

Read the full output. Do NOT skip or skim.

### Step 2: Think about what you read

Before writing any JSON, answer these questions internally:
- **What is the author's core argument or purpose?**
- **What evidence or examples do they use?**
- **What makes this worth bookmarking?** (not "what is it about" — why did the user save THIS specific page)
- **What would I lose if this page disappeared?**
- **When would I want to reference this in the future?**

### Step 3: Generate the structured JSON

Write to a temp file, then pass to `b2k write-obsidian` and `b2k write-skill`.

Required fields: `url`, `title`, `summary`, `date_processed`

#### title
Rewrite as the core claim or insight — NOT the original title.
- Bad: "An Introduction to System Design"
- Good: "Worse is Better: 实现简单性胜过接口完美性的生存优势"

#### summary (CRITICAL — this is the most important field)
2-4 sentences. Must contain:
1. The core argument or what this page IS
2. The key evidence or method
3. Why it matters or when it's useful

- Bad: "这篇文章讲了系统设计的一些内容。"
- Good: "Richard Gabriel 论证 worse-is-better 哲学——实现简单性比接口完美性更重要，因为它决定了可移植性和扩散速度。通过 Unix/C vs Lisp 的历史对比，说明 50% 正确 + 病毒式传播胜过 90% 正确但无法发布。软件工程史上最有影响力的设计哲学论述之一。"

#### category
Choose from taxonomy or create new. Format: `area/sub` (e.g., `engineering/ai`, `thinking/insights`, `design/game`).

#### layers.distillation

**logic_chain** — Trace the author's reasoning as a chain:
- Bad: `["介绍了一些概念", "给出了一些建议"]`
- Good: `["实现简单 → 易于移植", "易于移植 → 快速扩散", "快速扩散 → 社区改进", "因此: worse is better 是更优的生存策略"]`

**brilliant_quotes** — Keep original words + annotate WHY brilliant:
- Bad: `[{"text": "一句话", "why": "很好"}]`
- Good: `[{"text": "It is slightly better to be simple than correct.", "why": "一句话概括 worse-is-better 核心取舍——直接挑战'正确性不可妥协'的信条"}]`

If no quote is truly brilliant, leave empty. Do NOT force it.

**narrative_craft** — HOW the author writes, not WHAT they write:
- "用两个人的对话具象化抽象的设计哲学"
- "先把观点描述为'显然是坏的'，然后翻转——先抑后扬"

**concrete_examples** — Write out the ACTUAL example, not "the author gave an example":
- Bad: `["作者举了一个操作系统的例子"]`
- Good: `["PC loser-ing 问题: MIT 方案是系统回退并恢复 PC（正确但复杂），Unix 方案是返回错误码让用户重试（简单但复杂度推给用户）"]`

**counterpoints** — What the author acknowledged as limitations, or what you see as blind spots.

**overlooked_details** — Tool names, version numbers, config values, links mentioned in passing. These are the details you'll need in 6 months but won't remember.

#### layers.agent_metadata

**key_claims** — Assertive statements that can be AGREED or DISAGREED with:
- Bad: `["这篇文章讲了设计"]`
- Good: `["实现简单性比接口完美性更重要——因为它决定了软件的可移植性和扩散速度"]`

**taste_signals** — What does bookmarking this reveal about the user's preferences:
- `aesthetic`: writing/design style preferences (e.g., "极简主义", "对立结构叙事")
- `intellectual`: thinking patterns (e.g., "第一性原理", "进化论思维")
- `values`: what matters to them (e.g., "实用主义胜过理想主义", "开源优先")

If unclear, leave arrays empty. Do NOT guess.

**reuse_contexts** — Concrete scenarios where this should be referenced:
- Bad: `[{"situation": "需要参考", "how": "看这篇文章"}]`
- Good: `[{"situation": "讨论是否先发布 MVP 还是追求完美", "how": "引用 worse-is-better: 50% 正确 + 传播胜过 90% 正确无法发布"}]`

**quality_score** — Be honest, not generous:
- `depth`: 1=浅谈 2=概述 3=有深度 4=系统性 5=权威
- `originality`: 1=常见观点 2=有角度 3=新颖 4=独特 5=开创性
- `practicality`: 1=纯理论 2=有启发 3=可参考 4=可直接用 5=即拿即用
- `writing`: 1=粗糙 2=能读 3=清晰 4=有风格 5=精彩

### Step 4: Write outputs

```bash
# Save JSON
cat > /tmp/b2k-distilled.json << 'EOF'
{ ... your JSON ... }
EOF

# Write Obsidian note
b2k write-obsidian --url <url> --data /tmp/b2k-distilled.json --vault-path ./b2k-vault

# Write skill file
b2k write-skill --url <url> --data /tmp/b2k-distilled.json --category <category> --skill-dir ./b2k-skills

# Mark done
b2k mark-done <url> --obsidian-path <path> --skill-path <path>
```

### Step 5: Verify

Read the generated files. Check:
- Does the summary answer "what, evidence, why it matters"?
- Are the key_claims actually assertive (can be agreed/disagreed)?
- Would you find this useful in 6 months with zero memory of the original?

## What NOT to Do

- Do NOT write "这篇文章讲了..." as a summary — that's meta-description, not distillation
- Do NOT force-fill fields — empty is better than garbage
- Do NOT copy the original title as the distilled title
- Do NOT write generic reuse_contexts like "需要参考时"
- Do NOT give everything quality_score 3/3/3/3 — differentiate
- Do NOT skip reading the content — mechanical extraction produces empty shells

## For Pages Without Depth

Some bookmarks are tools, resources, or product pages — not articles. For these:
- summary: What it is + what it's useful for + what makes it unique
- Skip: logic_chain, brilliant_quotes, narrative_craft, counterpoints
- Focus: concrete_examples (what can you DO with it), reuse_contexts, overlooked_details

## Batch Processing

When processing multiple bookmarks:
1. Fetch all first, filter out unreachable
2. Distill ONE at a time — read fully before writing
3. After each: write + mark-done immediately
4. Print progress: `[N/total] title → category`
