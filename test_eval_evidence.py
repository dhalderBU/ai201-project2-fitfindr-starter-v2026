"""Recorder checks only: stubbed responses are not acceptance results."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import agent
import run_eval
import scenarios
from tools import search_listings


def local_search(name, arguments):
    assert name == 'search_listings'
    return search_listings(**arguments)


def outfit(new_item, wardrobe):
    return 'Wear with your white sneakers for a vintage vibe.'


def card(outfit, new_item):
    return 'A black graphic tee with a vintage vibe. Wear with white sneakers.'


class EvaluationEvidenceTests(unittest.TestCase):
    def run_scenario(self, scenario, card_function=card):
        with (patch.object(agent, 'call_tool', local_search),
              patch.object(agent, 'suggest_outfit', outfit),
              patch.object(agent, 'create_fit_card', card_function),
              redirect_stdout(io.StringIO())):
            return run_eval.run_once(scenario)

    def test_actual_arguments_and_independent_snapshots(self):
        scenario = next(s for s in scenarios.SCENARIOS if s['criterion'] == 3)
        record = self.run_scenario(scenario)
        self.assertIsNone(record['crashed'])
        search, suggestion, caption = record['calls']
        self.assertTrue(all(call['completed'] for call in record['calls']))
        selected = suggestion['session_before']['selected_item']
        self.assertIn(selected, search['returned'])
        self.assertEqual(suggestion['arguments']['new_item'], selected)
        self.assertEqual(caption['arguments']['new_item'], selected)
        self.assertEqual(caption['arguments']['outfit'], caption['session_before']['outfit_suggestion'])
        self.assertEqual(record['word_count'], len(record['session']['fit_card'].split()))
        record['session']['selected_item']['title'] = 'changed afterwards'
        self.assertNotEqual(selected['title'], 'changed afterwards')
        self.assertEqual(record['input_requests'], [])
        json.dumps(record)

    def test_both_duplicate_branches_and_empty_search(self):
        for scenario in scenarios.SCENARIOS:
            if scenario['criterion'] not in (2, 5):
                continue
            record = self.run_scenario(scenario)
            if scenario['wardrobe'] == 'first_match_owned':
                self.assertEqual(record['session']['selected_item']['id'], 'lst_002')
                self.assertIn('skip wardrobe duplicate', record['trace'])
            else:
                self.assertEqual(len(record['calls']), 1)
                self.assertTrue(record['displayed_response'])
                self.assertIsNone(record['session']['fit_card'])

    def test_failed_tool_keeps_call_and_partial_state(self):
        def broken_card(outfit, new_item):
            raise RuntimeError('recorder test failure')
        record = self.run_scenario(scenarios.SCENARIOS[0], broken_card)
        self.assertIn('recorder test failure', record['crashed'])
        self.assertFalse(record['calls'][-1]['completed'])
        self.assertTrue(record['session']['outfit_suggestion'])
        self.assertIn('suggest_outfit', record['trace'])

    def test_report_has_exactly_five_criterion_rows(self):
        record = self.run_scenario(scenarios.SCENARIOS[0])
        rows = [{'scenario': scenarios.SCENARIOS[0], 'tries': [record] * 5}]
        with tempfile.TemporaryDirectory(dir=run_eval.config.ROOT) as directory:
            with (patch.object(run_eval.config, 'RESULTS_DIR', Path(directory)),
                  redirect_stdout(io.StringIO())):
                run_eval.write_report(rows, SimpleNamespace(tries=5, label='recorder-test'))
            report = next(Path(directory).glob('*.md')).read_text()
        criterion_rows = [line for line in report.splitlines() if line.startswith(tuple(f'| {i}.' for i in range(1, 6)))]
        self.assertEqual(len(criterion_rows), 5)
        self.assertIn('session_before', report)
        self.assertIn('fit-card words:', report)


if __name__ == '__main__':
    unittest.main()
