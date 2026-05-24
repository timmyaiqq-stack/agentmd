"""agentmd: turn a one-line natural language description into a command/rule
markdown file for any of 6 AI coding agents.

Usage:
    agentmd new "grep all TODO comments in the repo" --agent claude-code
    agentmd new "..." --agent all              # produce all 6 at once
    agentmd refine my-slash "also print stats" --agent claude-code
    agentmd list [--agent claude-code]
    agentmd show my-slash --agent claude-code
    agentmd serve [--port 8901]                # HTTP mode (compose with n8n etc.)

Agents: claude-code | cursor | copilot | codex | gemini | roo

Backend: shells out to the local `claude` CLI (`claude -p`). No API key needed
when you're already logged in via Claude Code. Override the binary path with
AI_CMD_CLAUDE_PATH and the subprocess timeout with AI_CMD_TIMEOUT.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# ---------- agent config ----------

AGENTS = {
    "claude-code": {
        "subdir": ".claude/commands",
        "ext": ".md",
        "guide": (
            "You are generating a Claude Code slash-command markdown file.\n"
            "Output exactly this shape (no extra commentary, no code fences):\n"
            "  ---\n"
            "  description: <one-line summary>\n"
            "  ---\n"
            "  <full prompt body. You may use $ARGUMENTS to interpolate user args. "
            "Use markdown freely.>"
        ),
    },
    "cursor": {
        "subdir": ".cursor/rules",
        "ext": ".mdc",
        "guide": (
            "You are generating a Cursor .mdc rule file.\n"
            "Output exactly this shape (no extra commentary, no code fences):\n"
            "  ---\n"
            "  description: <one-line summary>\n"
            "  globs: [\"**/*\"]\n"
            "  alwaysApply: false\n"
            "  ---\n"
            "  <rule body in markdown>"
        ),
    },
    "copilot": {
        "subdir": ".github/copilot",
        "ext": ".md",
        "guide": (
            "You are generating a GitHub Copilot custom-instruction markdown file.\n"
            "Output exactly this shape (no extra commentary, no code fences):\n"
            "  ---\n"
            "  applyTo: \"**/*\"\n"
            "  ---\n"
            "  # <title>\n"
            "\n"
            "  <guidance body in markdown>"
        ),
    },
    "codex": {
        "subdir": ".codex/workflows",
        "ext": ".md",
        "guide": (
            "You are generating an OpenAI Codex workflow markdown file.\n"
            "Output exactly this shape (no extra commentary, no code fences):\n"
            "  ---\n"
            "  title: <title>\n"
            "  ---\n"
            "  <ordered workflow steps in markdown>"
        ),
    },
    "gemini": {
        "subdir": ".gemini/commands",
        "ext": ".md",
        "guide": (
            "You are generating a Gemini CLI command markdown file.\n"
            "Output exactly this shape (no extra commentary, no code fences):\n"
            "  ---\n"
            "  name: <command name>\n"
            "  description: <one-line summary>\n"
            "  ---\n"
            "  <prompt body in markdown>"
        ),
    },
    "roo": {
        "subdir": ".roo/rules",
        "ext": ".md",
        "guide": (
            "You are generating a Roo Code rule markdown file.\n"
            "Output exactly this shape (no extra commentary, no code fences):\n"
            "  ---\n"
            "  tags: [auto]\n"
            "  ---\n"
            "  <rule body in markdown>"
        ),
    },
}

CLAUDE_BIN = os.environ.get("AI_CMD_CLAUDE_PATH", "claude")
CLAUDE_TIMEOUT = int(os.environ.get("AI_CMD_TIMEOUT", "180"))


# ---------- helpers ----------


def slugify(text: str, max_len: int = 50) -> str:
    """Convert free text into a filename-safe slug.

    Preserves CJK and other unicode word chars; strips Windows-illegal chars.
    """
    text = text.strip()
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\\/:*?\"<>|\r\n\t]+", "", text)
    text = re.sub(r"\s+", "-", text)
    text = text.strip("-._")
    if len(text) > max_len:
        text = text[:max_len].rstrip("-._")
    return text or "untitled"


def call_claude(user_prompt: str, system_prompt: str) -> str:
    """Invoke the local `claude` CLI in print mode. Returns stdout (or '')."""
    full_input = (
        f"{system_prompt}\n\n---\nUser request:\n{user_prompt}\n\n"
        "Respond with only the final markdown content. Do not wrap it in code fences."
    )
    try:
        result = subprocess.run(
            [CLAUDE_BIN, "-p"],
            input=full_input,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=CLAUDE_TIMEOUT,
            shell=False,
        )
        if result.returncode != 0:
            print(
                f"[error] claude CLI rc={result.returncode}: {result.stderr[:300]}",
                file=sys.stderr,
            )
            return ""
        return result.stdout.strip()
    except FileNotFoundError:
        print(
            f"[error] claude CLI not found ({CLAUDE_BIN}). "
            "Set AI_CMD_CLAUDE_PATH or add it to PATH.",
            file=sys.stderr,
        )
        return ""
    except subprocess.TimeoutExpired:
        print(f"[error] claude CLI timed out after {CLAUDE_TIMEOUT}s", file=sys.stderr)
        return ""


def extract_markdown(raw: str) -> str:
    """Strip a possible ```markdown ... ``` wrapper from the model's reply."""
    if not raw:
        return ""
    m = re.search(r"```(?:markdown|md)?\s*\n(.*?)```", raw, re.DOTALL)
    if m:
        return m.group(1).strip()
    return raw.strip()


