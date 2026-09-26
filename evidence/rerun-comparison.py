"""Rerun the frozen corpus with explicit timeout and refusal scoring.

Uses the private harness at the pinned rewrite revision, without modifying it.
External timeouts on unbounded/bounded cases are UNKNOWN, never engine stops.
Complete cases exceeding their deadline fail. Supplemental bounded probes are
reported separately and never substituted into the default-settings score.
"""
from __future__ import annotations

import argparse
import copy
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

REVISIONS = {'old': 'e62758c23f66b26fa92c6d2dafaaf6bf3466499f',
             'new': '9be7804c933cc8a3c51af3d8a5e4f54b012c8be6'}


def normalize_refusal(goal, rows):
    """Only the predecessor's structured why/1 refusal; never arbitrary text."""
    if not goal.startswith('why(') or not isinstance(rows, list) or not rows:
        return rows, None
    if all(isinstance(row, dict) and row.get('type') == 'derived'
           and isinstance(row.get('explanation'), list) and row['explanation']
           and all(isinstance(item, dict) and item.get('reason') == 'no_derivation_found'
                   for item in row['explanation']) for row in rows):
        return [], rows
    return rows, None


def judge(case, result, note, expected, order, legacy_judge):
    if result is None and note.startswith('timed_out'):
        return {'case': case['id'], 'engine': '?',
                'outcome': 'fail' if case['termination'] == 'complete' else 'unknown',
                'reason': 'External deadline exceeded; engine completion status was not observed',
                'unsound_completeness': False, 'unobservable': 0, 'rows': []}
    return asdict(legacy_judge(case, result, note, expected, order))


def worker(args):
    sys.path[:0] = [str(args.new_repo / 'scripts'), str(args.root / 'src')]
    from comparison import worker as legacy
    original_old_query = legacy.OldEngine.query

    def old_query(self, goal):
        rows, meta = original_old_query(self, goal)
        rows, refusal = normalize_refusal(goal, rows)
        if refusal is not None:
            meta['raw_refusal'] = refusal
            meta['normalization'] = 'Structured why/1 no_derivation_found is a refusal, not proof'
        return rows, meta

    legacy.OldEngine.query = old_query
    if args.bounded:
        def bounded_query(self, goal):
            from cyclops import Limits
            result = self.kb.ask(goal, limits=Limits(steps=20_000, max_answers=32))
            return result.as_python(), {'status': result.status.name, 'notes': list(result.notes),
                                        'steps': result.steps}
        legacy.NewEngine.query = bounded_query
    case = json.loads(args.case.read_text(encoding='utf-8'))
    result = legacy.run_case(args.engine, case, args.phase)
    args.result.write_text(json.dumps(result), encoding='utf-8')


