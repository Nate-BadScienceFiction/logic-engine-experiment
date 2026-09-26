"""Record small, isolated feature probes; these are observations, not a conformance score.

python -B evidence/probe-prolog-features.py --repo C:/path/to/rewrite --output evidence/prolog-features.json
"""
import argparse
import hashlib
import json
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PIN = '9be7804c933cc8a3c51af3d8a5e4f54b012c8be6'


def case(id, query, program='', **options):
    return dict(id=id, query=query, program=program, **options)


CASES = [
    case('rules', 'g(a,c)', 'p(a,b). p(b,c). g(X,Z) :- p(X,Y), p(Y,Z).'),
    case('occurs-check', 'X = f(X)'),
    case('numeric-types', r'1 \= 1.0'),
    case('double-quotes', 'atom("abc")'),
    case('character-code', "X is 0'a, X = 97"),
    case('operators', 'op(500, xfy, likes)'),
    case('duplicates', 'p(X)', 'p(a). p(a).'),
    case('duplicates-opt-out', 'p(X)', 'p(a). p(a).', distinct=False),
    case('cut', 'p(X)', 'p(a) :- !. p(b).'),
    case('if-then-else', '(fail -> fail ; true)'),
    case('soft-cut', '(member(X,[a,b]) *-> true ; fail)'),
    case('negation', r'\+ (X = a, fail), var(X)'),
    case('meta-call', 'call(member, a, [a,b]), once(member(a,[a,a]))'),
    case('arithmetic', 'A is -10 // 3, B is -10 div 3, A = -3, B = -4'),
    case('arithmetic-error', 'X is a + 1'),
    case('lists', 'append([a],[b],L), L = [a,b], member(b,L), length(L,2)'),
    case('findall', 'findall(X,p(X),L), L = [a,a]', 'p(a). p(a).'),
    case('bagof-setof', 'bagof(X,p(X),B), B=[b,a,a], setof(X,p(X),S), S=[a,b]', 'p(b). p(a). p(a).'),
    case('sort', 'sort([b,a,a],S), S=[a,b], msort([b,a,a],M), M=[a,a,b]'),
    case('term-inspection', 'f(a,b) =.. L, L=[f,a,b], functor(f(a,b),f,2), arg(2,f(a,b),b)'),
    case('atom-conversion', "atom_concat(ab,cd,abcd), atom_length(abcd,4), atom_number('42',42)"),
    case('unknown', 'missing_feature_probe'),
    case('unknown-strict', 'missing_feature_probe', unknown_fails=False),
    case('left-recursion', 'path(a,Y)', 'edge(a,b). edge(b,c). path(X,Y) :- path(X,Z), edge(Z,Y). path(X,Y) :- edge(X,Y).', swi_prefix=':- table path/2.\n'),
    case('recursive-cut', 'p(a)', 'p(a) :- !. p(X) :- p(X).'),
    case('recursive-negation', 'win(b)', r'move(a,b). move(b,c). win(X) :- move(X,Y), \+ win(Y).'),
    case('exceptions', 'catch(throw(ball),ball,true)'),
    case('dynamic-database', 'assertz(probe_fact(a)), probe_fact(a), retract(probe_fact(a))'),
    case('dcg', 'phrase(s,[a])', 's --> [a].'),
    case('modules', 'lists:member(a,[a])'),
    case('constraints', 'X #= 2, X #> 1', swi_prefix=':- use_module(library(clpfd)).\n'),
    case('dif', 'dif(X,a), X=b'),
    case('freeze', 'freeze(X, X=b), X=b'),
    case('io', 'write(probe_output)'),
]


def worker(repo, item):
    sys.path.insert(0, str(Path(repo) / 'src'))
    from cyclops import KnowledgeBase
    kb = KnowledgeBase(unknown_fails=item.get('unknown_fails', True))
    phase = 'load'
    try:
        kb.load(item['program'])
        phase = 'query'
        result = kb.ask(item['query'], distinct=item.get('distinct', True))
        # Preserve native term rendering: Python conversion can erase atom/string distinctions.
        return dict(outcome='returned', status=result.status.value, count=len(result),
                    answers=[repr(a) for a in result], steps=result.steps)
    except Exception as exc:
        return dict(outcome='exception', phase=phase, type=type(exc).__name__, message=str(exc))


def run(command, **kwargs):
    try:
        p = subprocess.run(command, capture_output=True, text=True, timeout=10, **kwargs)
        return dict(returncode=p.returncode, stdout=p.stdout, stderr=p.stderr)
    except subprocess.TimeoutExpired:
        return dict(outcome='external-timeout', seconds=10)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True)
    parser.add_argument('--swipl', default='C:/Program Files/swipl/bin/swipl.exe')
    parser.add_argument('--output')
    parser.add_argument('--worker', type=int)
    args = parser.parse_args()
    if args.worker is not None:
        print(json.dumps(worker(args.repo, CASES[args.worker])))
        return
    git = ['git', '-c', 'safe.directory=' + Path(args.repo).resolve().as_posix(), '-C', args.repo]
    revision = subprocess.check_output(git + ['rev-parse', 'HEAD'], text=True).strip()
    if revision != PIN or subprocess.check_output(git + ['status', '--porcelain'], text=True).strip():
        raise SystemExit('Requires clean pinned rewrite ' + PIN)
    report = dict(revision=revision, started_utc=datetime.now(timezone.utc).isoformat(),
                  python=platform.python_version(), platform=platform.platform(),
                  swi=subprocess.check_output([args.swipl, '--version'], text=True).strip(),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), cases=[])
    for i, item in enumerate(CASES):
        rewrite = run([sys.executable, '-B', __file__, '--repo', args.repo, '--worker', str(i)])
        if rewrite.get('returncode') == 0:
            rewrite = json.loads(rewrite['stdout'])
        # Keep side effects, errors and canonical answers in the raw transcript.
        goal = item['query']
        harness = item.get('swi_prefix', '') + item['program'] + '\n'
        harness += ':- initialization(main, main).\n'
        harness += "main :- catch((findall((" + goal + "),(" + goal + "),Rows), length(Rows,N), format('~nCOUNT=~d~n',[N]), write_canonical(Rows), nl), E, (write_canonical(E),nl,halt(2))).\n"
        with tempfile.TemporaryDirectory(prefix='prolog-feature-') as tmp:
            source = Path(tmp) / 'probe.pl'
            source.write_text(harness, encoding='utf-8')
            swi = run([args.swipl, '-q', '-f', 'none', '-s', str(source)])
        report['cases'].append(dict(**item, rewrite=rewrite, swi=swi))
        print(item['id'], json.dumps(rewrite), json.dumps(swi))
    report['finished_utc'] = datetime.now(timezone.utc).isoformat()
    if not args.output:
        raise SystemExit('--output is required')
    Path(args.output).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
