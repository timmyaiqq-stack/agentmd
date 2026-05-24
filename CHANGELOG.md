# Changelog

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
