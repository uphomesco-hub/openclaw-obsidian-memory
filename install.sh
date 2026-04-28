#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
install_dir="${OPENCLAW_TOOLS_DIR:-$HOME/.openclaw/tools}"

mkdir -p "$install_dir"
install -m 755 "$repo_dir/bin/openclaw-obsidian.py" "$install_dir/openclaw-obsidian.py"
install -m 755 "$repo_dir/bin/openclaw-obsidian" "$install_dir/openclaw-obsidian"

"$install_dir/openclaw-obsidian" init

cat <<EOF
Installed OpenClaw Obsidian bridge:
  $install_dir/openclaw-obsidian

Add docs/openclaw-instructions.md to your OpenClaw workspace instructions.
EOF

