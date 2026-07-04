#!/usr/bin/env python3
"""Regression tests for screenpipe SQLite fallback extraction."""

import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("extract_raw_data.py")
SPEC = importlib.util.spec_from_file_location("extract_raw_data", SCRIPT_PATH)
extract_raw_data = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(extract_raw_data)


class ScreenpipeSqliteFallbackTests(unittest.TestCase):
    def test_current_schema_without_ocr_text_returns_frame_elements(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "screenpipe.sqlite"
            conn = sqlite3.connect(db_path)
            conn.executescript(
                """
                CREATE TABLE frames (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    name TEXT,
                    app_name TEXT,
                    window_name TEXT,
                    browser_url TEXT,
                    focused INTEGER,
                    full_text TEXT,
                    accessibility_text TEXT
                );
                CREATE TABLE elements (
                    frame_id INTEGER,
                    text TEXT,
                    source TEXT
                );
                CREATE TABLE audio_transcriptions (
                    timestamp TEXT,
                    transcription TEXT,
                    speaker_id INTEGER,
                    start_time REAL,
                    end_time REAL
                );
                CREATE TABLE speakers (
                    id INTEGER PRIMARY KEY,
                    name TEXT
                );
                INSERT INTO frames
                    (id, timestamp, name, app_name, window_name, browser_url, focused, full_text, accessibility_text)
                VALUES
                    (1, '2026-06-27T18:00:00Z', 'frame-1', 'Google Chrome', 'Gmail', 'https://mail.google.com', 1, '', '');
                INSERT INTO elements (frame_id, text, source)
                VALUES (1, 'Donghyun manuscript revision Reviewer 2 Comment 4', 'ocr');
                """
            )
            conn.commit()
            conn.close()

            original_db = extract_raw_data.SCREENPIPE_DB
            extract_raw_data.SCREENPIPE_DB = db_path
            try:
                result = extract_raw_data.query_screenpipe_sqlite(
                    "2026-06-27T00:00:00Z",
                    "2026-06-28T00:00:00Z",
                    limit=10,
                )
            finally:
                extract_raw_data.SCREENPIPE_DB = original_db

        self.assertEqual(len(result["data"]), 1)
        item = result["data"][0]
        self.assertEqual(item["type"], "OCR")
        self.assertIn("Reviewer 2 Comment 4", item["content"]["text"])
        self.assertEqual(item["content"]["app_name"], "Google Chrome")


if __name__ == "__main__":
    unittest.main()
