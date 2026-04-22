import json
import tempfile
import unittest
from pathlib import Path

from src.sniffer.futura_damper_bridge import derive_damper_identity_from_slave_id, load_damper_map


class DamperMapLoadingTests(unittest.TestCase):
    def load_entries(self, dampers):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "damper-map.json"
            path.write_text(json.dumps({"dampers": dampers}), encoding="utf-8")
            return load_damper_map(path)

    def test_derive_damper_identity_from_slave_id(self):
        self.assertEqual(derive_damper_identity_from_slave_id(72), (1, "privod", 2))
        self.assertEqual(derive_damper_identity_from_slave_id(98), (3, "odtah", 1))

    def test_load_damper_map_derives_missing_fields_and_default_label(self):
        entries = self.load_entries(
            [
                {
                    "slave_id": 72,
                    "room": "Obyvak",
                }
            ]
        )

        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.slave_id, 72)
        self.assertEqual(entry.room, "Obyvak")
        self.assertEqual(entry.zone, 1)
        self.assertEqual(entry.type, "privod")
        self.assertEqual(entry.damper_index, 2)
        self.assertEqual(entry.label, "Obyvak privod 2")
        self.assertTrue(entry.enabled)
        self.assertIsNone(entry.notes)

    def test_load_damper_map_accepts_matching_explicit_fields(self):
        entries = self.load_entries(
            [
                {
                    "slave_id": 98,
                    "room": "Kuchyn",
                    "zone": 3,
                    "type": "odtah",
                    "damper_index": 1,
                    "label": "Kuchyn odtah 1",
                    "enabled": False,
                    "notes": "manual override",
                }
            ]
        )

        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.zone, 3)
        self.assertEqual(entry.type, "odtah")
        self.assertEqual(entry.damper_index, 1)
        self.assertEqual(entry.label, "Kuchyn odtah 1")
        self.assertFalse(entry.enabled)
        self.assertEqual(entry.notes, "manual override")

    def test_load_damper_map_rejects_mismatched_explicit_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "damper-map.json"
            path.write_text(
                json.dumps(
                    {
                        "dampers": [
                            {
                                "slave_id": 72,
                                "room": "Marta",
                                "zone": 5,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                r"slave_id 72.*zone 5, ale odvozena zone je 1\.",
            ):
                load_damper_map(path)

    def test_load_damper_map_rejects_unsupported_non_damper_slave_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "damper-map.json"
            path.write_text(
                json.dumps(
                    {
                        "dampers": [
                            {
                                "slave_id": 16,
                                "room": "Obyvak",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, r"Slave_id 16.*\(64-127\)\."):
                load_damper_map(path)


if __name__ == "__main__":
    unittest.main()
