# examples

Sample outputs produced by `agentmd` for a single natural-language prompt
across all six supported agents. Useful for eyeballing the frontmatter
shape each agent expects.

## `find-todos/`

Prompt:

> find all TODO comments in the repo and group them by file

Generated with:

```bash
agentmd new "find all TODO comments in the repo and group them by file" \
  --agent all --name find-todos
```

Each file mirrors the path / extension that `agentmd` writes by default:

| Agent | File in this dir | Real destination |
|-------|------------------|------------------|
| Claude Code | `claude-code.md` | `.claude/commands/find-todos.md` |
| Cursor | `cursor.mdc` | `.cursor/rules/find-todos.mdc` |
| GitHub Copilot | `copilot.md` | `.github/copilot/find-todos.md` |
| OpenAI Codex | `codex.md` | `.codex/workflows/find-todos.md` |
| Gemini CLI | `gemini.md` | `.gemini/commands/find-todos.md` |
| Roo Code | `roo.md` | `.roo/rules/find-todos.md` |

These are **illustrative** — the live model output will vary in wording but
the frontmatter shape is enforced by `AGENTS[<name>]["guide"]` in
`ai_cmd.py`.
