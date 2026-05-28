import json
import os
import tempfile
import unittest

from storage import Storage


class StorageTest(unittest.TestCase):
    def make_storage(self, initial_data=None):
        temp_dir = tempfile.TemporaryDirectory()
        path = os.path.join(temp_dir.name, "records.json")
        if initial_data is not None:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f)

        storage = Storage(path)
        self.addCleanup(temp_dir.cleanup)
        return storage, path

    def test_legacy_records_load_and_migrate_to_v2(self):
        storage, path = self.make_storage({
            "2026-05-18": [
                {"manager": "pip", "name": "jinja2", "version": "3.1.0"}
            ]
        })

        self.assertEqual(len(storage.get_packages("2026-05-18")), 1)

        storage.save()
        with open(path, "r", encoding="utf-8") as f:
            saved = json.load(f)

        self.assertEqual(saved["metadata"]["schema_version"], 2)
        self.assertIn("2026-05-18", saved["records"])
        self.assertIn("snapshot", saved)

    def test_first_scan_establishes_baseline_without_records(self):
        storage, _ = self.make_storage()

        result = storage.record_scan(
            "2026-05-19",
            [{"manager": "pip", "name": "jinja2", "version": "3.1.0"}],
            "2026-05-19 10:30"
        )

        self.assertTrue(result["is_initial_scan"])
        self.assertEqual(result["new_count"], 0)
        self.assertEqual(storage.get_packages("2026-05-19"), [])
        self.assertEqual(len(storage.get_snapshot_packages()), 1)

    def test_repeated_scan_with_same_packages_adds_nothing(self):
        storage, _ = self.make_storage()
        packages = [{"manager": "pip", "name": "jinja2", "version": "3.1.0"}]

        storage.record_scan("2026-05-19", packages, "2026-05-19 10:30")
        result = storage.record_scan("2026-05-19", packages, "2026-05-19 11:30")

        self.assertFalse(result["is_initial_scan"])
        self.assertEqual(result["new_count"], 0)
        self.assertEqual(storage.get_packages("2026-05-19"), [])

    def test_new_package_after_baseline_is_recorded(self):
        storage, _ = self.make_storage()
        storage.record_scan(
            "2026-05-19",
            [{"manager": "pip", "name": "jinja2", "version": "3.1.0"}],
            "2026-05-19 10:30"
        )

        result = storage.record_scan(
            "2026-05-19",
            [
                {"manager": "pip", "name": "jinja2", "version": "3.1.0"},
                {"manager": "npm", "name": "vite", "version": "6.0.0"}
            ],
            "2026-05-19 11:30"
        )

        records = storage.get_packages("2026-05-19")
        self.assertEqual(result["new_count"], 1)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["manager"], "npm")
        self.assertEqual(records[0]["name"], "vite")
        self.assertEqual(records[0]["time"], "2026-05-19 11:30")

    def test_version_change_is_not_recorded_as_new_install(self):
        storage, _ = self.make_storage()
        storage.record_scan(
            "2026-05-19",
            [{"manager": "pip", "name": "jinja2", "version": "3.1.0"}],
            "2026-05-19 10:30"
        )

        result = storage.record_scan(
            "2026-05-19",
            [{"manager": "pip", "name": "jinja2", "version": "3.1.1"}],
            "2026-05-19 11:30"
        )

        self.assertEqual(result["new_count"], 0)
        self.assertEqual(storage.get_packages("2026-05-19"), [])


if __name__ == "__main__":
    unittest.main()
