#!/usr/bin/env python3
"""
OpenClaw -> Obsidian memory bridge.

This intentionally stays dependency-free. The vault remains normal Markdown
that Obsidian can open, while OpenClaw gets stable capture and search commands.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
from html.parser import HTMLParser
import json
import os
import re
import sys
import textwrap
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable


DEFAULT_VAULT = Path.home() / "Documents" / "Obsidian-AI-Memory"
SYSTEM_DIR = "90-System"
INDEX_FILE = "openclaw-memory-log.jsonl"
MAX_FETCH_BYTES = 2_000_000
MAX_EXTRACTED_CHARS = 80_000

TYPE_DIRS = {
    "journal": "01-Journal",
    "project": "02-Projects",
    "web": "03-Web-Clips",
    "github": "04-GitHub-Repos",
    "idea": "05-Ideas",
    "decision": "06-Decisions",
    "inbox": "00-Inbox",
}

PROJECT_KEYWORDS = {
    "uphomes": ["uphomes", "broker", "rental", "property", "kharadi", "pune"],
    "openclaw": ["openclaw", "open claw", "telegram", "gateway", "launchd"],
    "codex": ["codex", "claude", "claudecode", "claude code", "repo", "commit", "build"],
    "venomhunt": ["venomhunt", "jaipur", "fiverr", "design"],
    "vision-voice-agent": ["vision voice", "repair assistant", "gemini", "hud"],
    "teenpatti": ["teenpatti", "teen patti", "peerjs"],
}


def vault_path() -> Path:
    return Path(os.environ.get("OPENCLAW_OBSIDIAN_VAULT", str(DEFAULT_VAULT))).expanduser()


def now_local() -> dt.datetime:
    return dt.datetime.now().astimezone()


def iso_now() -> str:
    return now_local().isoformat(timespec="seconds")


def today() -> str:
    return now_local().date().isoformat()


def ensure_vault(vault: Path) -> None:
    for rel in [
        ".obsidian",
        "00-Inbox",
        "01-Journal",
        "02-Projects",
        "03-Web-Clips",
        "04-GitHub-Repos",
        "05-Ideas",
        "06-Decisions",
        "90-System",
    ]:
        (vault / rel).mkdir(parents=True, exist_ok=True)
    index = vault / SYSTEM_DIR / INDEX_FILE
    index.touch(exist_ok=True)


def slugify(value: str, fallback: str = "note") -> str:
    value = value.lower()
    value = re.sub(r"https?://", "", value)
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return (value[:80].strip("-") or fallback)


def yaml_scalar(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def yaml_list(values: Iterable[str]) -> str:
    clean = [v for v in values if v]
    if not clean:
        return "[]"
    return "[" + ", ".join(yaml_scalar(v) for v in clean) + "]"


def extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\s<>)\\\"]+", text)


class ReadableHTMLParser(HTMLParser):
    SKIP_TAGS = {"script", "style", "noscript", "svg", "canvas", "iframe", "template"}
    BLOCK_TAGS = {
        "article",
        "aside",
        "blockquote",
        "br",
        "dd",
        "div",
        "dl",
        "dt",
        "figcaption",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.meta_description: str | None = None
        self.text_parts: list[str] = []
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr_map = {key.lower(): value or "" for key, value in attrs}
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            name = attr_map.get("name", "").lower()
            prop = attr_map.get("property", "").lower()
            if name == "description" or prop == "og:description":
                content = attr_map.get("content", "").strip()
                if content and not self.meta_description:
                    self.meta_description = html.unescape(content)
        if tag in self.BLOCK_TAGS and self._skip_depth == 0:
            self.text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
            return
        if tag == "title":
            self._in_title = False
        if tag in self.BLOCK_TAGS and self._skip_depth == 0:
            self.text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        cleaned = re.sub(r"\s+", " ", data).strip()
        if not cleaned:
            return
        if self._in_title:
            self.title_parts.append(cleaned)
            return
        self.text_parts.append(cleaned)
        self.text_parts.append(" ")

    @property
    def title(self) -> str | None:
        title = re.sub(r"\s+", " ", " ".join(self.title_parts)).strip()
        return title or None

    @property
    def readable_text(self) -> str:
        raw = "".join(self.text_parts)
        lines = []
        for line in raw.splitlines():
            compact = re.sub(r"\s+", " ", line).strip()
            if compact:
                lines.append(compact)
        return "\n\n".join(lines)


def fetch_url(url: str, timeout: int = 20, max_bytes: int = MAX_FETCH_BYTES) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "openclaw-obsidian-memory/1.0 (+https://github.com/uphomesco-hub/openclaw-obsidian-memory)",
            "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            raw = response.read(max_bytes + 1)
            truncated = len(raw) > max_bytes
            raw = raw[:max_bytes]
            charset = response.headers.get_content_charset() or "utf-8"
            decoded = raw.decode(charset, errors="replace")
            status = getattr(response, "status", None)
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"URL fetch failed: HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"URL fetch failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise SystemExit(f"URL fetch timed out after {timeout}s: {url}") from exc

    if "html" in content_type.lower() or decoded.lstrip().lower().startswith(("<!doctype html", "<html")):
        parser = ReadableHTMLParser()
        parser.feed(decoded)
        title = parser.title
        description = parser.meta_description
        text = parser.readable_text
    else:
        title = None
        description = None
        text = decoded

    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return {
        "url": url,
        "title": title,
        "description": description,
        "contentType": content_type,
        "status": status,
        "truncated": truncated or len(text) > MAX_EXTRACTED_CHARS,
        "text": text[:MAX_EXTRACTED_CHARS],
    }


def classify(text: str, forced_type: str = "auto") -> tuple[str, list[str], str | None]:
    lowered = text.lower()
    urls = extract_urls(text)
    github_url = next((u for u in urls if "github.com/" in u.lower()), None)

    if forced_type != "auto":
        kind = forced_type
    elif github_url:
        kind = "github"
    elif urls:
        kind = "web"
    elif any(word in lowered for word in ["decided", "decision", "choose", "chose", "final call"]):
        kind = "decision"
    elif any(word in lowered for word in ["idea", "maybe", "should build", "want to build", "what if"]):
        kind = "idea"
    elif lowered.startswith(("journal:", "diary:")) or (
        len(text) < 500 and any(word in lowered for word in ["today i", "i felt", "i am thinking", "i'm thinking"])
    ):
        kind = "journal"
    elif any(any(key in lowered for key in keys) for keys in PROJECT_KEYWORDS.values()):
        kind = "project"
    else:
        kind = "inbox"

    tags = [kind, "openclaw", "captured"]
    for project, keys in PROJECT_KEYWORDS.items():
        if any(key in lowered for key in keys):
            tags.append(project)
    if urls:
        tags.append("url")
    if github_url:
        tags.append("github")
    return kind, sorted(set(tags)), github_url or (urls[0] if urls else None)


OBSIDIAN_WORD_RE = r"obs[ie]di[ae]n"


def derive_title(text: str, kind: str, source_url: str | None) -> str:
    if kind == "github" and source_url:
        match = re.search(r"github\.com/([^/\s]+/[^/\s#?]+)", source_url)
        if match:
            return match.group(1).removesuffix(".git")
    if source_url:
        host = re.sub(r"^https?://", "", source_url).split("/")[0]
        return host
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    first_line = re.sub(rf"^/{OBSIDIAN_WORD_RE}\s*", "", first_line, flags=re.I).strip()
    first_line = re.sub(r"\s+", " ", first_line)
    return first_line[:80] or f"{kind.title()} capture"


def note_id(text: str) -> str:
    stamp = now_local().strftime("%Y%m%d-%H%M%S")
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
    return f"{stamp}-{digest}"


def frontmatter(fields: dict[str, object]) -> str:
    lines = ["---"]
    for key, value in fields.items():
        if value is None:
            continue
        if isinstance(value, list):
            lines.append(f"{key}: {yaml_list([str(v) for v in value])}")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        else:
            lines.append(f"{key}: {yaml_scalar(str(value))}")
    lines.append("---")
    return "\n".join(lines)


def append_index(vault: Path, record: dict[str, object]) -> None:
    index = vault / SYSTEM_DIR / INDEX_FILE
    with index.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def strip_command(text: str) -> str:
    cleaned = re.sub(rf"^\s*/{OBSIDIAN_WORD_RE}(?:\s+|$)", "", text, flags=re.I).strip()
    crawl_suffix = r"(?:\s+and\s+(?:crawl|fetch|read)\s+it)?"
    natural_patterns = [
        rf"^\s*save\s+(?:(?:this|it)\s+)?(?:to|in)\s+{OBSIDIAN_WORD_RE}(?:\s+memory)?{crawl_suffix}\s*[:,-]?\s*",
        rf"^\s*add\s+(?:(?:this|it)\s+)?(?:to|in)\s+{OBSIDIAN_WORD_RE}(?:\s+memory)?{crawl_suffix}\s*[:,-]?\s*",
        rf"^\s*log\s+(?:(?:this|it)\s+)?(?:to|in)\s+{OBSIDIAN_WORD_RE}(?:\s+memory)?{crawl_suffix}\s*[:,-]?\s*",
        rf"^\s*remember\s+(?:(?:this|it)\s+)?(?:in|to)\s+{OBSIDIAN_WORD_RE}(?:\s+memory)?{crawl_suffix}\s*[:,-]?\s*",
        rf"^\s*crawl\s+(?:(?:this|it)\s+)?(?:to|in)\s+{OBSIDIAN_WORD_RE}(?:\s+memory)?\s*[:,-]?\s*",
    ]
    for pattern in natural_patterns:
        updated = re.sub(pattern, "", cleaned, flags=re.I).strip()
        if updated != cleaned:
            return updated
    return cleaned


def capture(
    text: str,
    forced_type: str = "auto",
    source: str = "openclaw-chat",
    crawled: dict[str, object] | None = None,
) -> dict[str, object]:
    vault = vault_path()
    ensure_vault(vault)
    clean_text = strip_command(text)
    if not clean_text:
        raise SystemExit("Nothing to capture after /obsidian.")

    kind, tags, source_url = classify(clean_text, forced_type)
    title = str(crawled.get("title") or "") if crawled else ""
    if not title:
        title = derive_title(clean_text, kind, source_url)
    capture_id = note_id(clean_text)

    if kind == "journal":
        rel_path = Path(TYPE_DIRS[kind]) / f"{today()}.md"
        path = vault / rel_path
        if not path.exists():
            path.write_text(
                frontmatter({
                    "type": "daily-journal",
                    "date": today(),
                    "source": "openclaw-obsidian",
                    "tags": ["journal", "openclaw"],
                })
                + f"\n\n# {today()}\n\n",
                encoding="utf-8",
            )
        with path.open("a", encoding="utf-8") as fh:
            fh.write(f"## {now_local().strftime('%H:%M')} - OpenClaw capture\n\n{clean_text}\n\n")
    else:
        directory = vault / TYPE_DIRS.get(kind, TYPE_DIRS["inbox"])
        filename = f"{capture_id}-{slugify(title, kind)}.md"
        rel_path = Path(TYPE_DIRS.get(kind, TYPE_DIRS["inbox"])) / filename
        path = vault / rel_path
        path.write_text(
            frontmatter({
                "type": kind,
                "title": title,
                "source": source,
                "sourceUrl": source_url,
                "crawled": bool(crawled),
                "contentType": crawled.get("contentType") if crawled else None,
                "created": iso_now(),
                "tags": tags,
                "openclawCaptureId": capture_id,
            })
            + f"\n\n# {title}\n\n"
            + "## User Capture\n\n"
            + clean_text
            + "\n\n"
            + (
                "## Crawled Page\n\n"
                + (f"- Description: {crawled.get('description')}\n" if crawled.get("description") else "")
                + f"- HTTP status: {crawled.get('status')}\n"
                + f"- Content type: {crawled.get('contentType') or 'unknown'}\n"
                + f"- Truncated: {str(crawled.get('truncated')).lower()}\n\n"
                + "## Extracted Text\n\n"
                + str(crawled.get("text") or "No readable text extracted.")
                + "\n\n"
                if crawled
                else ""
            )
            + "## OpenClaw Catalog\n\n"
            + f"- Type: {kind}\n"
            + f"- Captured: {iso_now()}\n"
            + (f"- Source URL: {source_url}\n" if source_url else "")
            + f"- Tags: {', '.join(tags)}\n",
            encoding="utf-8",
        )

    record = {
        "id": capture_id,
        "created": iso_now(),
        "type": kind,
        "title": title,
        "path": str(rel_path),
        "source": source,
        "sourceUrl": source_url,
        "tags": tags,
        "crawled": bool(crawled),
        "preview": re.sub(r"\s+", " ", clean_text)[:240],
    }
    append_index(vault, record)
    return record


def iter_markdown(vault: Path) -> Iterable[Path]:
    user_memory_roots = set(TYPE_DIRS.values())
    skip = {".obsidian", ".trash", "reports"}
    system_pages = {"README.md", "index.md"}
    for path in vault.rglob("*.md"):
        rel_parts = path.relative_to(vault).parts
        if not rel_parts or rel_parts[0] not in user_memory_roots:
            continue
        if any(part in skip for part in rel_parts):
            continue
        if rel_parts[-1] in system_pages and len(rel_parts) == 1:
            continue
        yield path


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9_-]*", text.lower())


def excerpt(text: str, terms: set[str], width: int = 280) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    lowered = compact.lower()
    positions = [lowered.find(term) for term in terms if lowered.find(term) >= 0]
    start = max(0, min(positions) - 80) if positions else 0
    snippet = compact[start : start + width]
    return ("..." if start else "") + snippet + ("..." if start + width < len(compact) else "")


def search(query: str, limit: int = 8) -> list[dict[str, object]]:
    vault = vault_path()
    ensure_vault(vault)
    terms = set(tokenize(query))
    if not terms:
        return []

    results: list[dict[str, object]] = []
    for path in iter_markdown(vault):
        raw = path.read_text(encoding="utf-8", errors="ignore")
        haystack = raw.lower()
        rel = str(path.relative_to(vault))
        score = 0
        for term in terms:
            count = haystack.count(term)
            if count:
                score += count
                if term in rel.lower():
                    score += 3
                if f"title:" in haystack and term in haystack[:500]:
                    score += 2
        if score:
            results.append({
                "score": score,
                "path": rel,
                "title": path.stem,
                "excerpt": excerpt(raw, terms),
            })
    return sorted(results, key=lambda item: (-int(item["score"]), str(item["path"])))[:limit]


def load_recent(limit: int = 10) -> list[dict[str, object]]:
    vault = vault_path()
    ensure_vault(vault)
    index = vault / SYSTEM_DIR / INDEX_FILE
    rows = []
    for line in index.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows[-limit:][::-1]


def print_capture(record: dict[str, object], json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return
    print(f"Saved to Obsidian: {record['path']}")
    print(f"Type: {record['type']}")
    print(f"Title: {record['title']}")


def print_results(results: list[dict[str, object]], json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    if not results:
        print("No Obsidian memory results.")
        return
    for idx, item in enumerate(results, 1):
        print(f"{idx}. {item['path']} (score {item['score']})")
        print(textwrap.indent(str(item["excerpt"]), "   "))


def cmd_init(_: argparse.Namespace) -> None:
    vault = vault_path()
    ensure_vault(vault)
    readme = vault / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Obsidian AI Memory\n\n"
            "This vault is managed by OpenClaw through `openclaw-obsidian`.\n\n"
            "- Paste `/obsidian ...` in OpenClaw to capture memory.\n"
            "- OpenClaw searches this vault when answering memory-style questions.\n"
            "- Human notes are welcome; files are plain Markdown.\n",
            encoding="utf-8",
        )
    print(f"Initialized Obsidian memory vault: {vault}")


def cmd_capture(args: argparse.Namespace) -> None:
    text = " ".join(args.text).strip() if args.text else sys.stdin.read().strip()
    crawled = None
    if args.crawl:
        clean_text = strip_command(text)
        urls = extract_urls(clean_text)
        if not urls:
            raise SystemExit("--crawl requires a URL in the captured text.")
        crawled = fetch_url(urls[0], timeout=args.timeout)
    print_capture(capture(text, forced_type=args.type, source=args.source, crawled=crawled), args.json)


def cmd_crawl(args: argparse.Namespace) -> None:
    url = args.url.strip()
    note = " ".join(args.note).strip()
    crawled = fetch_url(url, timeout=args.timeout)
    capture_text = f"{url}\n\nUser note: {note}" if note else url
    print_capture(capture(capture_text, forced_type=args.type, source=args.source, crawled=crawled), args.json)


def cmd_search(args: argparse.Namespace) -> None:
    query = " ".join(args.query).strip()
    print_results(search(query, limit=args.limit), args.json)


def cmd_recent(args: argparse.Namespace) -> None:
    rows = load_recent(args.limit)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    for row in rows:
        print(f"- {row.get('created')} {row.get('type')} {row.get('path')}: {row.get('preview')}")


def cmd_status(_: argparse.Namespace) -> None:
    vault = vault_path()
    ensure_vault(vault)
    notes = list(iter_markdown(vault))
    print(f"Vault: {vault}")
    print(f"Markdown notes: {len(notes)}")
    print(f"Index: {vault / SYSTEM_DIR / INDEX_FILE}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenClaw Obsidian memory bridge")
    sub = parser.add_subparsers(dest="command")

    init_p = sub.add_parser("init", help="Create the vault layout")
    init_p.set_defaults(func=cmd_init)

    cap_p = sub.add_parser("capture", help="Capture text into Obsidian")
    cap_p.add_argument("text", nargs="*")
    cap_p.add_argument("--type", default="auto", choices=["auto", *TYPE_DIRS.keys()])
    cap_p.add_argument("--source", default="openclaw-chat")
    cap_p.add_argument("--crawl", action="store_true", help="Fetch and store readable page text from the first URL")
    cap_p.add_argument("--timeout", type=int, default=20, help="URL fetch timeout in seconds")
    cap_p.add_argument("--json", action="store_true")
    cap_p.set_defaults(func=cmd_capture)

    crawl_p = sub.add_parser("crawl", help="Fetch a URL and save readable page text into Obsidian")
    crawl_p.add_argument("url")
    crawl_p.add_argument("note", nargs="*")
    crawl_p.add_argument("--type", default="web", choices=["web", "github", "project", "inbox"])
    crawl_p.add_argument("--source", default="openclaw-crawl")
    crawl_p.add_argument("--timeout", type=int, default=20, help="URL fetch timeout in seconds")
    crawl_p.add_argument("--json", action="store_true")
    crawl_p.set_defaults(func=cmd_crawl)

    search_p = sub.add_parser("search", help="Search captured Obsidian memory")
    search_p.add_argument("query", nargs="+")
    search_p.add_argument("--limit", type=int, default=8)
    search_p.add_argument("--json", action="store_true")
    search_p.set_defaults(func=cmd_search)

    recent_p = sub.add_parser("recent", help="Show recent captures")
    recent_p.add_argument("--limit", type=int, default=10)
    recent_p.add_argument("--json", action="store_true")
    recent_p.set_defaults(func=cmd_recent)

    status_p = sub.add_parser("status", help="Show vault status")
    status_p.set_defaults(func=cmd_status)

    return parser


def main() -> int:
    parser = build_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        return 2

    # Convenience: allow `openclaw-obsidian /obsidian pasted text`.
    if sys.argv[1].lower() in {"/obsidian", "/obsedian"}:
        record = capture(" ".join(sys.argv[1:]))
        print_capture(record, json_mode=False)
        return 0

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return 2
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
