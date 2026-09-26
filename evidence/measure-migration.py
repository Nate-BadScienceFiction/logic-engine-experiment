"""Measure pinned Git trees and verify the file-level test migration inventory.

Physical lines include blanks/comments. AST functions include methods and nested
definitions. Historical collected-case counts are read from the ledger, not
recollected. Input repositories are read only.
"""
import argparse
import ast
from collections import Counter, defaultdict
import hashlib
import io
import json
from pathlib import Path
import re
import statistics
import subprocess
import tarfile

REVISIONS = {'old': 'e62758c23f66b26fa92c6d2dafaaf6bf3466499f',
             'new': '9be7804c933cc8a3c51af3d8a5e4f54b012c8be6'}


def snapshot(root, revision):
    root = root.resolve()
    raw = subprocess.check_output(['git', '-c', 'safe.directory=' + root.as_posix(),
                                   '-C', str(root), 'archive', revision])
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        return {m.name: archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}


def measure(files, prefix):
    counts, spans = Counter(), []
    for name, raw in files.items():
        if not name.startswith(prefix) or not name.endswith('.py'):
            continue
        source = raw.decode('utf-8-sig')
        tree = ast.parse(source)
        functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        spans.extend(n.end_lineno - n.lineno + 1 for n in functions)
        counts.update(files=1, physical_lines=len(source.splitlines()), functions=len(functions),
                      classes=sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree)))
    result = dict(counts)
    if spans:
        result.update(function_span_median=statistics.median(spans),
                      function_span_p90=sorted(spans)[int(.9 * (len(spans) - 1))],
                      function_span_max=max(spans))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old-repo', type=Path, required=True)
    parser.add_argument('--new-repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    old = snapshot(args.old_repo, REVISIONS['old'])
    new = snapshot(args.new_repo, REVISIONS['new'])
    ledger = new['docs/TEST_MIGRATION_LEDGER.md']
    rows = re.findall(r'^\| \d+ \| `([^`]+)` \| (\d+) \| (\d+) \| ([ACROXB]) \|',
                      ledger.decode('utf-8'), re.M)
    inventory, totals = [], defaultdict(Counter)
    for name, definitions, cases, disposition in rows:
        tree = ast.parse(old['tests/' + name].decode('utf-8-sig'))
        actual = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith('test_')
                     for n in ast.walk(tree))
        if actual != int(definitions):
            raise RuntimeError(f'Definition mismatch: {name}')
        totals[disposition].update(files=1, definitions=actual, historical_collected_cases=int(cases))
        inventory.append(dict(file=name, disposition=disposition, definitions=actual,
                              historical_collected_cases=int(cases)))
    source_files = {name[6:] for name, raw in old.items() if name.startswith('tests/') and name.endswith('.py')
                    and any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith('test_')
                            for n in ast.walk(ast.parse(raw.decode('utf-8-sig'))))}
    if len(rows) != len(source_files) or {r['file'] for r in inventory} != source_files:
        raise RuntimeError('Inventory is not a complete, unique mapping of test files')
    report = {'revisions': REVISIONS, 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'ledger_sha256': hashlib.sha256(ledger).hexdigest(),
              'method': 'splitlines; AST definitions; p90 indexed at floor(.9*(n-1)); historical cases from ledger',
              'old_package': measure(old, 'src/kb/'), 'old_all_src': measure(old, 'src/'),
              'old_tools': measure(old, 'src/tools/'), 'new_package': measure(new, 'src/cyclops/'),
              'old_tests': measure(old, 'tests/'), 'new_tests': measure(new, 'tests/'),
              'dispositions': dict(totals), 'inventory': inventory}
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Verified', len(rows), 'unique file mappings; saved', args.output)


if __name__ == '__main__':
    main()
