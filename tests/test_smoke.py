"""Smoke tests for agentmd. Stdlib only. No `claude` CLI required.

Covers:
  - module imports cleanly
  - AGENTS config invariants
  - slugify / extract_markdown pure helpers
  - argparse builds without exploding
  - CLI `--help` exits 0
  - `serve` HTTP server starts and /health responds 200
  - `new` fails cleanly (non-zero exit) when claude CLI is missing
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import unittest
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import ai_cmd  # noqa: E402


class TestAgentsConfig(unittest.TestCase):
    def test_six_agents_present(self):
        expected = {"claude-code", "cursor", "copilot", "codex", "gemini", "roo"}
        self.assertEqual(set(ai_cmd.AGENTS.keys()), expected)

    def test_each_agent_has_required_keys(self):
        for name, cfg in ai_cmd.AGENTS.items():
            with self.subTest(agent=name):
                self.assertIn("subdir", cfg)
                self.assertIn("ext", cfg)
                self.assertIn("guide", cfg)
                self.assertTrue(cfg["subdir"], f"{name} subdir empty")
                self.assertTrue(cfg["ext"].startswith("."), f"{name} ext missing dot")
                self.assertTrue(len(cfg["guide"]) > 50, f"{name} guide too short")


class TestSlugify(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(ai_cmd.slugify("hello world"), "hello-world")

    def test_collapses_whitespace(self):
        self.assertEqual(ai_cmd.slugify("  a    b\tc  "), "a-b-c")

    def test_strips_windows_illegal_chars(self):
        self.assertEqual(ai_cmd.slugify('a/b\\c:d*e?f"g<h>i|j'), "abcdefghij")

    def test_truncates_to_max_len(self):
        s = ai_cmd.slugify("x" * 200, max_len=50)
        self.assertLessEqual(len(s), 50)

    def test_empty_becomes_untitled(self):
        self.assertEqual(ai_cmd.slugify(""), "untitled")
        self.assertEqual(ai_cmd.slugify("   \t\n"), "untitled")

    def test_preserves_cjk(self):
        # CJK should survive slugify intact (joined by dashes if needed).
        self.assertIn("找", ai_cmd.slugify("用 grep 找 TODO"))


class TestExtractMarkdown(unittest.TestCase):
    def test_strips_markdown_fence(self):
        raw = "```markdown\n# hello\nbody\n```"
        self.assertEqual(ai_cmd.extract_markdown(raw), "# hello\nbody")

    def test_strips_md_fence(self):
        raw = "```md\n# hi\n```"
        self.assertEqual(ai_cmd.extract_markdown(raw), "# hi")

    def test_strips_bare_fence(self):
        raw = "```\nplain\n```"
        self.assertEqual(ai_cmd.extract_markdown(raw), "plain")

    def test_passthrough_when_no_fence(self):
        self.assertEqual(ai_cmd.extract_markdown("just text"), "just text")

    def test_empty_input(self):
        self.assertEqual(ai_cmd.extract_markdown(""), "")
        self.assertEqual(ai_cmd.extract_markdown(None or ""), "")


class TestArgparse(unittest.TestCase):
    def test_builds(self):
        parser = ai_cmd.build_parser()
        self.assertIsNotNone(parser)

    def test_new_requires_prompt(self):
        parser = ai_cmd.build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["new"])

    def test_new_accepts_all_agent(self):
        parser = ai_cmd.build_parser()
        ns = parser.parse_args(["new", "hi", "--agent", "all"])
        self.assertEqual(ns.agent, "all")

    def test_unknown_agent_rejected(self):
        parser = ai_cmd.build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["new", "hi", "--agent", "nope"])


class TestAgentPath(unittest.TestCase):
    def test_claude_code_path(self):
        p = ai_cmd.agent_path("claude-code", "myslug", Path("/tmp/repo"))
        self.assertTrue(
            str(p).endswith(os.path.join(".claude", "commands", "myslug.md"))
        )

    def test_cursor_uses_mdc(self):
        p = ai_cmd.agent_path("cursor", "rules", Path("/tmp/repo"))
        self.assertTrue(str(p).endswith(".mdc"))


class TestCliHelp(unittest.TestCase):
    """Run the actual script as a subprocess; verifies the shebang/entry path."""

    SCRIPT = str(REPO_ROOT / "ai_cmd.py")

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, self.SCRIPT, *args],
            capture_output=True,
            text=True,
            timeout=15,
        )

    def test_top_help_exits_zero(self):
        r = self._run("--help")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("agentmd", r.stdout.lower())

    def test_new_help_exits_zero(self):
        r = self._run("new", "--help")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_serve_help_exits_zero(self):
        r = self._run("serve", "--help")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_no_subcommand_exits_nonzero(self):
        r = self._run()
        self.assertNotEqual(r.returncode, 0)


class TestServeHealth(unittest.TestCase):
    """Spin up `agentmd serve` and hit /health. Doesn't need claude CLI."""

    def test_health_endpoint(self):
        # Pick an unlikely port to avoid clashes.
        port = 38901
        proc = subprocess.Popen(
            [
                sys.executable,
                str(REPO_ROOT / "ai_cmd.py"),
                "serve",
                "--port",
                str(port),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            # Wait for the server to bind.
            deadline = time.time() + 5
            last_err = None
            payload = None
            while time.time() < deadline:
                try:
                    with urllib.request.urlopen(
                        f"http://127.0.0.1:{port}/health", timeout=1
                    ) as resp:
                        self.assertEqual(resp.status, 200)
                        payload = json.loads(resp.read().decode("utf-8"))
                        break
                except Exception as e:  # noqa: BLE001
                    last_err = e
                    time.sleep(0.2)
            self.assertIsNotNone(payload, f"server never came up: {last_err}")
            self.assertTrue(payload["ok"])
            self.assertIn("claude-code", payload["agents"])
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


class TestNewFailsWhenClaudeMissing(unittest.TestCase):
    """When AI_CMD_CLAUDE_PATH points at nothing, `new` must error out, not crash."""

    def test_returns_nonzero(self):
        env = dict(os.environ)
        env["AI_CMD_CLAUDE_PATH"] = "definitely_not_a_real_binary_xyz"
        r = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "ai_cmd.py"),
                "new",
                "hello",
                "--agent",
                "claude-code",
                "--name",
                "smoke-test",
            ],
            capture_output=True,
            text=True,
            timeout=15,
            env=env,
            cwd=str(REPO_ROOT / "tests"),
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("claude CLI not found", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
