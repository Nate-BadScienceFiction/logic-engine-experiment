"""Replay the frozen 21-case comparison at selected historical revisions.

Requires Python 3.12+, Git, SWI-Prolog, and local clones with the listed commits.
Only newly created scratch clones are checked out. Input repositories are read.
The scratch directory is retained for inspection. No engine or harness edits.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys


HARNESS = "9be7804c933cc8a3c51af3d8a5e4f54b012c8be6"
SEED = "5fce203ca2da4d5942a8ed4a4217d8bf18c04544"
# Chosen before replaying: every new-engine src-changing commit, then the
# published endpoint; first compatible old import layout, then each month's
# last commit (May-August). Different sampling densities are intentional.
REVISIONS = {
    "new": [
        "3ae199b04fdc7003646468661e9043845eb1b438",
        "0b231e62e42c0b80894f2bb1e7eabade04c11002",
        "08c64ff72247c3c1ae1240f408267007ecb8b75b",
        "f98ac6b24684c8dedc37bfc1fd4c7715cadda85a",
        "6f4161a78c19c10f9e8ed9b3dbb06fd6a66e4e80",
        HARNESS,
    ],
    "old": [
        "7cfca576e5c4029338048d4511a85cc3c46b7a47",
        "b6b299185487bd3a3d3ac9e95f03ce98d58ea3dc",
        "9c06533c00b6d42da03e3a0f71c8e4012fe2b62d",
        "9cff53c3c436e56495d1d37a87eeacdfe7ad6cfd",
        "e62758c23f66b26fa92c6d2dafaaf6bf3466499f",
    ],
}


def run(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(
        list(args), cwd=cwd, check=True, capture_output=True,
        text=True, encoding="utf-8", timeout=120,
    ).stdout.strip()


def git(root: Path, *args: str) -> str:
    return run("git", "-C", str(root), *args)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def revision(root: Path, commit: str) -> dict:
    fields = git(root, "show", "-s", "--format=%H%n%aI%n%cI%n%s", commit).splitlines()
    return dict(zip(("revision", "author_date", "committer_date", "subject"), fields))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-repo", required=True, type=Path)
    parser.add_argument("--new-repo", required=True, type=Path)
    parser.add_argument("--work-dir", required=True, type=Path, help="Must not exist")
    parser.add_argument("--output", required=True, type=Path, help="Must not exist")
    parser.add_argument("--swipl", default="swipl")
    parser.add_argument("--reference", type=Path,
                        default=Path(__file__).with_name("comparison-2026-09-24.json"))
    args = parser.parse_args()
    args.work_dir = args.work_dir.resolve()
    args.output = args.output.resolve()
    if args.work_dir.exists() or args.output.exists():
        parser.error("Use a new work directory and output file; existing paths are not replaced.")
    sources = {"new": args.new_repo.resolve(), "old": args.old_repo.resolve()}
    for engine, source in sources.items():
        if any(path.is_relative_to(source) for path in (args.work_dir, args.output)):
            parser.error("Work directory and output must be outside the input repositories")
        if Path(git(source, "rev-parse", "--show-toplevel")).resolve() != source:
            parser.error(f"{engine}: supply the repository root")
        for commit in REVISIONS[engine]:
            git(source, "cat-file", "-e", commit + "^{commit}")
    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    if reference["revisions"] != {e: revisions[-1] for e, revisions in REVISIONS.items()}:
        parser.error("Reference endpoints do not match the pinned revisions")
    swi_version = run(args.swipl, "--version")
    if swi_version != reference["swipl"]["version"]:
        parser.error(f"Use the reference oracle version: {reference['swipl']['version']}")
    args.work_dir.mkdir(parents=True)

    def clone(name: str, source: Path, commit: str) -> Path:
        root = args.work_dir / name
        # Exact, process-local trust for this explicitly supplied local source.
        run("git", "-c", f"safe.directory={(source / '.git').as_posix()}",
            "clone", "--no-hardlinks", "--no-checkout", str(source), str(root))
        git(root, "checkout", "--detach", commit)
        return root

    harness_root = clone("harness", sources["new"], HARNESS)
    sys.path.insert(0, str(harness_root / "scripts"))
    from comparison.compare import _expected_rows, _judge, _run_worker
    from comparison.corpus import load_corpus

    corpus_path = harness_root / "comparison" / "cases.json"
    cases = load_corpus(corpus_path)
    if {c["id"] for c in cases} != set(reference["verdicts"]):
        raise RuntimeError("Frozen corpus and reference have different cases")
    expected = {}
    for case in cases:
        rows, order, note = _expected_rows(case, args.swipl)
        if case["oracle"]["kind"] == "swipl" and rows is None:
            raise RuntimeError(f"Oracle unavailable for {case['id']}: {note}")
        expected[case["id"]] = {"rows": rows, "order": order, "note": note}

    report = {
        "schema_version": 1,
        "complete": False,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {"python": platform.python_version(),
                        "platform": platform.platform(), "swipl": swi_version},
        "harness_revision": HARNESS,
        "script_sha256": digest(Path(__file__)),
        "corpus_git_blob": git(harness_root, "rev-parse", HARNESS + ":comparison/cases.json"),
        "reference_sha256": digest(args.reference),
        "scheduled_per_snapshot": len(cases),
        "sampling": {
            "new": "Every commit changing src, then the published endpoint (no src changes since the preceding sample).",
            "old": "First compatible import layout, then last commit of each month May-August 2026. Earlier layouts not assessed.",
            "revisions_selected_before_replay": REVISIONS,
        },
        "seed_commit": revision(harness_root, SEED),
        "expected": expected,
        "snapshots": [],
        "endpoint_verdicts_match_reference": {},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Reserve the requested output name before running any historical workers.
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)

    for engine, commits in REVISIONS.items():
        for commit in commits:
            # Separate clones prevent ignored bytecode from crossing revisions.
            root = clone(f"{engine}-{commit[:7]}", sources[engine], commit)
            if git(root, "status", "--porcelain", "--untracked-files=no"):
                raise RuntimeError("Tracked snapshot files changed")
            snapshot = {"engine": engine, **revision(root, commit),
                        "source_tree": git(root, "rev-parse", commit + ":src"), "cases": {}}
            print(f"Running {engine} {commit[:7]} ({len(cases)} cases)", flush=True)
            for case in cases:
                expectation = expected[case["id"]]
                result, worker_note = _run_worker(
                    engine, case, sys.executable, root, float(case.get("timeout", 30)))
                verdict = _judge(case, result, worker_note, expectation["rows"], expectation["order"])
                snapshot["cases"][case["id"]] = {
                    "verdict": asdict(verdict), "worker_note": worker_note, "worker_result": result}
            counts = Counter(item["verdict"]["outcome"] for item in snapshot["cases"].values())
            snapshot["counts"] = {key: counts[key] for key in ("pass", "fail", "unknown")}
            if sum(snapshot["counts"].values()) != len(cases):
                raise RuntimeError("Pass/fail/unknown counts do not account for every case")
            snapshot["passes_by_external_timeout"] = sum(
                item["verdict"]["outcome"] == "pass" and item["worker_note"] == "timed_out"
                for item in snapshot["cases"].values())
            if git(root, "status", "--porcelain", "--untracked-files=no"):
                raise RuntimeError("Workers changed tracked snapshot files")
            report["snapshots"].append(snapshot)
            mismatches = []
            if commit == commits[-1]:
                mismatches = [cid for cid, item in snapshot["cases"].items()
                              if item["verdict"] != reference["verdicts"][cid][engine]]
                report["endpoint_verdicts_match_reference"][engine] = not mismatches
                snapshot["reference_mismatches"] = mismatches
            args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            if mismatches:
                raise RuntimeError(f"Endpoint verdicts differ from published results: {mismatches}")
            print(f"  {snapshot['counts']}; timeout passes: {snapshot['passes_by_external_timeout']}", flush=True)

    if git(harness_root, "status", "--porcelain", "--untracked-files=no"):
        raise RuntimeError("Frozen harness was modified")
    report["complete"] = True
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved {args.output}", flush=True)


if __name__ == "__main__":
    main()
