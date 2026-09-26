"""Regression checks for measurement/scoring mistakes, without engine clones."""
import importlib.util
from pathlib import Path
import types
import unittest
from unittest.mock import patch


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


benchmark = load('benchmark', 'benchmark-vs-swi.py')
comparison = load('rerun', 'rerun-comparison.py')


class EvidenceMethods(unittest.TestCase):
    def test_same_count_wrong_bindings_are_rejected(self):
        # SWI returns one answer, but the wrong reversed list. Counts alone pass.
        response = types.SimpleNamespace(stdout='[[[1,2,3]]]\n[0.01]\n')
        with patch.object(benchmark.subprocess, 'run', return_value=response):
            with self.assertRaisesRegex(RuntimeError, 'exact-answer'):
                benchmark.time_swi('unused', '', 'p(R)', [{'R': [3, 2, 1]}], 1, 1)

    def test_swi_collects_all_bindings(self):
        captured = []
        def run(command, **kwargs):
            captured.append(Path(command[-1]).read_text(encoding='utf-8'))
            return types.SimpleNamespace(stdout='[[[1],[2]]]\n[0.01]\n')
        with patch.object(benchmark.subprocess, 'run', side_effect=run):
            benchmark.time_swi('unused', '', 'p(X,Y)', [{'X': [1], 'Y': [2]}], 1, 1)
        self.assertIn('findall([X,Y], (p(X,Y))', captured[0])
        self.assertNotIn('findall(x,', captured[0])

    def test_duplicate_multiplicity_is_not_lost(self):
        row = {'X': [1, 2]}
        self.assertNotEqual(benchmark.canonical([row]), benchmark.canonical([row, row]))

    def test_independent_expected_workloads(self):
        self.assertEqual(benchmark.expected_rows('nrev30')[0]['R'], list(range(30, 0, -1)))
        splits = benchmark.expected_rows('split100')
        self.assertEqual(len(splits), 101)
        self.assertTrue(all(r['X'] + r['Y'] == list(range(1, 101)) for r in splits))
        self.assertEqual({tuple(r['Qs']) for r in benchmark.expected_rows('queens6')},
                         {(2, 4, 6, 1, 3, 5), (3, 6, 2, 5, 1, 4),
                          (4, 1, 5, 2, 6, 3), (5, 3, 1, 6, 4, 2)})

    def test_external_timeout_never_passes(self):
        def forbidden(*args):
            raise AssertionError('Timeout must not reach the old timeout-as-pass policy')
        for termination, outcome in [('unbounded', 'unknown'), ('bounded', 'unknown'), ('complete', 'fail')]:
            case = {'id': 'deadline', 'termination': termination}
            result = comparison.judge(case, None, 'timed_out_query', [], 'sequence', forbidden)
            self.assertEqual(result['outcome'], outcome)

    def test_refusal_normalization_preserves_positive_and_mixed_proofs(self):
        refusal = {'type': 'derived', 'explanation': [{'reason': 'no_derivation_found'}]}
        positive = {'type': 'derived', 'explanation': [{'reason': 'rule_derivation'}]}
        self.assertEqual(comparison.normalize_refusal('why(p)', [refusal]), ([], [refusal]))
        for rows in [[positive], [positive, refusal], [], ['No derivation path found'],
                     [{'type': 'derived', 'explanation': []}]]:
            self.assertEqual(comparison.normalize_refusal('why(p)', rows), (rows, None))
        self.assertEqual(comparison.normalize_refusal('evidence_chain(p)', [refusal]), ([refusal], None))


if __name__ == '__main__':
    unittest.main()
