# Changelog

## [0.1.1] - 2026-05-24

### Added
- GitHub Actions CI: ruff lint + ruff format check + stdlib-only ast
  invariant + smoke test matrix (ubuntu/windows/macos x py3.9/3.12).
- `tests/test_smoke.py`: 25 stdlib `unittest` tests covering AGENTS
  config, slugify, extract_markdown, argparse, agent_path, CLI `--help`,
  HTTP `/health` endpoint, and missing-binary error path. No `claude`
  CLI required.
- `examples/find-todos/`: sample output for all 6 agents.
- README badges: CI status, Python version, license.

### Fixed
- `slugify`: treat `\t` as whitespace (was being stripped as illegal
  char, so `"a\tb"` became `"ab"` instead of `"a-b"`).

### Changed
- Renamed `version.md` → `CHANGELOG.md` for convention.
- `ruff format` pass on `ai_cmd.py` and `tests/`.

## [0.1.0] - 2026-05-24

Initial public release.

### Added
- `ai_cmd.py`: single-file Python CLI (stdlib only).
  - 6 agents: claude-code / cursor / copilot / codex / gemini / roo.
  - 5 subcommands: `new`, `refine`, `list`, `show`, `serve`.
  - HTTP mode: `POST /generate` and `GET /health` with CORS.
  - Claude CLI subprocess wrapper (UTF-8, configurable timeout).
- `agentmd.bat` / `agentmd` shims for Windows and POSIX.
- `install.bat` Windows installer (copies shim to `~/.local/bin/`).
- MIT license, .gitignore, README.
