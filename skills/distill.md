---
name: distill
description: Distill fetched bookmarks into structured Obsidian notes + Claude Code skills. Use when processing bookmarks with b2k. Invoke with /distill or when user says "蒸馏", "distill", "处理书签".
---

# Bookmark Distillation Skill

You are distilling web pages into structured knowledge entries. This is NOT summarization — it is deconstruction that preserves the original texture, opinions, conclusions, and value.

## When to Use

When orchestrating the `b2k` (bookmark2skill) pipeline. This skill is the "brain" part — b2k handles the "hands" (fetch, write, track).

## Two-Phase Pipeline

```
Phase 1 (batch, can automate):
  b2k list --source chrome --include-folder "X" | get URLs
  b2k fetch <url> --save-raw ./b2k-raw              # batch fetch, save raw markdown

Phase 2 (AI, must be per-page):
  Read b2k-raw/*.md → Distill → b2k write-obsidian + write-skill → b2k mark-done
```

Phase 1 is the safety net (raw content survives link rot). Phase 2 is where YOU add value.

## Execution Flow

When the user asks to distill bookmarks, follow this exact flow:

### 1. Identify what to process

```bash
# Option A: Specific folder
b2k list --source chrome --include-folder "有意思的" --only-new

# Option B: Check pending
b2k status

# Option C: Already have raw files
ls ./b2k-raw/*.md
```

### 2. Phase 1 — Batch fetch raw content

For each URL, fetch and save raw:

```bash
b2k fetch <url> --save-raw ./b2k-raw
```

If processing many URLs, do this in a loop first. Skip URLs that fail.

### 3. Phase 2 — AI distillation (ONE AT A TIME)

For each raw file:

**A. Read the full content.**

```bash
cat ./b2k-raw/<file>.md
```

DO NOT skip or skim. Read it all.

**B. Think before writing.** Answer internally:
- What is the author's core argument?
- What evidence or examples support it?
- What makes this worth saving? What would be lost if the page disappeared?
- What is the author's CONCLUSION? What do they want the reader to DO or BELIEVE?
- When would I reference this in 6 months?

**C. Generate the structured JSON:**

```bash
cat > /tmp/b2k-distilled.json << 'JSONEOF'
{
  "url": "<url>",
  "title": "<rewritten title — core claim, NOT original title>",
  "summary": "<2-4 sentences: core argument + evidence + why it matters>",
  "date_processed": "<ISO8601>",
  "original_title": "<original page title>",
  "category": "<area/sub from taxonomy>",
  "layers": {
    "distillation": {
      "logic_chain": ["A → B", "B → C", "Therefore D"],
      "brilliant_quotes": [{"text": "exact quote", "why": "why it's brilliant"}],
      "narrative_craft": ["how the author writes, not what they write"],
      "concrete_examples": ["the actual example with details, not 'the author gave an example'"],
      "counterpoints": ["limitations acknowledged or blind spots"],
      "overlooked_details": ["tool names, version numbers, config values, links mentioned in passing"]
    },
    "agent_metadata": {
      "tags": ["tag1", "tag2"],
      "content_type": "technical-article|opinion-essay|tool-repo|game-resource|reference",
      "key_claims": ["assertive statement that can be agreed/disagreed with"],
      "taste_signals": {
        "aesthetic": ["style preferences this bookmark reveals"],
        "intellectual": ["thinking patterns"],
        "values": ["what matters"]
      },
      "reuse_contexts": [{"situation": "specific scenario", "how": "exactly how to use this"}],
      "quality_score": {"depth": 1-5, "originality": 1-5, "practicality": 1-5, "writing": 1-5}
    }
  }
}
JSONEOF
```

**D. Write outputs:**

```bash
b2k write-obsidian --url <url> --data /tmp/b2k-distilled.json --vault-path ./b2k-vault
b2k write-skill --url <url> --data /tmp/b2k-distilled.json --category <cat> --skill-dir ./b2k-skills
b2k mark-done <url> --obsidian-path <path> --skill-path <path>
```

**E. Print progress:**
```
[3/20] ✅ thinking/insights — "Worse is Better: 实现简单性胜过接口完美性"
```

