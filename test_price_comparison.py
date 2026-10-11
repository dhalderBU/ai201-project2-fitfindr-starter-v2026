"""Offline checks for the price-comparison stretch features.

Run with: python -m unittest -v test_price_comparison
Only model-dependent steps are replaced in the agent checks.
"""

import io
import unittest
from contextlib import redirect_stdout
from copy import deepcopy
from unittest.mock import Mock, call, patch

import agent
import app
import tools
import trace


def listing(item_id, price, category="tops"):
    return {
        "id": item_id,
        "title": "Graphic Tee",
        "description": "graphic tee",
        "category": category,
        "price": price,
        "size": "M",
        "colors": ["black"],
        "platform": "depop",
    }


class ComparePriceTests(unittest.TestCase):
    def test_average_uses_all_category_peers_excluding_selected_id(self):
        item = listing("selected", 25.0)
        rows = [
            item,
            listing("low", 15.0),
            listing("middle", 35.0),
            listing("high", 100.0),
            listing("other-category", 200.0, "shoes"),
        ]
        original = deepcopy(rows)
        with patch("tools.load_listings", return_value=rows):
            result = tools.compare_price(item)
        self.assertEqual(result, {
            "listing_id": "selected",
            "category": "tops",
            "item_price": 25.0,
            "comparison_count": 3,
            "average_price": 50.0,
            "difference": -25.0,
            "status": "below_average",
        })
        self.assertEqual(rows, original)

    def test_above_below_and_equal_to_cent_rounded_average(self):
        peers = [listing("a", 10.0), listing("b", 10.0), listing("c", 10.01)]
        for price, status, difference in [
            (11.0, "above_average", 1.0),
            (9.0, "below_average", -1.0),
            (10.0, "at_average", 0.0),
        ]:
            with self.subTest(price=price):
                with patch("tools.load_listings", return_value=peers):
                    result = tools.compare_price(listing("selected", price))
                self.assertEqual(result["average_price"], 10.0)
                self.assertEqual(result["difference"], difference)
                self.assertEqual(result["status"], status)

    def test_no_peers_returns_explicit_unavailable_values(self):
        item = listing("selected", 25.0)
        for rows in ([], [item], [item, listing("other", 50.0, "shoes")]):
            with self.subTest(rows=rows):
                with patch("tools.load_listings", return_value=rows):
                    result = tools.compare_price(item)
                self.assertEqual(result["comparison_count"], 0)
                self.assertIsNone(result["average_price"])
                self.assertIsNone(result["difference"])
                self.assertEqual(result["status"], "insufficient_data")


class PriceBranchTests(unittest.TestCase):
    def tearDown(self):
        trace.start_trace(enabled=False)

    def run_case(self, rows, wardrobe=None):
        wardrobe = {"items": []} if wardrobe is None else wardrobe
        events = Mock()
        output = io.StringIO()
        with (
            patch("tools.load_listings", return_value=rows),
            patch("agent.search_listings", wraps=tools.search_listings) as search,
            patch("agent.compare_price", wraps=tools.compare_price) as compare,
            patch("agent.suggest_outfit", return_value="Wear with white sneakers.") as outfit,
            patch("agent.create_fit_card", return_value="A graphic tee outfit.") as card,
            redirect_stdout(output),
        ):
            for name, mock in [("search", search), ("compare", compare),
                               ("outfit", outfit), ("card", card)]:
                events.attach_mock(mock, name)
            session = app._ask_one("graphic tee under $30", wardrobe, True)
        return session, events.mock_calls, output.getvalue()

    def test_above_average_branch_displays_warning_and_preserves_handoffs(self):
        item = listing("selected", 25.0)
        session, calls, output = self.run_case([item, listing("peer", 15.0)])
        self.assertIsNone(session["error"])
        self.assertEqual(session["selected_item"], item)
        self.assertEqual(session["price_comparison"]["average_price"], 15.0)
        self.assertEqual(calls, [
            call.search("graphic tee", None, 30.0),
            call.compare(item),
            call.outfit(item, {"items": []}),
            call.card("Wear with white sneakers.", item),
        ])
        self.assertEqual(session["fit_card_inputs"]["new_item"], item)
        self.assertEqual(session["fit_card"], "A graphic tee outfit.")
        self.assertIn("above-average price branch", output)
        self.assertIn("peers=1; average=15.0; difference=10.0", output)
        self.assertIn("Price warning: This item is $10.00 above", output)

    def test_nonwarning_paths_continue_and_do_not_reuse_previous_warning(self):
        self.run_case([listing("selected", 25.0), listing("peer", 15.0)])
        for peer_price, status in [(40.0, "below_average"), (25.0, "at_average")]:
            with self.subTest(status=status):
                session, calls, output = self.run_case([
                    listing("selected", 25.0), listing("peer", peer_price),
                ])
                self.assertEqual(session["price_comparison"]["status"], status)
                self.assertIsNone(session["price_warning"])
                self.assertIsNone(session["error"])
                self.assertEqual(len(calls), 4)
                self.assertIn("price comparison: no warning", output)
                self.assertNotIn("Price warning:", output)

    def test_no_peers_continues_without_a_warning(self):
        session, calls, output = self.run_case([listing("selected", 25.0)])
        self.assertEqual(session["price_comparison"]["status"], "insufficient_data")
        self.assertIsNone(session["price_warning"])
        self.assertIsNone(session["error"])
        self.assertEqual(len(calls), 4)
        self.assertIn("no other listings in this category", output)

    def test_empty_search_stops_before_comparison_and_model_tools(self):
        session, calls, output = self.run_case([])
        self.assertEqual(calls, [call.search("graphic tee", None, 30.0)])
        self.assertIsNone(session["price_comparison"])
        self.assertIsNone(session["price_warning"])
        self.assertIsNone(session["fit_card"])
        self.assertIn("Try broader keywords", session["error"])
        self.assertNotIn("Category average:", output)

    def test_all_owned_stops_before_comparison_and_model_tools(self):
        wardrobe = {"items": [{
            "name": "Graphic Tee", "category": "tops", "colors": ["black"],
        }]}
        session, calls, output = self.run_case([listing("selected", 25.0)], wardrobe)
        self.assertEqual(calls, [call.search("graphic tee", None, 30.0)])
        self.assertIsNone(session["price_comparison"])
        self.assertIsNone(session["price_warning"])
        self.assertIsNone(session["fit_card"])
        self.assertIn("already appear", session["error"])
        self.assertIn("wardrobe-owned branch", output)


if __name__ == "__main__":
    unittest.main()