def ensure_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def agent_path(agent: str, slug: str, base: Path) -> Path:
    cfg = AGENTS[agent]
    return base / cfg["subdir"] / f"{slug}{cfg['ext']}"


# ---------- subcommands ----------


def cmd_new(args: argparse.Namespace) -> int:
    prompt = args.prompt.strip()
    if not prompt:
        print("[error] description must not be empty", file=sys.stderr)
        return 2

    agents = list(AGENTS.keys()) if args.agent == "all" else [args.agent]
    slug = args.name or slugify(prompt[:40])
    base = Path(args.out).resolve() if args.out else Path.cwd()
    results = []

    for ag in agents:
        guide = AGENTS[ag]["guide"]
        print(f"[agentmd] generating {ag} ({slug}) ...", file=sys.stderr)
        raw = call_claude(prompt, guide)
        body = extract_markdown(raw)
        if not body:
            print(f"[warn] {ag} produced empty output, skipping", file=sys.stderr)
            continue
        out_path = agent_path(ag, slug, base)
        ensure_dir(out_path)
        out_path.write_text(body, encoding="utf-8")
        results.append(
            {"agent": ag, "path": str(out_path), "bytes": len(body.encode("utf-8"))}
        )
        print(f"  -> {out_path}", file=sys.stderr)

    if args.json:
        print(json.dumps({"slug": slug, "results": results}, ensure_ascii=False, indent=2))
    elif not results:
        return 1
    return 0


def cmd_refine(args: argparse.Namespace) -> int:
    base = Path(args.out).resolve() if args.out else Path.cwd()
    p = agent_path(args.agent, args.slug, base)
    if not p.exists():
        print(f"[error] not found: {p}", file=sys.stderr)
        return 2
    existing = p.read_text(encoding="utf-8")
    guide = AGENTS[args.agent]["guide"]
    user_prompt = (
        f"Current file contents:\n```markdown\n{existing}\n```\n\n"
        f"Apply the following change and return the full new version:\n{args.tweak.strip()}"
    )
    print(f"[agentmd] refining {args.agent} ({args.slug}) ...", file=sys.stderr)
    raw = call_claude(user_prompt, guide)
    body = extract_markdown(raw)
    if not body:
        print("[error] empty output", file=sys.stderr)
        return 1
    p.write_text(body, encoding="utf-8")
    print(f"  -> {p}", file=sys.stderr)
    if args.json:
        print(
            json.dumps(
                {"slug": args.slug, "agent": args.agent, "path": str(p)},
                ensure_ascii=False,
                indent=2,
            )
        )
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    base = Path(args.out).resolve() if args.out else Path.cwd()
    agents = list(AGENTS.keys()) if args.agent == "all" else [args.agent]
    out = []
    for ag in agents:
        cfg = AGENTS[ag]
        d = base / cfg["subdir"]
        if not d.exists():
            continue
        for f in sorted(d.glob(f"*{cfg['ext']}")):
            out.append(
                {
                    "agent": ag,
                    "slug": f.stem,
                    "path": str(f),
                    "size": f.stat().st_size,
                    "mtime": datetime.fromtimestamp(
                        f.stat().st_mtime, tz=timezone.utc
                    ).isoformat(),
                }
            )
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        for r in out:
            print(f"{r['agent']:12s} {r['slug']:40s} {r['size']:>6}B  {r['path']}")
        if not out:
            print("(none)")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    base = Path(args.out).resolve() if args.out else Path.cwd()
    p = agent_path(args.agent, args.slug, base)
    if not p.exists():
        print(f"[error] not found: {p}", file=sys.stderr)
        return 2
    print(p.read_text(encoding="utf-8"))
    return 0


