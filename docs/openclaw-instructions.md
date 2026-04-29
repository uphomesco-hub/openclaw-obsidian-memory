# OpenClaw Instructions For Obsidian Memory

The user's personal Obsidian memory vault is normally:

```text
~/Documents/Obsidian-AI-Memory
```

Use the local bridge:

```bash
~/.openclaw/tools/openclaw-obsidian
```

## Memory Philosophy

Use this vault as recall-based long-term memory, not as a giant prompt.

Do not load the whole vault, all daily notes, or every old decision into normal conversation. Talk naturally from the current chat context. Search Obsidian only when the user asks for memory or when the task clearly depends on prior context.

Working rule:

- current chat = working memory
- Obsidian notes/wiki = long-term memory
- `search`/`query` = recall

Recall from Obsidian when:

- the user says `do you remember`, `what did we decide`, `what did I save`, `from memory`, or `from my Obsidian`
- the user asks about saved notes, links, articles, GitHub repos, journal entries, project context, people, or prior work
- the task depends on a prior preference, decision, repo state, playbook, or project convention
- answering without recall would be a guess about the user's past context

If nothing indicates prior context is needed, do not search just to stuff more memory into the reply.

## Capture Contract

If the user message starts with `/obsidian` or `/obsedian`, treat the rest of the message as memory to save.

Also treat natural phrases as capture requests even without a slash command:

- `save to Obsidian ...`
- `save this to Obsidian ...`
- `save it to Obsidian ...`
- `save to Obsedian ...`
- `add this to Obsidian memory ...`
- `log this to Obsidian ...`
- `remember this in Obsidian ...`

Do not ask where to put it. Run:

```bash
~/.openclaw/tools/openclaw-obsidian capture "<full user text>"
```

If the captured text contains a URL, the bridge automatically tries to crawl the first URL and save readable page text. The user does not need to say "crawl it".

```bash
~/.openclaw/tools/openclaw-obsidian capture "<full user text with URL>"
```

For an explicit URL-only crawl:

```bash
~/.openclaw/tools/openclaw-obsidian crawl "<url>" "<optional user note>"
```

The crawler stores readable page text in the note. It is intentionally bounded by timeout and size limits, so if a site blocks bots or requires login, say that the page could not be crawled and save the URL/note normally. Use `--no-crawl` only when the user explicitly wants URL-only storage.

The bridge decides note type, tags, filename, and folder. It writes plain Markdown into the Obsidian vault and logs captures to:

```text
90-System/openclaw-memory-log.jsonl
```

It also maintains an LLM Wiki layer:

```text
raw/sources/
wiki/sources/
wiki/concepts/
wiki/projects/
wiki/questions/
wiki/reports/
wiki/index.md
wiki/log.md
```

The user should not need to know these commands. Map plain English to them internally:

- "save this", "remember this", "add this to my Obsidian" -> `capture`
- "what do I know about...", "find in my memory", "query my Obsidian" -> `query`
- "organize my wiki", "update the wiki", "compile this into memory" -> use the captured/wiki pages and edit the relevant Markdown pages directly
- "check my memory", "health check the wiki", "find missing links", "find contradictions/orphans" -> `lint`, then explain the report

When a source is captured, the bridge creates a raw source and a wiki source page automatically. OpenClaw should then enrich the wiki if useful: update concept/entity/project pages, add cross-links, and write durable answers into `wiki/syntheses/`.

## Recall Contract

If the user asks about saved notes, past work, links, articles, GitHub repos, project context, journal entries, or says phrases like `do you remember`, `what did I save`, `what was that repo`, `from my Obsidian`, or `from memory`, search the vault before answering:

```bash
~/.openclaw/tools/openclaw-obsidian search "<query>"
```

For broader memory questions, use:

```bash
~/.openclaw/tools/openclaw-obsidian query "<plain English question>"
```

Use the search result paths and excerpts as evidence. If search returns nothing, say the Obsidian vault did not have a matching note.

Prefer saving user-provided memory exactly. Do not rewrite the user's pasted note into a different meaning.

## Summary Contract

If the user asks for a summary of a saved article or URL, search the vault first. If the crawled page text exists, summarize from the extracted text and cite the note path. If only a URL was saved and no crawled text exists, say that the vault has the link but not page contents yet, then offer to crawl it.

If the answer is useful beyond the current chat, file it as a Markdown page under `wiki/syntheses/` and update `wiki/index.md` and `wiki/log.md`.
