"""Style-memory checks using the standard library and isolated storage.

Run with: python -m unittest -v test_wardrobe_memory test_price_comparison
"""

import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import agent
import app
import trace
from utils import data_loader as data


class WardrobeMemoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "wardrobe.json"
        self.environment = patch.dict(os.environ, {"FITFINDR_WARDROBE_PATH": str(self.path)})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.addCleanup(trace.start_trace, False)

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(Path(app.__file__)), *args],
            cwd=self.directory.name, capture_output=True, text=True, check=True,
        ).stdout

    def test_initializes_from_same_example_once_then_loads_saved_items(self):
        expected = data.get_example_wardrobe()
        wardrobe, source = data.load_wardrobe()
        self.assertEqual(source, "initialized")
        self.assertEqual(wardrobe, expected)
        with patch.object(data, "get_example_wardrobe", side_effect=AssertionError("reseeded")):
            loaded, source = data.load_wardrobe()
        self.assertEqual(source, "saved")
        self.assertEqual(loaded, expected)

    def test_add_remove_preserve_other_items_and_original_example(self):
        original = data.get_example_wardrobe()
        added, count = data.add_wardrobe_item("Purple trousers", "bottoms", ["purple"], ["casual"])
        self.assertEqual(count, len(original["items"]) + 1)
        self.assertEqual(added["id"], "w_011")
        loaded, _ = data.load_wardrobe()
        self.assertEqual(loaded["items"][:-1], original["items"])
        self.assertEqual(loaded["items"][-1], added)
        removed, count = data.remove_wardrobe_item("w_001")
        self.assertEqual(removed, original["items"][0])
        self.assertEqual(count, len(original["items"]))
        loaded, _ = data.load_wardrobe()
        self.assertEqual(loaded["items"], original["items"][1:] + [added])
        self.assertEqual(data.get_example_wardrobe(), original)

    def test_removing_last_item_keeps_empty_memory_on_later_runs(self):
        only_item = data.get_example_wardrobe()["items"][0]
        data.save_wardrobe({"items": [only_item]})
        data.remove_wardrobe_item(only_item["id"])
        with patch.object(data, "get_example_wardrobe", side_effect=AssertionError("reseeded")):
            wardrobe, source = data.load_wardrobe()
        self.assertEqual(wardrobe, {"items": []})
        self.assertEqual(source, "saved")

    def test_duplicate_and_unknown_removal_do_not_change_memory(self):
        data.load_wardrobe()
        before = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "already saved as w_007"):
            data.add_wardrobe_item(" chunky  WHITE sneakers ", "shoes", ["WHITE"])
        with self.assertRaisesRegex(ValueError, "wardrobe list"):
            data.remove_wardrobe_item("missing")
        self.assertEqual(self.path.read_bytes(), before)

    def test_invalid_memory_is_reported_without_overwriting_it(self):
        for content in ('{broken', '{"items": null}', '{"items": [{"id": "x"}]}'):
            with self.subTest(content=content):
                self.path.write_text(content)
                with self.assertRaisesRegex(ValueError, "retry"):
                    data.load_wardrobe()
                self.assertEqual(self.path.read_text(), content)

    def test_invalid_new_item_does_not_initialize_or_change_memory(self):
        for name, category, colors in [(" ", "tops", ["red"]), ("Tee", "unknown", ["red"]),
                                       ("Tee", "tops", [" "])]:
            with self.subTest(name=name, category=category):
                with self.assertRaises(ValueError):
                    data.add_wardrobe_item(name, category, colors)
                self.assertFalse(self.path.exists())

    def test_failed_save_keeps_previous_json_and_cleans_temporary_file(self):
        data.load_wardrobe()
        before = self.path.read_bytes()
        with patch.object(data.os, "replace", side_effect=OSError("disk unavailable")):
            with self.assertRaisesRegex(OSError, "disk unavailable"):
                data.save_wardrobe({"items": []})
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])

    def test_cli_add_list_remove_persist_across_separate_processes(self):
        output = self.run_cli("wardrobe", "add", "--name", "Purple trousers",
                              "--category", "bottoms", "--colors", "purple")
        self.assertIn("Added w_011", output)
        self.assertIn("Saved wardrobe: 11 items", output)
        self.assertIn("w_011  Purple trousers", self.run_cli("wardrobe", "list"))
        self.assertIn("Removed w_011", self.run_cli("wardrobe", "remove", "--id", "w_011"))
        output = self.run_cli("wardrobe", "list")
        self.assertIn("Loaded saved wardrobe: 10 items", output)
        self.assertNotIn("Purple trousers", output)

    def test_second_run_uses_saved_item_in_agent_duplicate_branch(self):
        query = "vintage graphic tee under $30"
        original_wardrobe = data.get_example_wardrobe()
        from tools import search_listings
        baseline = next(item for item in search_listings("vintage graphic tee", max_price=30)
                        if not agent._listing_in_wardrobe(item, original_wardrobe))
        self.run_cli("wardrobe", "add", "--name", baseline["title"],
                     "--category", baseline["category"], "--colors", *baseline["colors"])
        loaded, _ = data.load_wardrobe()
        output = io.StringIO()
        with (
            patch("agent.suggest_outfit", return_value="An outfit from the saved wardrobe.") as outfit,
            patch("agent.create_fit_card", return_value="A fit card."),
            redirect_stdout(output),
        ):
            args = app.build_parser().parse_args(["ask", query, "--trace"])
            args.func(args)
        self.assertNotEqual(outfit.call_args.args[0]["id"], baseline["id"])
        self.assertEqual(outfit.call_args.args[1], loaded)
        self.assertIn("source=saved; items=11", output.getvalue())
        self.assertIn("w_011: " + baseline["title"], output.getvalue())
        self.assertIn("skip wardrobe duplicate", output.getvalue())

    def test_empty_override_does_not_load_or_modify_saved_memory(self):
        self.path.write_text("{not valid JSON")
        output = self.run_cli("ask", "designer ballgown size XXS under $5",
                              "--empty-wardrobe", "--trace")
        self.assertIn("source=empty override; items=0", output)
        self.assertIn("No listings matched", output)
        self.assertEqual(self.path.read_text(), "{not valid JSON")


if __name__ == "__main__":
    unittest.main()