# ---------- HTTP serve (for n8n / external orchestrators) ----------


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *a):
        sys.stderr.write(f"[agentmd serve] {self.address_string()} - " + (fmt % a) + "\n")

    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._send(
                200,
                {"ok": True, "agents": list(AGENTS.keys()), "claude_cli": CLAUDE_BIN},
            )
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid json"})
            return

        if self.path == "/generate":
            prompt = (payload.get("prompt") or "").strip()
            agent = payload.get("agent") or "claude-code"
            name = payload.get("name")
            out_dir = payload.get("out_dir")
            write = bool(payload.get("write", False))
            if not prompt:
                self._send(400, {"error": "prompt required"})
                return
            if agent not in AGENTS:
                self._send(
                    400, {"error": f"unknown agent. supported: {list(AGENTS)}"}
                )
                return
            slug = name or slugify(prompt[:40])
            raw = call_claude(prompt, AGENTS[agent]["guide"])
            body = extract_markdown(raw)
            if not body:
                self._send(502, {"error": "claude returned empty"})
                return
            result = {"slug": slug, "agent": agent, "content": body}
            if write:
                base = Path(out_dir).resolve() if out_dir else Path.cwd()
                p = agent_path(agent, slug, base)
                ensure_dir(p)
                p.write_text(body, encoding="utf-8")
                result["path"] = str(p)
            self._send(200, result)
        else:
            self._send(404, {"error": "not found"})


def cmd_serve(args: argparse.Namespace) -> int:
    server = HTTPServer(("127.0.0.1", args.port), _Handler)
    print(
        f"[agentmd serve] http://127.0.0.1:{args.port}  agents={list(AGENTS)}",
        file=sys.stderr,
    )
    print(
        "  POST /generate  body: {prompt, agent?, name?, out_dir?, write?}",
        file=sys.stderr,
    )
    print("  GET  /health", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[agentmd serve] stopped", file=sys.stderr)
    return 0


# ---------- argparse ----------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="agentmd",
        description="Turn a natural language description into a command/rule "
        "markdown file for any of 6 AI coding agents.",
    )
    sub = p.add_subparsers(dest="action", required=True)

    p_new = sub.add_parser("new", help="generate a new file from a description")
    p_new.add_argument("prompt", help="natural language description")
    p_new.add_argument("--agent", choices=[*AGENTS.keys(), "all"], default="claude-code")
    p_new.add_argument(
        "--name", help="slug without extension (default: first 40 chars of prompt)"
    )
    p_new.add_argument("--out", help="output root dir (default: cwd)")
    p_new.add_argument(
        "--json", action="store_true", help="emit machine-readable JSON to stdout"
    )
    p_new.set_defaults(func=cmd_new)

    p_ref = sub.add_parser("refine", help="rewrite an existing file with a tweak")
    p_ref.add_argument("slug")
    p_ref.add_argument("tweak", help="change description")
    p_ref.add_argument("--agent", choices=list(AGENTS.keys()), default="claude-code")
    p_ref.add_argument("--out", help="root dir")
    p_ref.add_argument("--json", action="store_true")
    p_ref.set_defaults(func=cmd_refine)

    p_ls = sub.add_parser("list", help="list generated files")
    p_ls.add_argument("--agent", choices=[*AGENTS.keys(), "all"], default="all")
    p_ls.add_argument("--out", help="root dir")
    p_ls.add_argument("--json", action="store_true")
    p_ls.set_defaults(func=cmd_list)

    p_sh = sub.add_parser("show", help="print file contents")
    p_sh.add_argument("slug")
    p_sh.add_argument("--agent", choices=list(AGENTS.keys()), default="claude-code")
    p_sh.add_argument("--out", help="root dir")
    p_sh.set_defaults(func=cmd_show)

    p_srv = sub.add_parser("serve", help="HTTP server mode (for n8n etc.)")
    p_srv.add_argument(
        "--port", type=int, default=int(os.environ.get("AI_CMD_PORT", "8901"))
    )
    p_srv.set_defaults(func=cmd_serve)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
