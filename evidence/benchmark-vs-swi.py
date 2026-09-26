"""Time two classic Prolog benchmarks, and one list case, on the Cyclops Storm rewrite and on SWI-Prolog.

Usage:
    python evidence/benchmark-vs-swi.py <path to the AkiyaBlocks-CyclopsStorm checkout>
        [--swipl "C:/Program Files/swipl/bin/swipl.exe"] [--batches 5] [--json out.json]

The engine repository is private for now; this script is published so the method
can be read and rerun. Both engines load each program once and answer the same
query and materializes full bindings. Exact answer multisets are checked against
independent finite expectations. Native answers and Python value conversion are
timed separately; neither isolates the solver from query/answer setup. Each runs a
few warm-up passes, then times several batches of repeated runs. The figure
reported is the median time per run across batches, in wall-clock time.
"""
import argparse
import json
import platform
import statistics
import subprocess
import sys
import tempfile
import time
import hashlib
import itertools
from pathlib import Path

NREV = """
app([], L, L).
app([H|T], L, [H|R]) :- app(T, L, R).
nrev([], []).
nrev([H|T], R) :- nrev(T, RT), app(RT, [H], R).
"""
QUEENS = """
sel(X, [X|T], T).
sel(X, [H|T], [H|R]) :- sel(X, T, R).
perm([], []).
perm(L, [H|T]) :- sel(H, L, R), perm(R, T).
safe([]).
safe([Q|Qs]) :- noattack(Q, Qs, 1), safe(Qs).
noattack(_, [], _).
noattack(Q, [Q1|Qs], D) :- Q =\\= Q1 + D, Q =\\= Q1 - D, D1 is D + 1, noattack(Q, Qs, D1).
queens(Ns, Qs) :- perm(Ns, Qs), safe(Qs).
"""
LIST30 = '[' + ','.join(str(i) for i in range(1, 31)) + ']'
LIST100 = '[' + ','.join(str(i) for i in range(1, 101)) + ']'
BENCHMARKS = [
    # name, description, program, query, expected answers, runs per batch: engine default, engine untabled, SWI
    ('nrev30', 'Naive reverse of a 30-element list', NREV, f'nrev({LIST30}, R)', 1, 10, 50, 20000),
    ('queens6', 'All solutions of 6-queens', QUEENS, 'queens([1,2,3,4,5,6], Qs)', 4, 3, 5, 1000),
    ('split100', 'All ways to split a 100-item list with app/3', NREV, f'app(X, Y, {LIST100})', 101, 1, 20, 5000),
]


def expected_rows(name):
    """Independent finite expectations, including values and multiplicity."""
    if name == 'nrev30':
        return [{'R': list(range(30, 0, -1))}]
    if name == 'split100':
        values = list(range(1, 101))
        return [{'X': values[:i], 'Y': values[i:]} for i in range(101)]
    return [{'Qs': list(p)} for p in itertools.permutations(range(1, 7))
            if all(abs(p[i] - p[j]) != j - i for i in range(6) for j in range(i + 1, 6))]


def canonical(rows):
    # Sort rows, not their contents; duplicate rows remain observable.
    return sorted(json.dumps(row, sort_keys=True) for row in rows)


def time_engine(checkout, auto_table, program, query, expected, runs, batches, native):
    sys.path.insert(0, str(Path(checkout) / 'src'))
    from cyclops import KnowledgeBase
    kb = KnowledgeBase(auto_table=auto_table)
    kb.load(program)
    result = kb.ask(query, distinct=False)
    answers = result.as_python()
    if not result.complete or canonical(answers) != canonical(expected):
        raise SystemExit(f'{query}: exact-answer validation failed')
    def run():
        result = kb.ask(query, distinct=False)
        if not result.complete:
            raise RuntimeError('Timed query did not complete')
        return result if native else result.as_python()
    for _ in range(2):
        run()
    per_run = []
    for _ in range(batches):
        start = time.perf_counter()
        for _ in range(runs):
            run()
        per_run.append((time.perf_counter() - start) / runs)
    return statistics.median(per_run), per_run, answers


