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

