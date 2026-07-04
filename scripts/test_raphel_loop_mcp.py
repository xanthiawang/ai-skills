#!/usr/bin/env python3
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("raphel_loop_mcp.py")
spec = importlib.util.spec_from_file_location("raphel_loop_mcp", MODULE_PATH)
raphel = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(raphel)


class RaphelLoopMcpTests(unittest.TestCase):
    def test_rejects_costly_model_variants_by_default(self):
        for model in [
            "claude-opus-4-8-max",
            "gpt-5.1-codex-max-xhigh",
            "claude-4.6-opus-max-thinking",
        ]:
            with self.subTest(model=model):
                with self.assertRaises(ValueError):
                    raphel.validate_model(model)

    def test_allows_default_non_max_model(self):
        raphel.validate_model("gpt-5.5-extra-high")
        raphel.validate_model("gpt-5.5-extra-high-fast")

    def test_parses_last_status_marker(self):
        output = "RAPHEL_STATUS: continue\nlater\nRAPHEL_STATUS: done\n"
        self.assertEqual(raphel.parse_status(output), "done")

    def test_prompt_requires_internal_loop_single_invocation(self):
        prompt = raphel.make_prompt("finish the task", 9)
        self.assertIn("only Cursor Agent invocation", prompt)
        self.assertIn("inside this single", prompt)
        self.assertIn("9 internal", prompt)

    def test_run_job_invokes_cursor_agent_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            bin_dir = tmp_path / "bin"
            work_dir = tmp_path / "work"
            state_dir = tmp_path / "state"
            count_file = tmp_path / "count"
            prompt_file = tmp_path / "prompt"
            bin_dir.mkdir()
            work_dir.mkdir()
            state_dir.mkdir()
            fake_cursor = bin_dir / "cursor-agent"
            fake_cursor.write_text(
                "#!/bin/sh\n"
                f"count=$(cat '{count_file}' 2>/dev/null || echo 0)\n"
                f"echo $((count + 1)) > '{count_file}'\n"
                f"printf '%s\\n' \"$@\" > '{prompt_file}'\n"
                "echo fake internal loop complete\n"
                "echo RAPHEL_STATUS: done\n",
                encoding="utf-8",
            )
            fake_cursor.chmod(0o755)

            old_state_dir = raphel.STATE_DIR
            old_path = os.environ.get("PATH", "")
            raphel.STATE_DIR = state_dir
            os.environ["PATH"] = f"{bin_dir}:{old_path}"
            try:
                paths = raphel.job_paths("job1")
                paths["dir"].mkdir(parents=True)
                raphel.write_json_atomic(
                    paths["state"],
                    {
                        "job_id": "job1",
                        "task": "finish the task",
                        "workspace": str(work_dir),
                        "model": "gpt-5.5-extra-high",
                        "max_iterations": 7,
                        "cursor_timeout_sec": 60,
                        "iteration": 0,
                        "status": "starting",
                        "created_at": raphel.utc_now(),
                        "updated_at": raphel.utc_now(),
                        "agent_log": str(paths["agent_log"]),
                        "runner_log": str(paths["runner_log"]),
                    },
                )
                self.assertEqual(raphel.run_job("job1"), 0)
                self.assertEqual(count_file.read_text(encoding="utf-8").strip(), "1")
                state = raphel.read_json(paths["state"])
                self.assertEqual(state["status"], "done")
                self.assertEqual(state["iteration"], 1)
                self.assertIn("only Cursor Agent invocation", prompt_file.read_text(encoding="utf-8"))
            finally:
                raphel.STATE_DIR = old_state_dir
                os.environ["PATH"] = old_path

    def test_ignores_non_final_status_marker(self):
        output = "RAPHEL_STATUS: done\nbut then more text\n"
        self.assertEqual(raphel.parse_status(output), "continue")

    def test_tools_call_rejects_costly_model(self):
        response = raphel.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "start_cursor_loop",
                    "arguments": {
                        "task": "do a task",
                        "workspace": str(Path.cwd()),
                        "model": "claude-opus-4-8-max",
                    },
                },
            }
        )
        self.assertIsNotNone(response)
        self.assertIn("error", response)

    def test_tools_list_exposes_checkpoint(self):
        response = raphel.handle_request(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        )
        self.assertIsNotNone(response)
        names = {tool["name"] for tool in response["result"]["tools"]}
        self.assertIn("raphel_loop_checkpoint", names)

    def test_checkpoint_blocks_unverified_finish(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_state_dir = raphel.STATE_DIR
            raphel.STATE_DIR = Path(tmp)
            try:
                result = raphel.raphel_loop_checkpoint(
                    {
                        "status": "done",
                        "summary": "Changed files",
                        "remaining_work": "tests not run",
                    }
                )
                self.assertFalse(result["finish_allowed"])
                self.assertIn("continue_work", result["instruction"])
            finally:
                raphel.STATE_DIR = old_state_dir

    def test_checkpoint_allows_verified_finish(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_state_dir = raphel.STATE_DIR
            raphel.STATE_DIR = Path(tmp)
            try:
                result = raphel.raphel_loop_checkpoint(
                    {
                        "status": "done",
                        "summary": "Implemented and tested",
                        "verification": "pytest passed",
                        "remaining_work": "",
                    }
                )
                self.assertTrue(result["finish_allowed"])
                self.assertIn("finish_allowed", result["instruction"])
            finally:
                raphel.STATE_DIR = old_state_dir

    def test_summarize_job_reads_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_state_dir = raphel.STATE_DIR
            raphel.STATE_DIR = Path(tmp)
            try:
                paths = raphel.job_paths("job1")
                paths["dir"].mkdir(parents=True)
                raphel.write_json_atomic(paths["state"], {"job_id": "job1", "status": "done"})
                summary = raphel.summarize_job("job1", include_tail=False)
                self.assertEqual(summary["status"], "done")
                self.assertTrue(summary["state_path"].endswith("state.json"))
            finally:
                raphel.STATE_DIR = old_state_dir


if __name__ == "__main__":
    unittest.main()
