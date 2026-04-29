# OpenClaw Obsidian Memory

Small OpenClaw add-on for using an Obsidian vault as personal AI memory.

It gives OpenClaw two simple abilities:

- Capture: save pasted text, links, articles, GitHub repos, journal notes, ideas, and project notes into an Obsidian vault.
- Recall: search the vault before answering memory-style questions.
- Wiki maintenance: build a persistent LLM-maintained wiki from raw sources, with source pages, concept pages, project pages, `wiki/index.md`, and `wiki/log.md`.

The vault stays normal Markdown. You can open it in Obsidian, sync it, edit it manually, or back it up like any other folder.

## Recall-Based Memory Architecture

This project treats memory more like a human brain than a giant prompt.

The assistant should not load the whole vault, all old chats, or every past decision into every conversation. Normal chat should use small working memory: the current message, the current task, and only the recent context needed to reply naturally.

Long-term memory lives in Obsidian. OpenClaw should recall from it only when memory is actually needed:

- the user asks "do you remember...", "what did we decide...", "what did I save...", or "continue from last time"
- the task depends on a prior project, repo, decision, preference, person, article, saved link, or old note
- the user asks about their own saved knowledge: "what do I know about..."
- the answer would otherwise be based on a guess about past context

In this model:

- current chat = working memory
- raw notes and daily logs = experiences
- curated Markdown/wiki pages = long-term memory
- search/query = recall
- links, tags, and summaries = associations

The goal is not to make an AI that re-sends all context forever. The goal is to make an agent that can talk forward, forget irrelevant details, and deliberately retrieve the right memory when asked or when the task clearly needs it.

## What This Does

When you tell OpenClaw:

```text
/obsidian paste anything here
```

or:

```text
save this to Obsidian: paste anything here
```

the bridge writes a Markdown note into the vault and logs the capture in `90-System/openclaw-memory-log.jsonl`.

It also accepts the common typo:

```text
/obsedian paste anything here
save this to Obsedian: paste anything here
```

## Vault Layout

Default vault:

```text
~/Documents/Obsidian-AI-Memory
```

Folders created by the bridge:

```text
00-Inbox/
01-Journal/
02-Projects/
03-Web-Clips/
04-GitHub-Repos/
05-Ideas/
06-Decisions/
90-System/
raw/
  sources/
  assets/
wiki/
  index.md
  log.md
  AGENTS.md
  sources/
  concepts/
  entities/
  projects/
  syntheses/
  questions/
  reports/
```

`raw/` is the immutable evidence layer. `wiki/` is the LLM-maintained compiled knowledge layer.

## Install

Clone or copy this repo, then:

```bash
./install.sh
```

That installs:

```text
~/.openclaw/tools/openclaw-obsidian.py
~/.openclaw/tools/openclaw-obsidian
```

Optional shell shim:

```bash
ln -sf ~/.openclaw/tools/openclaw-obsidian ~/.npm-global/bin/openclaw-obsidian
```

## Commands

Initialize the vault:

```bash
~/.openclaw/tools/openclaw-obsidian init
```

Capture memory:

```bash
~/.openclaw/tools/openclaw-obsidian capture "/obsidian remember this"
~/.openclaw/tools/openclaw-obsidian capture "save this to Obsidian: remember this"
```

If the captured text contains a URL, the bridge automatically tries to crawl and save readable page text.

Search memory:

```bash
~/.openclaw/tools/openclaw-obsidian search "what did I save about browser automation"
```

Ask a durable question and file it in the wiki:

```bash
~/.openclaw/tools/openclaw-obsidian query "what do I know about browser automation"
```

Health-check the wiki:

```bash
~/.openclaw/tools/openclaw-obsidian lint
```

Crawl and save a webpage:

```bash
~/.openclaw/tools/openclaw-obsidian crawl "https://example.com/article" "why this article matters"
```

Normal URL captures auto-crawl:

```bash
~/.openclaw/tools/openclaw-obsidian capture "save this to Obsidian: https://example.com/article revisit later"
```

Disable crawling for URL-only storage:

```bash
~/.openclaw/tools/openclaw-obsidian capture --no-crawl "save this to Obsidian: https://example.com/article revisit later"
```

Show recent captures:

```bash
~/.openclaw/tools/openclaw-obsidian recent
```

Use another vault:

```bash
OPENCLAW_OBSIDIAN_VAULT="$HOME/Documents/MyVault" ~/.openclaw/tools/openclaw-obsidian capture "/obsidian note"
```

## OpenClaw Instructions

Add the contents of [`docs/openclaw-instructions.md`](docs/openclaw-instructions.md) to your OpenClaw workspace instructions, usually:

```text
~/.openclaw/workspace/AGENTS.md
```

The user-facing workflow is plain English. The commands above are for OpenClaw/agents internally.

## Test The Setup

See [`docs/testing.md`](docs/testing.md) for end-to-end checks.

Quick shell test:

```bash
openclaw-obsidian capture "save this to Obsidian: this is a test memory from OpenClaw"
openclaw-obsidian search "test memory from OpenClaw"
```

Quick OpenClaw chat test:

```text
save this to Obsidian: my favorite test keyword is blue-river-742
```

Then ask:

```text
what did I save in Obsidian about blue-river-742?
```

OpenClaw should search the vault and answer from the saved note.

Webpage auto-crawl test:

```text
save this to Obsidian: https://example.com this page is for testing extraction
```

OpenClaw should save the URL and extracted page text, then later answer questions from that crawled content.

## OpenClaw Memory Wiki

If your OpenClaw version includes the bundled `memory-wiki` plugin, you can point it at the same vault:

```bash
openclaw plugins enable memory-wiki
openclaw config set plugins.entries.memory-wiki.config '{
  "vaultMode": "isolated",
  "vault": {
    "path": "'"$HOME"'/Documents/Obsidian-AI-Memory",
    "renderMode": "obsidian"
  },
  "obsidian": {
    "enabled": true,
    "useOfficialCli": false,
    "vaultName": "Obsidian-AI-Memory",
    "openAfterWrites": false
  },
  "ingest": {
    "autoCompile": true,
    "maxConcurrentJobs": 1,
    "allowUrlIngest": true
  },
  "search": {
    "backend": "local",
    "corpus": "wiki"
  },
  "context": {
    "includeCompiledDigestPrompt": true
  },
  "render": {
    "preserveHumanBlocks": true,
    "createBacklinks": true,
    "createDashboards": true
  }
}' --strict-json
openclaw gateway restart
openclaw wiki status
```

## What Not To Commit

Do not commit a live vault, private notes, logs, state, credentials, browser exports, or machine-specific paths. This repo should contain only the bridge, docs, and examples.

## Graphs, Vectors, And Tokens

See [`docs/memory-model.md`](docs/memory-model.md) for the practical difference between Obsidian graph links, keyword search, and vector search.