def time_swi(swipl, program, query, expected, runs, batches):
    variables = list(expected[0])
    template = '[' + ','.join(variables) + ']'
    harness = program + f"""
bench_batch(N, S) :- get_time(T0), ( between(1, N, _), findall({template}, ({query}), _), fail ; true ), get_time(T1), S is (T1 - T0) / N.
main :- findall({template}, ({query}), Xs), format("~w~n", [Xs]),
    findall({template}, ({query}), _), findall({template}, ({query}), _),
    findall(S, (between(1, {batches}, _), bench_batch({runs}, S)), Ss), format("~w~n", [Ss]).
"""
    with tempfile.NamedTemporaryFile('w', suffix='.pl', delete=False, encoding='utf-8') as handle:
        handle.write(harness)
        path = handle.name
    try:
        output = subprocess.run([swipl, '-q', '-g', 'main', '-t', 'halt', path], capture_output=True, text=True, check=True, timeout=120).stdout
    finally:
        Path(path).unlink()
    rows_text, timings_text = output.strip().splitlines()
    observed = [dict(zip(variables, values)) for values in json.loads(rows_text)]
    if canonical(observed) != canonical(expected):
        raise RuntimeError('SWI exact-answer validation failed')
    per_run = json.loads(timings_text)
    return statistics.median(per_run), per_run


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('checkout')
    parser.add_argument('--swipl', default='C:/Program Files/swipl/bin/swipl.exe')
    parser.add_argument('--batches', type=int, default=5)
    parser.add_argument('--json')
    args = parser.parse_args()
    checkout = str(Path(args.checkout).resolve()).replace('\\', '/')
    git = ['git', '-c', f'safe.directory={checkout}', '-C', checkout]
    commit = subprocess.check_output(git + ['rev-parse', 'HEAD'], text=True).strip()
    if commit != '9be7804c933cc8a3c51af3d8a5e4f54b012c8be6':
        raise SystemExit('Use the pinned rewrite revision 9be7804')
    if subprocess.check_output(git + ['status', '--porcelain', '--', 'src'], text=True).strip():
        raise SystemExit('Engine source must be clean')
    swi_version = subprocess.run([args.swipl, '--version'], capture_output=True, text=True).stdout.strip()
    report = {'schema_version': 2, 'method': 'full bindings; exact multiset validation; native answers and separate Python conversion',
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'engine_commit': commit, 'python': platform.python_version(), 'swi': swi_version,
              'machine': f'{platform.system()} {platform.release()}, {platform.processor()}',
              'batches': args.batches, 'results': []}
    for name, description, program, query, expected, default_runs, untabled_runs, swi_runs in BENCHMARKS:
        expected = expected_rows(name)
        print(f'Timing {name}: native results, Python conversion, SWI full bindings', flush=True)
        tabled, tabled_runs, _ = time_engine(args.checkout, True, program, query, expected, default_runs, args.batches, True)
        plain, plain_runs, _ = time_engine(args.checkout, False, program, query, expected, untabled_runs, args.batches, True)
        host, host_runs, _ = time_engine(args.checkout, True, program, query, expected, default_runs, args.batches, False)
        host_plain, host_plain_runs, _ = time_engine(args.checkout, False, program, query, expected, untabled_runs, args.batches, False)
        swi, swi_runs_s = time_swi(args.swipl, program, query, expected, swi_runs, args.batches)
        report['results'].append({'name': name, 'description': description, 'query': query, 'answers': len(expected),
                                  'exact_expected_rows': expected, 'program': program,
                                  'runs_per_batch': {'default': default_runs, 'untabled': untabled_runs, 'swi': swi_runs},
                                  'engine_default_ms': tabled * 1000, 'engine_untabled_ms': plain * 1000, 'swi_ms': swi * 1000,
                                  'python_values_default_ms': host * 1000, 'python_values_untabled_ms': host_plain * 1000,
                                  'ratio_default': tabled / swi, 'ratio_untabled': plain / swi,
                                  'batches_ms': {'engine_default': [t * 1000 for t in tabled_runs],
                                                 'python_values_default': [t * 1000 for t in host_runs],
                                                 'python_values_untabled': [t * 1000 for t in host_plain_runs],
                                                 'engine_untabled': [t * 1000 for t in plain_runs],
                                                 'swi': [t * 1000 for t in swi_runs_s]}})
    for row in report['results']:
        print(f"{row['description']}: engine {row['engine_default_ms']:.1f} ms (default), {row['engine_untabled_ms']:.1f} ms "
              f"(auto_table=False); SWI {row['swi_ms']:.4f} ms; {row['ratio_untabled']:,.0f}x to {row['ratio_default']:,.0f}x slower")
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