def run_worker(engine, case, root, new_repo, bounded=False):
    from comparison.compare import _clean_env
    with tempfile.TemporaryDirectory(prefix='cyclops-revised-') as folder:
        directory = Path(folder)
        case_path, output, phase = [directory / name for name in ('case.json', 'result.json', 'phase.txt')]
        case_path.write_text(json.dumps(case), encoding='utf-8')
        command = [sys.executable, '-B', str(Path(__file__).resolve()), '--worker',
                   '--engine', engine, '--root', str(root), '--new-repo', str(new_repo),
                   '--case', str(case_path), '--result', str(output), '--phase', str(phase)]
        if bounded:
            command.append('--bounded')
        env = {**_clean_env(), 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONHASHSEED': '0'}
        try:
            process = subprocess.run(command, cwd=root, env=env, capture_output=True,
                                     text=True, timeout=float(case.get('timeout', 30)))
        except subprocess.TimeoutExpired:
            stage = phase.read_text() if phase.exists() else 'before_query'
            return None, 'timed_out_' + stage
        if process.returncode or not output.exists():
            return None, 'worker_error: ' + process.stderr[-2000:]
        return json.loads(output.read_text(encoding='utf-8')), ''


def self_test(legacy_judge):
    case = {'id': 'test', 'termination': 'unbounded'}
    assert judge(case, None, 'timed_out_query', None, 'sequence', legacy_judge)['outcome'] == 'unknown'
    case['termination'] = 'complete'
    assert judge(case, None, 'timed_out_query', None, 'sequence', legacy_judge)['outcome'] == 'fail'
    refusal = [{'type': 'derived', 'explanation': [{'reason': 'no_derivation_found'}]}]
    assert normalize_refusal('why(p)', refusal) == ([], refusal)
    assert normalize_refusal('evidence_chain(p)', refusal) == (refusal, None)
    positive = [{'type': 'derived', 'explanation': [{'reason': 'rule_derivation'}]}]
    assert normalize_refusal('why(p)', positive) == (positive, None)
    assert normalize_refusal('why(p)', positive + refusal) == (positive + refusal, None)
    assert normalize_refusal('why(p)', [{'type': 'derived', 'explanation': []}])[1] is None
    print('Scoring regression checks passed', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old-repo', type=Path)
    parser.add_argument('--new-repo', required=True, type=Path)
    parser.add_argument('--swipl', default='C:/Program Files/swipl/bin/swipl.exe')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--bounded', action='store_true')
    parser.add_argument('--engine')
    for name in ('root', 'case', 'result', 'phase'):
        parser.add_argument('--' + name, type=Path)
    args = parser.parse_args()
    args.new_repo = args.new_repo.resolve()
    if args.worker:
        worker(args)
        return
    sys.path.insert(0, str(args.new_repo / 'scripts'))
    from comparison.compare import _judge, _expected_rows
    from comparison.corpus import load_corpus
    self_test(_judge)
    if args.self_test:
        return
    if not args.old_repo or not args.output:
        parser.error('--old-repo and --output are required for a rerun')
    roots = {'old': args.old_repo.resolve(), 'new': args.new_repo}
    for engine, root in roots.items():
        git = ['git', '-c', 'safe.directory=' + root.as_posix(), '-C', str(root)]
        actual = subprocess.check_output(git + ['rev-parse', 'HEAD'], text=True).strip()
        if actual != REVISIONS[engine]:
            raise SystemExit(f'{engine}: expected {REVISIONS[engine]}, found {actual}')
        if subprocess.check_output(git + ['status', '--porcelain', '--', 'src', 'scripts/comparison'], text=True).strip():
            raise SystemExit(f'{engine}: source/harness must be clean')
    corpus = Path(__file__).with_name('cases-2026-09-24.json')
    cases = load_corpus(corpus)
    report = {'schema_version': 2, 'complete': False, 'started_utc': datetime.now(timezone.utc).isoformat(),
              'revisions': REVISIONS, 'python': platform.python_version(), 'platform': platform.platform(),
              'swipl': subprocess.check_output([args.swipl, '--version'], text=True).strip(),
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'corpus_sha256': hashlib.sha256(corpus.read_bytes()).hexdigest(),
              'policy': 'External unbounded/bounded timeout = unknown; complete timeout = fail; structured why refusal normalized',
              'cases': [], 'supplemental_bounded': []}
    for case in cases:
        expected, order, oracle_note = _expected_rows(case, args.swipl)
        entry = {'id': case['id'], 'oracle': case['oracle'], 'oracle_note': oracle_note,
                 'expected_rows': expected, 'order': order, 'engines': {}}
        for engine, root in roots.items():
            result, note = run_worker(engine, case, root, args.new_repo)
            verdict = judge(case, result, note, expected, order, _judge)
            verdict['engine'] = engine
            entry['engines'][engine] = {'verdict': verdict, 'worker_result': result, 'worker_note': note}
            print(f'{engine} {case["id"]}: {verdict["outcome"]}', flush=True)
        report['cases'].append(entry)
        args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    for case in cases:
        if case['termination'] != 'unbounded':
            continue
        result, note = run_worker('new', case, roots['new'], args.new_repo, bounded=True)
        expected, order, _ = _expected_rows(case, args.swipl)
        report['supplemental_bounded'].append({'id': case['id'], 'limits': {'steps': 20000, 'max_answers': 32},
            'verdict': judge(case, result, note, expected, order, _judge), 'worker_result': result, 'worker_note': note})
    report['counts'] = {engine: dict(Counter(c['engines'][engine]['verdict']['outcome'] for c in report['cases']))
                        for engine in roots}
    report['complete'] = True
    report['finished_utc'] = datetime.now(timezone.utc).isoformat()
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report['counts']), flush=True)


if __name__ == '__main__':
    main()
