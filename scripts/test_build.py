"""Tests for scripts/build.py. Run with: python -m unittest discover -s scripts"""

import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

import build


class RepoDataTest(unittest.TestCase):
    def test_repository_entries_are_valid(self):
        _, errors = build.load_entries(build.ROOT)
        self.assertEqual(errors, [])

    def test_generated_files_are_up_to_date(self):
        for path, content in build.outputs(build.ROOT).items():
            self.assertEqual(
                path.read_text(encoding="utf-8"),
                content,
                f"{path.name} is stale; run scripts/build.py",
            )


class ValidationTest(unittest.TestCase):
    """Copies the repository into a temp dir, breaks one entry, and checks the error."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        for name in ("schema", "sources", "ai-records", "pending", "templates"):
            shutil.copytree(build.ROOT / name, self.tmp / name)
        self.path = self.tmp / "sources" / "mathematics" / "erdos-problems.yaml"
        self.entry = yaml.safe_load(self.path.read_text(encoding="utf-8"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def errors_after(self, entry, path=None):
        (path or self.path).write_text(
            yaml.safe_dump(entry, allow_unicode=True), encoding="utf-8"
        )
        _, errors = build.load_entries(self.tmp)
        return errors

    def test_disputed_record_needs_dispute_evidence(self):
        self.entry["ai_records"][0]["disputed"] = True
        errors = self.errors_after(self.entry)
        self.assertTrue(any("dispute_evidence" in error for error in errors), errors)

    def test_size_needs_as_of_date(self):
        del self.entry["size"]["as_of"]
        errors = self.errors_after(self.entry)
        self.assertTrue(any("as_of" in error for error in errors), errors)

    def test_unknown_evidence_level_is_rejected(self):
        self.entry["ai_records"][0]["level"] = "solved"
        errors = self.errors_after(self.entry)
        self.assertTrue(any("ai_records/0/level" in error for error in errors), errors)

    def test_unknown_record_key_is_rejected(self):
        self.entry["ai_records"][0]["rank"] = 1
        errors = self.errors_after(self.entry)
        self.assertTrue(any("rank" in error for error in errors), errors)

    def test_id_must_match_file_name(self):
        self.entry["id"] = "erdos"
        errors = self.errors_after(self.entry)
        self.assertTrue(
            any("must match the file name" in error for error in errors), errors
        )

    def test_field_must_match_directory(self):
        self.path.unlink()
        path = self.tmp / "sources" / "computer-science" / "erdos-problems.yaml"
        errors = self.errors_after(self.entry, path)
        self.assertTrue(
            any("must match the directory" in error for error in errors), errors
        )

    def test_duplicate_url_is_rejected(self):
        self.entry["id"] = "erdos-copy"
        errors = self.errors_after(self.entry, self.path.with_name("erdos-copy.yaml"))
        self.assertTrue(any("duplicates" in error for error in errors), errors)

    def test_size_date_cannot_follow_last_checked(self):
        self.entry["size"]["as_of"] = "2099-01-01"
        errors = self.errors_after(self.entry)
        self.assertTrue(
            any("is after last_checked" in error for error in errors), errors
        )

    def test_invalid_date_is_rejected(self):
        self.entry["last_checked"] = "2026-13-45"
        errors = self.errors_after(self.entry)
        self.assertTrue(any("last_checked" in error for error in errors), errors)

    def test_unquoted_hash_is_rejected(self):
        text = self.path.read_text(encoding="utf-8").replace("description: Database", "description: See #1 in the database")
        self.path.write_text(text, encoding="utf-8")
        _, errors = build.load_entries(self.tmp)
        self.assertTrue(any("starts a YAML comment" in error for error in errors), errors)

    def test_related_source_must_exist(self):
        path = self.tmp / "ai-records" / "openai-astra-ten-results.yaml"
        record = yaml.safe_load(path.read_text(encoding="utf-8"))
        record["related_sources"] = ["no-such-source"]
        errors = self.errors_after(record, path)
        self.assertTrue(any("not a listed source" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
