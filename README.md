# agentmd

> Natural language → command/rule markdown for 6 AI coding agents.
> One CLI. Zero dependencies. No API key.

```bash
agentmd new "grep all TODO comments and group them by file" --agent claude-code
# -> .claude/commands/grep-all-TODO-comments-and-group-them-by-fi.md

agentmd new "code review checklist for Python" --agent all
# -> .claude/commands/, .cursor/rules/, .github/copilot/,
#    .codex/workflows/, .gemini/commands/, .roo/rules/
```

`agentmd` is a single-file Python CLI (stdlib only) that takes a one-line
description and produces the correctly-formatted command, rule, or workflow
markdown file for **Claude Code, Cursor, GitHub Copilot, OpenAI Codex,
Gemini CLI, and Roo Code** — each in the exact subdirectory and frontmatter
shape that agent expects.

Under the hood it shells out to the local `claude` CLI (`claude -p`), so as
long as you're already logged into Claude Code you don't need an Anthropic API
key.

## Why

Modern AI coding agents each have their own slash-command / rule-file
convention:

| Agent | Path | Extension |
|-------|------|-----------|
| Claude Code | `.claude/commands/<slug>.md` | `.md` |
| Cursor | `.cursor/rules/<slug>.mdc` | `.mdc` |
| GitHub Copilot | `.github/copilot/<slug>.md` | `.md` |
| OpenAI Codex | `.codex/workflows/<slug>.md` | `.md` |
| Gemini CLI | `.gemini/commands/<slug>.md` | `.md` |
| Roo Code | `.roo/rules/<slug>.md` | `.md` |

Hand-writing six variants of "review this PR for security issues" is tedious.
`agentmd` does it from one English (or any-language) sentence.

It also exposes an HTTP endpoint so you can plug it into n8n, GitHub Actions,
or any orchestrator that does HTTP.

## Install

### Requirements

- Python 3.9+
- [Claude Code](https://docs.claude.com/en/docs/claude-code) installed and
  authenticated. `claude --version` should work in your terminal.

### Windows

```bat
git clone https://github.com/timmyaiqq-stack/agentmd.git
cd agentmd
install.bat
```

This copies `agentmd.bat` to `%USERPROFILE%\.local\bin\`. Add that directory
to `PATH` if it isn't already.

### macOS / Linux

```bash
git clone https://github.com/timmyaiqq-stack/agentmd.git
cd agentmd
chmod +x agentmd
ln -s "$PWD/agentmd" ~/.local/bin/agentmd
```

Or run directly: `python3 ai_cmd.py ...`

## Usage

### `new` — generate from a description

```bash
agentmd new "find all TODO comments and list file:line"
# default --agent claude-code, slug derived from prompt

agentmd new "..." --agent cursor --name find-todos
agentmd new "..." --agent all                       # produce all 6
agentmd new "..." --out ../some-project             # write into another repo
agentmd new "..." --json                            # machine-readable output
```

### `refine` — tweak an existing file

```bash
agentmd refine find-todos "only scan .py files and skip vendor/" --agent cursor
```

Reads the current file, ships its content plus your tweak to Claude, writes the
new version back.

### `list` / `show`

```bash
agentmd list                            # everything in cwd
agentmd list --agent claude-code        # just Claude Code commands
agentmd show find-todos --agent cursor  # print file contents
```

### `serve` — HTTP mode

```bash
agentmd serve --port 8901
```

Endpoints (CORS open):

| Method | Path | Body | Returns |
|--------|------|------|---------|
| POST | `/generate` | `{prompt, agent?, name?, out_dir?, write?}` | `{slug, agent, content, path?}` |
| GET | `/health` | — | `{ok, agents, claude_cli}` |

With `write: false` (default) the response carries the generated markdown
without touching the filesystem — handy when the caller already knows where it
wants the file. With `write: true`, `agentmd` drops the file in
`<out_dir>/<agent-subdir>/<slug>.<ext>`.

### n8n example

1. `agentmd serve --port 8901` (or wire it into a process manager).
2. n8n **HTTP Request** node →
   `POST http://127.0.0.1:8901/generate` with body
   `{"prompt": "{{$json.description}}", "agent": "claude-code", "write": true, "out_dir": "/path/to/repo"}`.
3. Chain to git commit, Slack notify, etc.

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `AI_CMD_CLAUDE_PATH` | `claude` | Path to the `claude` CLI binary |
| `AI_CMD_TIMEOUT` | `180` | Subprocess timeout (seconds) |
| `AI_CMD_PORT` | `8901` | Default port for `agentmd serve` |

## Project layout

```
agentmd/
├── ai_cmd.py         # everything (~380 LOC, stdlib only)
├── agentmd.bat       # Windows shim
├── agentmd           # POSIX shim
├── install.bat       # Windows installer
├── LICENSE           # MIT
├── README.md
└── examples/         # sample inputs / outputs
```

## Limitations / roadmap

- Frontmatter validation: today we trust the model to emit the right
  frontmatter. A post-processor that enforces each agent's schema is on the
  list.
- Only Claude is wired up as the generator. The interfaces are simple enough
  that swapping in any LLM CLI is a 20-line change; PR welcome.
- No model selection flag yet (`--model claude-haiku-4-5` style). Goes through
  whatever `claude -p` defaults to.

## Contributing

Issues and PRs welcome. Keep `ai_cmd.py` stdlib-only — that constraint is the
whole point.

## License

[MIT](./LICENSE) © 2026 timmyaiqq-stack
