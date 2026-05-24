# CLAUDE.md

Project guidance for Claude Code (and humans) working on this repo.

## What this is

`agentmd` — a single-file Python CLI that turns one natural-language sentence
into a command/rule markdown file for one (or all) of 6 AI coding agents:
Claude Code, Cursor, Copilot, Codex, Gemini, Roo.

It shells out to the local `claude` CLI; no API key required.

## Layout

```
ai_cmd.py        # everything: argparse, agent config dict, Claude subprocess, HTTP server
agentmd.bat      # Windows shim → py ai_cmd.py %*
agentmd          # POSIX shim
install.bat      # Windows installer (copies shim to %USERPROFILE%\.local\bin\)
README.md        # user-facing docs (English)
version.md       # changelog
LICENSE          # MIT
examples/        # sample inputs/outputs
```

## Core invariants

1. **stdlib only.** No `requirements.txt`, no `pip install`. Anything beyond
   the standard library breaks the "drop one file in PATH and go" promise.
2. **Single file.** `ai_cmd.py` is the whole tool. Resist splitting into
   modules unless the file passes ~800 LOC.
3. **Claude CLI subprocess.** Do not introduce a direct Anthropic SDK
   dependency. If you want to support a different generator backend, add it
   alongside the `call_claude` function and select via env var.
4. **UTF-8 everywhere.** All file I/O passes `encoding="utf-8"` explicitly.
   Important for CJK prompts on Windows.

## Adding a new agent

Edit the `AGENTS` dict in `ai_cmd.py`:

```python
"newagent": {
    "subdir": ".newagent/commands",
    "ext": ".md",
    "guide": "<system prompt describing exact output format>",
},
```

The `guide` string is the system prompt sent to Claude — it must specify the
frontmatter shape and ask for the file body with no extra commentary or
fences. Keep it short; verbosity here gets paid every invocation.

Then add the agent to the `--agent` choices (already automatic via
`AGENTS.keys()`) and update the table in `README.md`.

## Coding conventions

- snake_case functions / variables, PascalCase classes.
- Error messages go to stderr with an `[error]` / `[warn]` prefix.
- Normal output (markdown / JSON) goes to stdout so the tool composes via
  pipes.
- Subcommand handlers are named `cmd_<action>` and return an int exit code.

## Testing locally

Smoke test:

```bash
cd /tmp/some-empty-dir
python3 path/to/ai_cmd.py new "list TODOs" --agent claude-code --json
```

Expect: `.claude/commands/list-TODOs.md` is written and the JSON response
prints to stdout. If the file is suspiciously short (< 100 bytes), the
`extract_markdown` fence-stripper probably grabbed only a snippet — that's a
known sharp edge to fix.

## Releasing

1. Bump version in `version.md`.
2. Tag: `git tag v0.x.y && git push --tags`.
3. (Optional) GitHub release with changelog from `version.md`.
