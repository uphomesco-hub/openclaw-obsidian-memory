# Testing

This guide verifies both write and read behavior.

## 1. Confirm The Bridge Is Installed

```bash
~/.openclaw/tools/openclaw-obsidian status
```

Expected:

```text
Vault: ...
Markdown notes: ...
Index: .../90-System/openclaw-memory-log.jsonl
```

If you created a shell shim:

```bash
openclaw-obsidian status
```

## 2. Test Capture From Shell

Use a unique keyword:

```bash
openclaw-obsidian capture "save this to Obsidian: shell-test-keyword-123 should be searchable"
```

Expected:

```text
Saved to Obsidian: ...
Type: ...
Title: ...
```

## 3. Test Search From Shell

```bash
openclaw-obsidian search "shell-test-keyword-123"
```

Expected: one result with a path under the vault and an excerpt containing the keyword.

## 4. Test Slash Command From OpenClaw Chat

Send OpenClaw:

```text
/obsidian openclaw-chat-test-keyword-456 should be saved to Obsidian memory
```

Then ask OpenClaw:

```text
what did I save in Obsidian about openclaw-chat-test-keyword-456?
```

Expected: OpenClaw searches the vault and answers from the saved note.

## 5. Test Natural Language Capture

Send OpenClaw:

```text
save this to Obsidian: natural-language-test-keyword-789 should also be saved
```

Then ask:

```text
search my Obsidian memory for natural-language-test-keyword-789
```

Expected: OpenClaw uses the bridge search command and returns the matching saved note.

## 6. Test Typo Support

Both of these should work:

```text
/obsedian typo-command-test-keyword
save this to Obsedian: typo-natural-test-keyword
```

Search:

```bash
openclaw-obsidian search "typo-command-test-keyword"
openclaw-obsidian search "typo-natural-test-keyword"
```

## 7. Inspect The Vault In Obsidian

Open Obsidian and open the vault folder:

```text
~/Documents/Obsidian-AI-Memory
```

You should see notes in folders such as:

```text
00-Inbox/
01-Journal/
02-Projects/
03-Web-Clips/
04-GitHub-Repos/
05-Ideas/
06-Decisions/
```

## 8. Check OpenClaw Memory Wiki

If using OpenClaw's bundled `memory-wiki` plugin:

```bash
openclaw wiki status
openclaw wiki doctor
```

Expected:

```text
Vault: ready
Render mode: obsidian
Wiki doctor: healthy
```