### 4. Report when done

```
蒸馏完成:
  成功: 18/20
  失败: 2 (HTTP 404)
  分类: thinking/insights(7), engineering/ai(5), design/game(4), product/indie(2)
```

## Quality Standards

### title
Rewrite as the core claim — NOT the original title.
- Bad: "An Introduction to System Design"
- Good: "Worse is Better: 实现简单性胜过接口完美性的生存优势"

### summary (THE most important field)
2-4 sentences. MUST contain:
1. The core argument or what this IS
2. Key evidence or method
3. Why it matters — the author's CONCLUSION

- Bad: "这篇文章讲了系统设计的一些内容。"
- Bad: "写这篇文章目的是之前在一篇文章中谈到..." (copying the first paragraph is NOT a summary)
- Good: "Richard Gabriel 论证 worse-is-better 哲学——实现简单性比接口完美性更重要。通过 Unix/C vs Lisp 的对比，说明 50% 正确 + 病毒式传播胜过 90% 正确但无法发布。这是软件工程史上最有影响力的设计哲学论述之一。"

### key_claims
Assertive statements — things that can be AGREED or DISAGREED with:
- Bad: "这篇文章讲了设计"
- Bad: (copying a paragraph verbatim)
- Good: "实现简单性比接口完美性更重要，因为它决定了可移植性和扩散速度"
- Good: "限制程序员发展的主要因素是自我封闭的意识，而非外部环境"

### brilliant_quotes
Keep ORIGINAL words + annotate WHY:
- The "why" must be specific — "很好" is not acceptable
- If no quote is truly brilliant, leave empty

### reuse_contexts
Concrete and specific:
- Bad: {"situation": "需要参考", "how": "看这篇文章"}
- Good: {"situation": "讨论是否先发 MVP 还是追求完美", "how": "引用 worse-is-better: 50% 正确 + 传播胜过无法发布"}

### quality_score
Be honest:
- `depth`: 1=浅谈 2=概述 3=有深度 4=系统性 5=权威
- `originality`: 1=常见观点 2=有角度 3=新颖 4=独特 5=开创性
- `practicality`: 1=纯理论 2=有启发 3=可参考 4=可直接用 5=即拿即用
- `writing`: 1=粗糙 2=能读 3=清晰 4=有风格 5=精彩

## Content Type Adaptation

### Articles / Essays (has depth)
Use ALL distillation fields. Focus on logic_chain, key_claims, brilliant_quotes.

### Tools / Repos / Products
- summary: What it is + what it's useful for + what makes it unique
- Skip: logic_chain, brilliant_quotes, narrative_craft
- Focus: concrete_examples (what can you DO with it), reuse_contexts, overlooked_details

### Game Resources / Art / Visual
- summary: What it is + art style + intended use
- Skip: logic_chain, counterpoints
- Focus: concrete_examples (what does it look like/contain), reuse_contexts

### Resource Collections / Portals
- summary: What's collected + who it's for + what makes it better than alternatives
- Skip: brilliant_quotes, narrative_craft
- Focus: overlooked_details (specific resources listed), reuse_contexts

## Anti-Patterns — NEVER DO THESE

| Anti-pattern | Why it's wrong |
|---|---|
| Copy first paragraph as summary | That's extraction, not distillation |
| Copy paragraph as key_claim | Claims must be assertive opinions, not descriptions |
| All quality_scores 3/3/3/3 | Differentiate — a shallow tool page is NOT depth:3 |
| Generic reuse_context "需要参考时" | Must be a specific scenario |
| Empty taste_signals for articles | Articles always reveal aesthetic/intellectual signals |
| Forcing brilliant_quotes on tool pages | Tools don't have quotes — leave empty |
| Processing without reading | Mechanical extraction produces empty shells |

## Session Workflow

When starting a new distillation session:

1. Check `b2k status` — see what's pending
2. Pick a batch (10-20 pages per session recommended)
3. Phase 1: batch fetch all URLs to b2k-raw/
4. Phase 2: distill one at a time, mark-done after each
5. Report at the end
6. Next session picks up where this one left off (manifest tracks state)
