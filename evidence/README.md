# How the numbers were measured

*For anyone checking my work.* Every number on the front page comes from a file in this folder or from a pinned commit in the engine's private repositories. This page says which, how each number was produced, and what it can't tell you.

The measurements answer three different questions:

| Evidence | Question it answers | Where to read it |
|---|---|---|
| Engine unit tests | Does each version satisfy its own suite? The suites differ in scope. | [Test counts and their limits](#what-the-test-counts-mean) |
| Shared cross-checks | How do both versions handle the same 21 selected programs and API probes? | [Current cross-check results](comparison-revised-2026-09-25.md) |
| Performance benchmarks | How long do three queries take in the rewrite and SWI-Prolog? | [Current timings and method](benchmarks-revised-2026-09-25.md) |

| File | What it is |
|---|---|
| `test-timeline-2026-09-25.csv` | Dated passing-test counts, Sep 2025–Sep 2026 (433 observations, each with its timestamp and source) |
| `render-test-timeline.py` | Draws `assets/test-timeline.png` from that CSV |
| `cases-2026-09-24.json` | The 21 comparison programs and their expected results |
| `comparison-2026-09-24.json`, `.md` | The comparison's raw results and the harness's own report |
| `development-progress-2026-09-25.json` | The same 21 checks replayed on 11 saved versions |
| `replay-development-progress.py`, `render-development-progress.py` | The replay and its chart |
| `index.html` | Historical results under the original scoring, case by case ([web version](https://nate-badsciencefiction.github.io/logic-engine-experiment/evidence/)) |

## Current comparison and migration

The [migration drill-down](../docs/MIGRATION.md) includes measured package/file/function counts and the test dispositions, backed by [raw measurements](migration-measurements-2026-09-25.json) and [a reproducible inventory script](measure-migration.py). The [revised comparison](comparison-revised-2026-09-25.md) reruns the same 21 cases with corrected timeout and refusal scoring: old **11 pass / 10 fail**, rewrite **16 pass / 3 fail / 2 unknown**.

The [revised benchmarks](benchmarks-revised-2026-09-25.md) collect full bindings in both engines, validate exact answers and separately measure Python conversion. Earlier comparison/replay scores and original benchmark timings below are historical records under their original methods.

## What the test counts mean

**Where they come from.** From the start the project kept a log with one pytest summary line per test run, added by hand at first and later mostly in the agents' own commits. It holds 814 runs through Aug 30, 2026. Most lines carry no date. The 167 lines from Sep 7–25, 2025 carry their own timestamps; the rest I dated three ways:

- **Log history.** Each commit to the log dates the lines it added, from Oct 25, 2025 on.
- **Commit messages.** From Sep 8 to late Nov 2025, 114 commit messages include a pytest summary.
- **Anchors.** Some log lines match those messages exactly. For example, run #168, "44 failed, 513 passed," is commit `f8f59f0` on Sep 8, 2025.

The first 139 runs carry no date and can't be anchored; the count grew from about 90 to about 500 passing over them. About the first 60 probably predate the earliest surviving repository (Aug 30, 2025), whose first commit already had about 320 test functions. The rewrite's counts come from its `TestScores.md`. Its first commit was rebuilt and run to get 540.

**What they count.** Passing pytest cases in each engine's test suite, where a parameterized test counts once per case. The earlier engine's suite covered more than the reasoning core. At its final commit (6,759 cases collected), about 79% tested engine semantics, 8% the text parser, 5% narrative models, 4% the host API, and 3% the command-line game and ontology tools.

**Why the final figure varies.** The earlier engine's final suite is quoted four ways:

| Figure | What it counts |
|---:|---|
| 6,660 | Passing, as logged by the project's runner, which excludes slow and benchmark tests |
| 6,683 | Passing under plain `pytest` |
| 6,759 | Collected |
| 6,778 | Collected, including benchmarks and one file skipped at collection. This is what the rewrite's audit classified, file by file |

**What the counts don't tell you:**

- **Quality.** The earlier engine passed 6,660 tests while getting textbook cut, negation and arithmetic cases wrong ([HISTORY.md](../docs/HISTORY.md#same-programs-three-engines)). On July 12, 2026 it logged "6,477 passed" with no failures. Replayed later, that same commit passes 9 of the 21 cross-checks below.
- **Like-for-like runs.** The log mixes several ways of invoking the suite, so neighboring lines aren't always comparable.
- **Real drops.** The chart shows the last logged count on each day it has data, as steps, so most mid-refactor failure spikes don't appear. The worst logged was 149 passing, with 317 failures, on Sep 9, 2025. There are two visible dips in 2026:
  - **June 14** was dead code deleted along with the tests that only exercised it.
  - **May 8** was partly a silent loss. Deleting an unused parser module made one test file skip itself at import time, dropping 148 tests of built-ins that still existed. They stayed skipped to the end.
- **Cross-engine comparisons.** The rewrite's suite was written fresh against a different design, so 1,144 versus 6,660 compares two different things.

## The 21-check comparison

**Historical scoring.** This section explains the original report and replay. For the corrected policy and a fresh endpoint run, use the [revised comparison](comparison-revised-2026-09-25.md).

**What it is.** 21 small Prolog programs, each with an expected result, run on the earlier engine (`e62758c`, Aug 30) and the rewrite (`9be7804`, Sep 24). Each case runs in its own process with a timeout.

**Where expected answers come from:**

- 12 cases use **SWI-Prolog 10.0.2**.
- 1 combines an SWI answer with a judgment about the Python API.
- 8 use **recorded rulings**: a written judgment stored with each case. The harness labels them "human adjudication," but their authorship is not established in the available record. All are dated Sep 22, the day the harness was built.

No case takes its expected answer from either engine's own documentation. The harness refuses that by name, after a review caught an early design draft doing it.

**Results:**

| | Earlier engine | Rewrite |
|---|---:|---:|
| Pass | 10 | 18 |
| of which, passes by test-runner timeout | 0 | 2 |
| Pass, if a timeout counts as a failure | 10 | 16 |
| Pass, if the undecodable `why/1` refusal counts as correct | 11 | 18 |

**The earlier engine's 11 failures, by kind:**

| Kind | Count |
|---|---:|
| Couldn't parse the program (`div`, `=..`) | 2 |
| Wrong or missing answers: sort/msort, operator precedence, `1`/`'1'`/`1.0` merged | 3 |
| Endless search returned as a short, final-looking list (2 answers; 0 answers) | 2 |
| Bad arithmetic answered "no" instead of raising an error | 1 |
| Shared cache: a caller's edit changed a later answer | 1 |
| `evidence_chain/1` called a non-fact "derived" | 1 |
| `why/1` replied "No derivation path found," which the harness couldn't decode and scored as an answer | 1 |

**Read it with these caveats:**

- **Not a random sample.** The cases were written after both engines existed, by people and agents who knew both. Some were added specifically for capabilities the rewrite lacks, to keep the set from flattering it. They net the earlier engine one case.
- **Timeouts.** On the two endless-search cases, the rule accepts "stopping" of any kind, including the test runner's timeout. Under that rule a hung engine passes too. Both rewrite passes were timeouts, so the harness never saw the engine's own "stopped early" status.
  - On `nat/1`, the engine's step budget hadn't run out after 25 seconds.
  - On the open-list generator, the engine did stop, after about 6 seconds. Converting its 1,498 partial answers to Python took far longer than the timeout.

  The raw JSON records both as "stopped on an unbounded answer set, as required." Only the replay file's `timed_out` marker shows how they actually stopped.
- **One-sided coverage.** The cases probe places where the earlier engine departs from ISO. They don't probe the rewrite's own departures from SWI, which are:
  - default deduplication;
  - the occurs check;
  - no cut in recursive predicates;
  - rejecting programs that are safe only because of their data;
  - unsupported built-ins quietly failing;
  - the non-classical reading of timed effect rules.

  None covers story time, source provenance or the game hooks, the things the engine is actually for.
- **Blind spots.** The corpus missed some of the earlier engine's known bugs. Its cut case puts the cut after a goal in the clause body, which the earlier engine handled. The failing case is a cut that should stop a later *fact* clause from being tried. Its negation case negates a variable that's already bound.
- **Explanation probes check that a request gets an answer, not that the answer is right.** Each probe has a negative control, a request that should get nothing. Only `derivation/1` passes. The rewrite has none of the three predicates.

**The replay.** The same 21 checks were rerun on 11 saved versions: 5 of the earlier engine (May–August 2026) and 6 of the rewrite.

- **Earlier engine: 8 → 8 → 9 → 9 → 10.** The gains were left recursion, and facts and rules combined in one predicate.
- **Rewrite: 17, then 18 from the next version on.** Its first commit already passed 17. The one later gain was the open-list case going from a Python `RecursionError` to a timeout.

Both endpoints reproduce the published verdicts exactly. Dates are commit dates, and the intervals between commits aren't hours worked.

## Semantic probes

The "same programs, three engines" table in [HISTORY.md](../docs/HISTORY.md#same-programs-three-engines) comes from small programs run against snapshots exported from the private repositories (`git archive` into scratch directories), with SWI-Prolog 10.0.2 as the reference. Every program is written out in full in that table. Reproducing the engine columns needs the engine code.

## Code size

Non-test Python lines, counted per commit with `git show` and `wc -l`:

- **Earlier package tree (`src/kb/`, excluding `src/tools/` at the final revision):** 13,032 (Aug 30, 2025) → 61,359 (Feb 21, 2026) → 54,387 (Aug 30, 2026). The package also held a text parser, a command-line game and application tools. At the final revision, all Python under `src/` totals 61,715 lines, including 7,328 additional analysis-tool lines.
- **Rewrite:** kernel 6,691 lines in 17 modules, plus 519 for the host boundary and 216 in package `__init__` files, for 7,426 in total.

## What isn't measured

- **Speed, between the engines.** The comparison's notes mention a warm, repeated-query benchmark on which the earlier engine looked about 3,500 times faster. The reason was its cross-query answer cache. The cache's *bug* was that it handed callers its own internal list; the *speed* came from caching itself. On a small ancestor query, measured for this write-up:

  | | Earlier engine | Rewrite |
  |---|---:|---:|
  | First (cold) query | 6.3 ms | 2.4 ms |
  | Repeated (warm) query | 0.004 ms | 0.44 ms |
  | Warm, deep-copying each answer (the bug fix) | 0.008 ms | n/a |

  So the old engine was faster on repeated queries because it cached, and it would have stayed that way with the bug fixed. The rewrite has no cross-query cache, by design, and is faster on a first query. Neither is a general benchmark. Revised full-binding timings for the rewrite against SWI-Prolog are in the [benchmark detail page](benchmarks-revised-2026-09-25.md).
- **Memory, effort and cost.** Nothing comparable was recorded for either engine.

## Reproducing

Everything here can be rerun from local clones of the engine repositories, with Python 3.12+ and SWI-Prolog 10.0.2. The commands are in [development-progress-notes.html](development-progress-notes.html#replay). The replay script uses the comparison harness's scoring code from the private rewrite repository, so without access to those repositories, the JSON files here are the record.
