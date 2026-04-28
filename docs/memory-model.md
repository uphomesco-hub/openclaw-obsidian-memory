# Memory Model

Obsidian memory works well for AI because it gives the AI a durable, readable, searchable memory store. It is not automatically magic vector memory.

## Obsidian Graph

Obsidian's graph comes from Markdown structure:

- folders
- tags
- frontmatter
- `[[wikilinks]]`
- backlinks

This is useful because it creates human-readable relationships. It helps AI too, because related notes can be discovered by filenames, tags, and links.

But the graph is not the same thing as a vector database.

## Keyword Search

This bridge currently includes local keyword search over Markdown notes.

Pros:

- dependency-free
- fast enough for normal vaults
- transparent results
- low token usage because only matching excerpts are returned

Limit:

- it works best when the query shares words with the saved note

## Vector Search

Vector search means notes are embedded into numeric vectors. Then the system can find semantic matches even when the exact words differ.

Example:

```text
Query: browser automation tool
Saved note: repo for agents controlling webpages
```

A vector index is more likely to connect those two.

Vector search usually needs an embedding model and a local/vector database such as LanceDB, Chroma, SQLite vector extensions, or a managed vector store.

## Token Savings

The token savings come from retrieval, not from Obsidian alone.

Bad pattern:

```text
Load the whole vault into the prompt.
```

Better pattern:

```text
Search the vault.
Return 5-10 relevant snippets.
Answer using only those snippets.
```

This uses far fewer tokens and gives better answers because the model sees focused context instead of thousands of unrelated notes.

## Best Practical Setup

Start with:

- plain Markdown vault
- structured folders
- tags/frontmatter
- capture command
- keyword search
- OpenClaw instruction to search before answering memory questions

Upgrade later with:

- embeddings
- vector index
- automatic note linking
- daily/weekly summaries
- project-level memory pages

## LLM Wiki Layer

The bridge now supports the LLM Wiki pattern:

- `raw/sources/` stores immutable captured evidence.
- `wiki/sources/` stores source summaries and key terms.
- `wiki/concepts/`, `wiki/entities/`, and `wiki/projects/` store compiled knowledge.
- `wiki/questions/` stores durable questions and retrieved context.
- `wiki/syntheses/` is where OpenClaw should file useful answers.
- `wiki/reports/` stores health checks.
- `wiki/index.md` catalogs the wiki.
- `wiki/log.md` records what happened over time.

The important UX point is that the human does not need to say "ingest", "compile", or "lint". OpenClaw maps plain English onto those maintenance actions.

## Crawled Webpages

When a URL is only saved as a link, the AI can remember that the link exists but may not know what the page said.

When the bridge sees a URL in an Obsidian capture, it tries to crawl the page and stores readable extracted text in the vault. Then OpenClaw can search and summarize that content later without re-fetching the website.

This improves context, but it still has limits:

- login-only pages may not be accessible
- some sites block crawlers
- JavaScript-heavy pages may expose little HTML text
- very large pages are truncated by size limits

For important pages, crawling plus a short user note is better than saving the URL alone.
