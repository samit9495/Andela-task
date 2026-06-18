#!/usr/bin/env bash
# Appends every user prompt to docs/prompts.md as an audit log of all instructions.
# Wired to the `beforeSubmitPrompt` Cursor hook. Fails open: a logging error must
# never block the user's prompt.
#
# Acceptance criterion (Requirement doc Section 15):
#   "prompts.md contains complete prompt history."
# Root-level prompts.md is a symlink to docs/prompts.md (the single source of truth).

set -uo pipefail

# Read the hook payload from stdin and hand it to Python via the environment so
# that stdin stays free for the inline program.
HOOK_PAYLOAD="$(cat || true)"
export HOOK_PAYLOAD
export LOG_FILE="docs/prompts.md"

python3 <<'PY'
import datetime
import json
import os
import re
import sys

log_file = os.environ.get("LOG_FILE", "docs/prompts.md")
raw = os.environ.get("HOOK_PAYLOAD", "")

try:
    data = json.loads(raw) if raw.strip() else {}
except json.JSONDecodeError:
    data = {}

prompt = (data.get("prompt") or "").strip()
if not prompt:
    print(json.dumps({"continue": True}))
    sys.exit(0)

# Redact obvious secrets so the audit log never leaks credentials.
SECRET_PATTERNS = [
    r"AIza[0-9A-Za-z_\-]{20,}",            # Google API key
    r"sk-[A-Za-z0-9]{20,}",                # OpenAI-style key
    r"gh[pousr]_[A-Za-z0-9]{20,}",         # GitHub token
    r"xox[baprs]-[A-Za-z0-9-]{10,}",       # Slack token
    r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*\S+",
]
for pattern in SECRET_PATTERNS:
    prompt = re.sub(pattern, "[REDACTED]", prompt)

conversation_id = data.get("conversation_id") or "unknown"
composer_mode = data.get("composer_mode") or "unknown"
attachments = data.get("attachments") or []
attachment_paths = [
    a.get("file_path") or a.get("filePath")
    for a in attachments
    if isinstance(a, dict) and (a.get("file_path") or a.get("filePath"))
]

timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

lines = [
    "",
    f"## {timestamp} - conversation `{conversation_id}` - mode `{composer_mode}`",
    "",
]
if attachment_paths:
    lines.append("**Attachments:** " + ", ".join(f"`{p}`" for p in attachment_paths))
    lines.append("")
lines.append("```text")
lines.append(prompt)
lines.append("```")
lines.append("")

entry = "\n".join(lines)

os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
if not os.path.exists(log_file):
    header = (
        "# Prompt Audit Log\n"
        "\n"
        "Complete history of every instruction given to the AI coding agent for the\n"
        "Agentic Observability Platform. Appended automatically by the\n"
        "`beforeSubmitPrompt` Cursor hook (`.cursor/hooks/log-prompt.sh`).\n"
        "\n"
        "Runtime Gemini prompts from the triage pipeline are logged separately to\n"
        "`docs/llm_prompts.md` by `backend/app/triage/prompt_log.py`.\n"
    )
    with open(log_file, "w", encoding="utf-8") as fh:
        fh.write(header)

with open(log_file, "a", encoding="utf-8") as fh:
    fh.write(entry)

print(json.dumps({"continue": True}))
PY

# Always allow the prompt through, even if the logger above failed.
status=$?
if [ "$status" -ne 0 ]; then
  echo '{"continue": true}'
fi
exit 0
