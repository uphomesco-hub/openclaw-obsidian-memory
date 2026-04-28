# OpenClaw Instructions For Obsidian Memory

The user's personal Obsidian memory vault is normally:

```text
~/Documents/Obsidian-AI-Memory
```

Use the local bridge:

```bash
~/.openclaw/tools/openclaw-obsidian
```

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

The bridge decides note type, tags, filename, and folder. It writes plain Markdown into the Obsidian vault and logs captures to:

```text
90-System/openclaw-memory-log.jsonl
```

## Recall Contract

If the user asks about saved notes, past work, links, articles, GitHub repos, project context, journal entries, or says phrases like `do you remember`, `what did I save`, `what was that repo`, `from my Obsidian`, or `from memory`, search the vault before answering:

```bash
~/.openclaw/tools/openclaw-obsidian search "<query>"
```

Use the search result paths and excerpts as evidence. If search returns nothing, say the Obsidian vault did not have a matching note.

Prefer saving user-provided memory exactly. Do not rewrite the user's pasted note into a different meaning.
