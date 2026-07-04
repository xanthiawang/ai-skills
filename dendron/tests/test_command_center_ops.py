import importlib.util
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "command-center" / "scripts"


def load_script(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CommandCenterHealthcheckTests(unittest.TestCase):
    def setUp(self):
        self.healthcheck = load_script("healthcheck")

    def test_sync_status_marks_stale_sources(self):
        text = """
## Sync Status

| Source | Last sync | Coverage |
|---|---|---|
| Email | 2026-04-30 22:52 UTC | inbox 30 + sent 50 |
| Calendar | 2026-05-01 16:30 UTC | today |
"""
        rows = self.healthcheck.parse_sync_status(text)
        now = datetime(2026, 5, 1, 17, 0, tzinfo=timezone.utc)

        checks = self.healthcheck.check_sync_status(rows, now=now)

        by_name = {c["name"]: c for c in checks}
        self.assertEqual(by_name["sync.email"]["severity"], "warn")
        self.assertIn("18.1h old", by_name["sync.email"]["detail"])
        self.assertEqual(by_name["sync.calendar"]["severity"], "ok")

    def test_session_index_warns_when_latest_jsonl_is_newer(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db_path = root / "session_index.db"
            session_dir = root / "sessions"
            session_dir.mkdir()
            latest = session_dir / "new.jsonl"
            latest.write_text("{}\n")
            latest_mtime = datetime(2026, 5, 1, 17, 0, tzinfo=timezone.utc).timestamp()
            old_indexed = datetime(2026, 4, 27, 10, 0, tzinfo=timezone.utc).timestamp()
            latest.touch()
            import os

            os.utime(latest, (latest_mtime, latest_mtime))
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE sessions (indexed_at INTEGER)")
            conn.execute("INSERT INTO sessions(indexed_at) VALUES (?)", (int(old_indexed),))
            conn.commit()
            conn.close()

            check = self.healthcheck.check_session_index(
                db_path=db_path,
                session_dir=session_dir,
                now=datetime(2026, 5, 1, 17, 0, tzinfo=timezone.utc),
            )

        self.assertEqual(check["severity"], "warn")
        self.assertIn("latest transcript is 103.0h newer", check["detail"])


class ProactiveQueueTests(unittest.TestCase):
    def setUp(self):
        self.queue = load_script("proactive_queue")

    def test_queue_prioritizes_urgent_action_over_tracking(self):
        working_memory = """
## Email Inbox — Active Items (synced 2026-05-01)

### Needs Action (HIGH)
- [ ] **HK TTPS Cat C — temp ID expires today 2026-05-01**. Verify submission status before midnight.
- [ ] **Ken Chen UKB GWAS QC** — results delivered 4/18; 13 days stale.

### Tracking / FYI (no immediate action)
- **Tony 'Prompts for the agentic cortex'** — Tony replied. Tracking.

## Live Tasks
- [ ] **Send Wuxi spec to Shajesh** — proceed.
"""
        command_center = """
## Open Follow-Ups

### High Priority
- [ ] **Frontiers reviewer response overdue** — respond point-by-point.
"""

        items = self.queue.build_queue(
            working_memory=working_memory,
            command_center=command_center,
            parked_convos="",
            limit=5,
        )

        titles = [item["title"] for item in items]
        self.assertEqual(titles[0], "HK TTPS Cat C - temp ID expires today 2026-05-01")
        self.assertIn("Frontiers reviewer response overdue", titles[:3])
        self.assertNotIn("Tony 'Prompts for the agentic cortex'", titles)

    def test_json_output_contains_ranked_actions(self):
        payload = self.queue.render_json(
            [
                {
                    "score": 120,
                    "title": "Frontiers reviewer response overdue",
                    "source": "email.high",
                    "reason": "overdue",
                    "next_action": "respond point-by-point",
                }
            ]
        )
        data = json.loads(payload)

        self.assertEqual(data["items"][0]["score"], 120)
        self.assertEqual(data["items"][0]["next_action"], "respond point-by-point")

    def test_queue_ignores_checked_context_items(self):
        command_center = """
## Open Follow-Ups

### High Priority
- [x] **HK Top Talent Pass application** — SUBMITTED 2026-04-15.
- [ ] **Nature revision work** — inspect false-positive rate.
"""

        items = self.queue.build_queue(
            working_memory="",
            command_center=command_center,
            parked_convos="",
            limit=5,
        )

        titles = [item["title"] for item in items]
        self.assertEqual(titles, ["Nature revision work"])

    def test_queue_dedupes_items_with_same_distinctive_id(self):
        working_memory = """
## Email Inbox — Active Items (synced 2026-05-01)

### Needs Action (HIGH)
- [ ] **Frontiers in Aging ms 1803872 - Reviewer 3 response overdue** — submit.
"""
        command_center = """
## Open Follow-Ups

### High Priority
- [ ] **Frontiers in Aging ms 1803872 - R3 comments due** — respond point-by-point.
"""

        items = self.queue.build_queue(
            working_memory=working_memory,
            command_center=command_center,
            parked_convos="",
            limit=5,
        )

        titles = [item["title"] for item in items]
        self.assertEqual(titles, ["Frontiers in Aging ms 1803872 - Reviewer 3 response overdue"])


class DecisionPacketsTests(unittest.TestCase):
    def setUp(self):
        self.packets = load_script("decision_packets")

    def test_packet_marks_new_items_and_approval_boundary(self):
        now = datetime(2026, 5, 1, 17, 30, tzinfo=timezone.utc)
        health = {"status": "warn", "checks": [{"name": "sync.email", "severity": "warn"}]}
        items = [
            {
                "score": 153,
                "title": "Frontiers reviewer response overdue",
                "source": "email.high",
                "reason": "overdue",
                "next_action": "submit point-by-point response",
            }
        ]

        packet = self.packets.build_packet(health=health, items=items, previous=None, now=now)

        self.assertEqual(packet["status"], "needs_decision")
        self.assertEqual(packet["changes"]["new"], 1)
        self.assertEqual(packet["approval_required_count"], 1)
        self.assertEqual(packet["items"][0]["approval"], "required")

    def test_packet_is_silent_when_unchanged(self):
        now = datetime(2026, 5, 1, 17, 30, tzinfo=timezone.utc)
        health = {"status": "ok", "checks": []}
        items = [
            {
                "score": 90,
                "title": "Ken Chen UKB GWAS QC",
                "source": "email.medium",
                "reason": "stale",
                "next_action": "review results",
            }
        ]
        previous = self.packets.build_packet(health=health, items=items, previous=None, now=now)

        current = self.packets.build_packet(health=health, items=items, previous=previous, now=now)

        self.assertEqual(current["status"], "silent")
        self.assertTrue(self.packets.should_emit_silent(current))

    def test_packet_suppresses_abandoned_items_until_source_changes(self):
        now = datetime(2026, 5, 1, 17, 30, tzinfo=timezone.utc)
        health = {"status": "ok", "checks": []}
        item = {
            "score": 153,
            "title": "Frontiers reviewer response overdue",
            "source": "email.high",
            "reason": "overdue",
            "next_action": "submit point-by-point response. Thread: abc123",
        }
        item_id = self.packets.stable_item_id(item)
        fingerprint = self.packets.item_fingerprint(item)
        ledger = {"actions": {item_id: {"status": "done", "fingerprint": fingerprint}}}

        packet = self.packets.build_packet(
            health=health,
            items=[item],
            previous=None,
            now=now,
            ledger=ledger,
        )
        changed = self.packets.build_packet(
            health=health,
            items=[{**item, "next_action": "submit revised response. Thread: abc123"}],
            previous=None,
            now=now,
            ledger=ledger,
        )

        self.assertEqual(packet["items"], [])
        self.assertEqual(packet["suppressed_count"], 1)
        self.assertEqual(len(changed["items"]), 1)

    def test_active_context_marks_related_items(self):
        now = datetime(2026, 5, 2, 9, 45, tzinfo=timezone.utc)
        health = {"status": "ok", "checks": []}
        items = [
            {
                "score": 100,
                "title": "Command-center decision desk v2",
                "source": "context.high_priority",
                "reason": "make proactive board useful",
                "next_action": "prepare the command-center design",
            },
            {
                "score": 120,
                "title": "Unrelated tax filing",
                "source": "context.high_priority",
                "reason": "file",
                "next_action": "file tax paperwork",
            },
        ]
        active_context = {
            "threads": [
                {
                    "id": "command-center",
                    "label": "Command Center",
                    "score": 95,
                    "evidence": ["process: agent-dynamic-canvas"],
                }
            ]
        }

        packet = self.packets.build_packet(
            health=health,
            items=items,
            previous=None,
            now=now,
            active_context=active_context,
        )

        self.assertEqual(packet["active_context"]["threads"][0]["id"], "command-center")
        self.assertEqual(packet["items"][0]["title"], "Command-center decision desk v2")
        self.assertEqual(packet["items"][0]["active_thread"], "command-center")
        self.assertIn("active work", packet["items"][0]["why_shown_now"])


class PreparedActionsTests(unittest.TestCase):
    def setUp(self):
        self.prepared = load_script("prepared_actions")

    def test_builds_ready_artifacts_for_concrete_email_action(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            packet = {
                "generated_at": "2026-05-01T17:30:00+00:00",
                "items": [
                    {
                        "id": "abc123",
                        "score": 153,
                        "title": "Frontiers reviewer response overdue",
                        "source": "email.high",
                        "reason": "overdue",
                        "next_action": "submit point-by-point response. Thread: 19db1d321f49f543",
                        "approval": "required",
                        "state": "new",
                    }
                ],
            }

            prepared_packet = self.prepared.build_prepared_actions(
                decision_packet=packet,
                output_dir=root / "prepared-actions",
                ledger_path=root / "action-ledger.json",
                summary_path=root / "prepared-actions.json",
                now=datetime(2026, 5, 1, 17, 45, tzinfo=timezone.utc),
            )

            action = prepared_packet["actions"][0]
            artifact_dir = Path(action["artifact_dir"])
            self.assertEqual(action["status"], "needs_draft")
            self.assertTrue((artifact_dir / "brief.md").exists())
            self.assertTrue((artifact_dir / "fire_plan.json").exists())
            self.assertTrue((artifact_dir / "draft.md").exists())
            self.assertIn("submit point-by-point response", (artifact_dir / "brief.md").read_text())
            self.assertEqual(prepared_packet["needs_draft_count"], 1)

    def test_accept_actions_are_concrete_enough_to_prepare(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            packet = {
                "generated_at": "2026-05-01T17:30:00+00:00",
                "items": [
                    {
                        "id": "accept123",
                        "score": 98,
                        "title": "Nature Communications review NCOMMS-26-031737",
                        "source": "email.medium",
                        "reason": "deadline, due",
                        "next_action": "accept through MTS if the portal still shows pending. Thread: 19ddb6b5bcbf59c5",
                        "approval": "required",
                        "state": "new",
                    }
                ],
            }

            prepared_packet = self.prepared.build_prepared_actions(
                decision_packet=packet,
                output_dir=root / "prepared-actions",
                ledger_path=root / "action-ledger.json",
                summary_path=root / "prepared-actions.json",
                now=datetime(2026, 5, 1, 17, 45, tzinfo=timezone.utc),
            )

            action = prepared_packet["actions"][0]
            self.assertEqual(action["status"], "needs_draft")
            self.assertEqual(prepared_packet["needs_draft_count"], 1)

    def test_skips_vague_context_items(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            packet = {
                "generated_at": "2026-05-01T17:30:00+00:00",
                "items": [
                    {
                        "id": "ctx1",
                        "score": 100,
                        "title": "Nature revision thread",
                        "source": "context.high_priority",
                        "reason": "reply",
                        "next_action": "open the source thread and resolve the next concrete step",
                        "approval": "required",
                        "state": "new",
                    }
                ],
            }

            prepared_packet = self.prepared.build_prepared_actions(
                decision_packet=packet,
                output_dir=root / "prepared-actions",
                ledger_path=root / "action-ledger.json",
                summary_path=root / "prepared-actions.json",
                now=datetime(2026, 5, 1, 17, 45, tzinfo=timezone.utc),
            )

            self.assertEqual(prepared_packet["actions"][0]["status"], "skipped")
            self.assertIn("vague", prepared_packet["actions"][0]["skip_reason"])
            artifact_dir = Path(prepared_packet["actions"][0]["artifact_dir"])
            self.assertTrue((artifact_dir / "brief.md").exists())
            self.assertIn("Skipped", (artifact_dir / "brief.md").read_text())

    def test_reports_ready_transition_once_after_completed_artifact_exists(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            summary_path = root / "prepared-actions.json"
            packet = {
                "generated_at": "2026-05-01T17:30:00+00:00",
                "items": [
                    {
                        "id": "abc123",
                        "score": 153,
                        "title": "Frontiers reviewer response overdue",
                        "source": "email.high",
                        "reason": "overdue",
                        "next_action": "submit point-by-point response. Thread: 19db1d321f49f543",
                        "approval": "required",
                        "state": "new",
                    }
                ],
            }
            first = self.prepared.build_prepared_actions(
                decision_packet=packet,
                output_dir=root / "prepared-actions",
                ledger_path=root / "action-ledger.json",
                summary_path=summary_path,
                now=datetime(2026, 5, 1, 17, 45, tzinfo=timezone.utc),
            )
            action_dir = Path(first["actions"][0]["artifact_dir"])
            (action_dir / "final.md").write_text(
                "Final response package prepared from source evidence. "
                "Albert still must approve before any external submission.\n"
            )

            second = self.prepared.build_prepared_actions(
                decision_packet=packet,
                output_dir=root / "prepared-actions",
                ledger_path=root / "action-ledger.json",
                summary_path=summary_path,
                now=datetime(2026, 5, 1, 17, 50, tzinfo=timezone.utc),
            )
            third = self.prepared.build_prepared_actions(
                decision_packet=packet,
                output_dir=root / "prepared-actions",
                ledger_path=root / "action-ledger.json",
                summary_path=summary_path,
                now=datetime(2026, 5, 1, 17, 55, tzinfo=timezone.utc),
            )

            self.assertEqual(second["actions"][0]["status"], "ready")
            self.assertEqual(second["ready_count"], 1)
            self.assertEqual(second["notification_events"][0]["kind"], "prepared_action_ready")
            self.assertEqual(third["notification_events"], [])

    def test_reports_blocked_transition_once_after_blocked_artifact_exists(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            summary_path = root / "prepared-actions.json"
            packet = {
                "generated_at": "2026-05-01T17:30:00+00:00",
                "items": [
                    {
                        "id": "abc123",
                        "score": 153,
                        "title": "Frontiers reviewer response overdue",
                        "source": "email.high",
                        "reason": "overdue",
                        "next_action": "submit point-by-point response. Thread: 19db1d321f49f543",
                        "approval": "required",
                        "state": "new",
                    }
                ],
            }
            first = self.prepared.build_prepared_actions(
                decision_packet=packet,
                output_dir=root / "prepared-actions",
                ledger_path=root / "action-ledger.json",
                summary_path=summary_path,
                now=datetime(2026, 5, 1, 17, 45, tzinfo=timezone.utc),
            )
            action_dir = Path(first["actions"][0]["artifact_dir"])
            (action_dir / "blocked.md").write_text(
                "Blocked because the real source thread is unavailable. "
                "Albert must provide the missing evidence before finalization.\n"
            )

            second = self.prepared.build_prepared_actions(
                decision_packet=packet,
                output_dir=root / "prepared-actions",
                ledger_path=root / "action-ledger.json",
                summary_path=summary_path,
                now=datetime(2026, 5, 1, 17, 50, tzinfo=timezone.utc),
            )
            third = self.prepared.build_prepared_actions(
                decision_packet=packet,
                output_dir=root / "prepared-actions",
                ledger_path=root / "action-ledger.json",
                summary_path=summary_path,
                now=datetime(2026, 5, 1, 17, 55, tzinfo=timezone.utc),
            )

            self.assertEqual(second["actions"][0]["status"], "blocked")
            self.assertEqual(second["blocked_count"], 1)
            self.assertEqual(second["notification_events"][0]["kind"], "prepared_action_blocked")
            self.assertEqual(third["notification_events"], [])

    def test_mark_done_suppresses_action_with_same_fingerprint(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            packet = {
                "generated_at": "2026-05-01T17:30:00+00:00",
                "items": [
                    {
                        "id": "abc123",
                        "score": 153,
                        "title": "Frontiers reviewer response overdue",
                        "source": "email.high",
                        "reason": "overdue",
                        "next_action": "submit point-by-point response. Thread: 19db1d321f49f543",
                        "approval": "required",
                        "state": "new",
                    }
                ],
            }
            first = self.prepared.build_prepared_actions(
                decision_packet=packet,
                output_dir=root / "prepared-actions",
                ledger_path=root / "action-ledger.json",
                summary_path=root / "prepared-actions.json",
                now=datetime(2026, 5, 1, 17, 45, tzinfo=timezone.utc),
            )
            action = first["actions"][0]

            self.prepared.mark_action(
                action_id=action["id"],
                status="done",
                ledger_path=root / "action-ledger.json",
                fingerprint=action["fingerprint"],
                reason="already done in source system",
                now=datetime(2026, 5, 1, 17, 46, tzinfo=timezone.utc),
            )
            second = self.prepared.build_prepared_actions(
                decision_packet=packet,
                output_dir=root / "prepared-actions",
                ledger_path=root / "action-ledger.json",
                summary_path=root / "prepared-actions.json",
                now=datetime(2026, 5, 1, 17, 50, tzinfo=timezone.utc),
            )

            self.assertEqual(second["actions"][0]["status"], "done")
            self.assertEqual(second["actions"][0]["skip_reason"], "suppressed by action ledger")


class PrepWorkerTests(unittest.TestCase):
    def setUp(self):
        self.worker = load_script("prep_worker")

    def test_selects_needs_draft_actions_without_recent_job(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact_dir = root / "prepared" / "abc"
            artifact_dir.mkdir(parents=True)
            summary = {
                "actions": [
                    {
                        "id": "abc123",
                        "fingerprint": "fp1",
                        "status": "needs_draft",
                        "title": "Frontiers reviewer response overdue",
                        "artifact_dir": str(artifact_dir),
                        "prompt_path": str(artifact_dir / "codex_prompt.md"),
                    },
                    {
                        "id": "skip1",
                        "fingerprint": "fp2",
                        "status": "skipped",
                        "title": "Skipped",
                        "artifact_dir": str(root / "prepared" / "skip"),
                    },
                ]
            }

            selected = self.worker.select_actions(summary, {"jobs": {}}, limit=2)

            self.assertEqual([action["id"] for action in selected], ["abc123"])

    def test_does_not_relaunch_action_with_blocked_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact_dir = root / "prepared" / "abc"
            artifact_dir.mkdir(parents=True)
            (artifact_dir / "blocked.md").write_text("Missing source evidence.\n")
            summary = {
                "actions": [
                    {
                        "id": "abc123",
                        "fingerprint": "fp1",
                        "status": "needs_draft",
                        "title": "Frontiers reviewer response overdue",
                        "artifact_dir": str(artifact_dir),
                        "prompt_path": str(artifact_dir / "codex_prompt.md"),
                    }
                ]
            }

            selected = self.worker.select_actions(summary, {"jobs": {}}, limit=2)

            self.assertEqual(selected, [])

    def test_build_prompt_requires_final_artifact_and_approval_boundary(self):
        action = {
            "id": "abc123",
            "title": "Frontiers reviewer response overdue",
            "artifact_dir": "/tmp/prepared/abc",
            "prompt_path": "/tmp/prepared/abc/codex_prompt.md",
        }

        prompt = self.worker.build_worker_prompt(action)

        self.assertIn("final.md", prompt)
        self.assertIn("Do not send", prompt)
        self.assertIn("Only write final.md", prompt)

    def test_worker_uses_bypass_enabled_codex_exec(self):
        args = self.worker.codex_command_args(
            Path("/tmp/prepared/abc"),
            Path("/tmp/prepared/abc/prep_worker_last_message.md"),
        )

        self.assertIn("--dangerously-bypass-approvals-and-sandbox", args)
        self.assertNotIn("--sandbox", args)

    def test_supervisor_writes_blocked_artifact_when_worker_fails_to_finish(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            action = {
                "id": "abc123",
                "title": "Frontiers reviewer response overdue",
                "source": "email.high",
                "reason": "overdue",
                "next_action": "submit point-by-point response",
            }

            self.worker.write_supervisor_blocked(
                action,
                root,
                "Codex exited without creating final.md or blocked.md.",
                root / "prep_worker.log",
            )

            blocked = root / "blocked.md"
            self.assertTrue(blocked.exists())
            text = blocked.read_text()
            self.assertIn("Codex exited without creating final.md or blocked.md.", text)
            self.assertIn("submit point-by-point response", text)


if __name__ == "__main__":
    unittest.main()
