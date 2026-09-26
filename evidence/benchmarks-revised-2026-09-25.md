# Speed with full answer bindings

Measured September 25, 2026, after correcting the answer materialization mismatch in the original benchmark. Both engines now retain every requested binding, and every workload must match exact independently constructed answers before its timings are accepted.

[Raw batches and expected answers](benchmarks-revised-2026-09-25.json) · [script](benchmark-vs-swi.py) · [original measurements](benchmarks-2026-09-25.md) · [shared cross-check results](comparison-revised-2026-09-25.md).

## Time to return all query values

Median milliseconds per query across five batches. Here, native answers means values in each engine's own term representation, before any conversion to Python host values. Displayed timings are rounded to three significant figures; the raw JSON retains full precision. The rewrite uses `ask(..., distinct=False)` and retains its native answer terms; SWI uses `findall` with a template containing **all query variables**, not a constant placeholder. Both include query execution and complete answer construction. These are runtime/API measurements, not isolated solver timings.

| Workload | Exact answers | Rewrite, automatic tabling | Rewrite, tabling off | SWI-Prolog | Rewrite/SWI, off to automatic |
|---|---:|---:|---:|---:|---:|
| Naive reverse of a 30-element list | 1 | 108 | 9.2 | 0.00807 | 1,140×–13,368× |
| All solutions of 6-queens | 4 | 508 | 206 | 0.552 | 373×–920× |
| All ways to split a 100-item list with app/3 | 101 | 4,200 | 18.6 | 0.221 | 84×–19,025× |

On naive reverse and six queens, the rewrite is approximately **373–13,368 times slower** in this run, depending on workload and tabling settings. List splitting spans **84–19,025 times slower**. These are three small workloads on one Windows 11 machine, not a general speed ranking or a comparison against the old Python engine.

## Python value conversion, measured separately

This is the same rewrite query with conversion of its answer terms to Python values included. There is no SWI ratio for this column: a Prolog answer term and a Python host representation are different API products. Measurements are separate batches; noise can make the conversion-inclusive median slightly lower than the native median, so subtracting the medians is not a reliable conversion-only cost estimate.

| Workload | Python values, automatic tabling (ms) | Python values, tabling off (ms) |
|---|---:|---:|
| Reverse a 30-item list (`nrev30`) | 107 | 9.04 |
| Solve six queens (`queens6`) | 511 | 204 |
| Split a 100-item list (`split100`) | 6,860 | 42.9 |

## Variability and limits

Batch ranges below are minimum–maximum **batch means**, not confidence intervals. The list-split conversion and SWI measurements varied substantially; retain that uncertainty when interpreting their ratios. We do not infer that Python interpreter overhead accounts for a measured share of the gap. Algorithm, tabling policy, parsing, representation, allocation and runtime all contribute.

| Workload | Rewrite native/default range (ms) | SWI range (ms) | Python values/default range (ms) |
|---|---:|---:|---:|
| Reverse a 30-item list (`nrev30`) | 106–119 | 0.00801–0.00842 | 106–108 |
| Solve six queens (`queens6`) | 507–514 | 0.547–0.557 | 507–513 |
| Split a 100-item list (`split100`) | 4,120–4,370 | 0.205–0.282 | 4,190–9,730 |

The rewrite parses the query on each `ask` call; SWI executes a compiled goal. Setup/compilation and process startup are excluded from the timed loops, but this API difference remains. SWI uses ordinary untabled execution here. Automatic tabling versus no tabling is shown explicitly for the rewrite; the table is not a same-algorithm experiment. Wall-clock measurements on a shared desktop include scheduling and runtime noise.

## What changed in the method

1. **Full bindings in both engines.** SWI collects `[R]`, `[Qs]`, or `[X,Y]`. The original `findall(x, Goal, _)` discarded those values, especially understating the materialization work for 101 list splits.
2. **Exact results, not counts alone.** Expected reverse is the reversed input; splits are all prefix/suffix pairs; queens are Python permutations filtered by an independent diagonal test. Comparison is a multiset: row order is ignored, duplicate multiplicity and values are checked. A failed correctness check aborts publication of the timings.
3. **Status checked.** The rewrite must complete each validation and timed query. A partial answer set is not timed as a successful result.
4. **Separate native and host results.** Python conversion has its own timing, instead of being silently included on only one side of a solver-speed claim.
5. **Pinned inputs and raw observations.** The script requires clean source at rewrite `9be7804c933cc8a3c51af3d8a5e4f54b012c8be6`, records its own hash and runtime versions, and saves programs, exact expected rows, batch sizes and all batch means.

## Timing protocol

Python 3.12.10; SWI-Prolog 10.0.2 for x64-win64; Windows 11; Intel64 Family 6 Model 151 Stepping 5. Each mode loads its program once. An initial correctness query precedes two warm-up queries. Five timed batches follow; the headline is the median of their per-query means. Python uses `perf_counter`, SWI uses `get_time` around a failure-driven loop; the loop overhead remains included. SWI outputs its exact answers outside the timed batches, and Python verifies them before accepting the results.

| Runs per batch | Automatic tabling | Tabling off | SWI |
|---|---:|---:|---:|
| Reverse a 30-item list (`nrev30`) | 10 | 50 | 20000 |
| Solve six queens (`queens6`) | 3 | 5 | 1000 |
| Split a 100-item list (`split100`) | 1 | 20 | 5000 |

The same batch sizes apply to the Python-conversion mode. The historical old/new warm-cache observations in the evidence overview are a different experiment and are not folded into these ratios. Caching can provide a real speed advantage even when an implementation also has a result-aliasing bug.

## Programs and reproduction

The complete programs and queries are stored in the raw JSON and the script. Naive reverse reverses 1 through 30; six queens enumerates all four solutions; list splitting enumerates all 101 splits of 1 through 100.

```powershell
python -B evidence/benchmark-vs-swi.py <rewrite-checkout> --json timings.json
```

Reproduction requires the private rewrite checkout and SWI-Prolog. The old timestamped JSON is retained as historical data, but its placeholder-answer ratios are superseded for full-binding comparisons.
