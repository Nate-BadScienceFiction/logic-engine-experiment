# The 21 checks, rescored and rerun

Rerun September 25, 2026: the earlier engine passes **11**, fails **10**; the rewrite passes **16**, fails **3**, and has **2 unknowns**. External timeouts no longer count as engine stops, and the earlier engine's explicit `why/1` refusal is recognized as a refusal. No engine code changed.

[Raw results, observations and oracle outputs](comparison-revised-2026-09-25.json) · [rerun/scoring script](rerun-comparison.py) · [frozen 21-case corpus](cases-2026-09-24.json) · [original report](comparison-2026-09-24.md).

## Same cases, revised interpretation

The revisions remain old `e62758c23f66b26fa92c6d2dafaaf6bf3466499f` and new `9be7804c933cc8a3c51af3d8a5e4f54b012c8be6`. Each engine/case runs in a fresh subprocess. The corpus, default engine settings and case deadlines are unchanged. The rerun uses Python 3.12.10 and SWI-Prolog 10.0.2 on Windows 11.

| Rule | Original scoring | Revised scoring |
|---|---|---|
| External timeout on unbounded/bounded search | Pass | **Unknown**: no completed observation of the engine's status |
| External timeout on a case required to complete | Fail | Fail: required result did not arrive by the deadline |
| Observed explicit incomplete status on unbounded search | Pass | Pass; the engine itself reported incompleteness |
| Finite result without incompleteness status on unbounded search | Fail | Fail; silently truncating is not completion |
| Structured `why/1` response containing only `no_derivation_found` explanations | Counted as a positive answer | Recognized as a refusal; original payload retained in raw metadata |
| Other explanation-shaped values or arbitrary strings | Existing encoding/count rules | Unchanged; no general string-matching exemption |
| Worker/encoder/oracle unavailable | Unknown where observation is unavailable | Retained; never converted into evidence of correctness |

The refusal adjustment recognizes the predecessor's structured public response, not whether a particular test is its negative control. The same normalization is applied to all `why/1` calls: a refusal on a positive probe would therefore fail that probe. Mixed positive/refusal responses are not collapsed. This change does not certify that positive explanations contain correct proofs.

The wrapper imports the comparison harness from the pinned rewrite, applies these two corrections, preserves raw observations, and leaves both private repositories unchanged. Its self-checks cover timeout distinctions, positive explanations, explicit refusals, mixed results and unrelated predicates.

## What a difference looks like

These examples show what the cross-checks measure beyond a passing-test total:

| Question | Expected answer | Earlier engine | Rewrite |
|---|---|---|---|
| Given `p(1). p('1'). p(1.0).`, what does `p(X)` return? | Three distinct values: integer, atom, float | Collapses them into one answer | Returns all three distinct values |
| What are `-10 // 3` and `-10 div 3`? | `-3` (truncate toward zero) and `-4` (round down) | Fails to parse the test program | Returns the two expected values |
| Does the unbounded natural-number search finish? | An unfinished search must not be described as complete | Fails the check | Unknown: the external deadline arrives before an observable result |

The first two expectations were checked against SWI-Prolog. The third tests the engine's reporting contract; a timeout alone cannot establish whether that contract was met. Exact programs, observations and judgments are in the [raw results](comparison-revised-2026-09-25.json).

## Results by evidence strength

| Scope | Old pass | Old fail | Old unknown | Rewrite pass | Rewrite fail | Rewrite unknown |
|---|---:|---:|---:|---:|---:|---:|
| Answer, control, API and termination checks (18) | 9 | 9 | 0 | 16 | 0 | 2 |
| Explanation capability probes (3) | 2 | 1 | 0 | 0 | 3 | 0 |
| **All 21** | **11** | **10** | **0** | **16** | **3** | **2** |

The capability probes test positive presence plus a negative control. They are weaker than checking the content of a proof. Do not turn the combined totals into a general correctness percentage or migration-coverage percentage.

| Paired outcome | Cases |
|---|---:|
| Both pass | 9 |
| Both fail | 1 |
| Old passes, rewrite fails | 2 |
| Old fails, rewrite passes | 7 |
| Old fails, rewrite unknown | 2 |
| **Total** | **21** |

The rewrite still fixes observed arithmetic, syntax, value-fidelity and returned-list isolation failures. The old engine still supplies capabilities the rewrite omits. The revised scoring changes evidence accounting, not either implementation.

## What changed from the original report

- **Old `why/1`: fail → pass.** The absent target produced a structured `no_derivation_found` response, which now satisfies the negative control. The original payload is stored under the operation's `meta.raw_refusal`.
- **Rewrite infinite natural numbers: pass → unknown.** The default run hit the external deadline; no completed worker result demonstrated an engine stop.
- **Rewrite open-list generator: pass → unknown.** The end-to-end worker also hit its deadline. The query phase includes conversion of returned answers, so this observation alone cannot tell whether solving or conversion consumed the time.
- **All other case outcomes are unchanged.** The raw file contains every observation from the new run, rather than merely relabeling the old JSON.

The original 10/18 score and historical replay charts remain dated records using the old rules. Their scores must not be compared directly with this 11/16/2-unknown result as evidence of code changes.

## Every case in the rerun

The labels summarize each check. Exact identifiers match the frozen corpus and raw results.

| Cross-check | Earlier | Rewrite |
|---|---|---|
| Combine facts and rules for one predicate<br><small><code>resolution.facts-and-rules-for-one-predicate</code></small> | pass | pass |
| Join two conditions<br><small><code>resolution.conjunction-join</code></small> | pass | pass |
| Commit to a choice with cut<br><small><code>resolution.cut-commits-to-the-clause</code></small> | pass | pass |
| Keep negation from binding variables<br><small><code>resolution.negation-binds-nothing</code></small> | pass | pass |
| Divide negative integers correctly<br><small><code>builtins.arithmetic-integer-division-on-negatives</code></small> | fail | pass |
| Distinguish sorting with and without duplicates<br><small><code>builtins.sort-deduplicates-msort-does-not</code></small> | fail | pass |
| Keep repeated answers in findall<br><small><code>builtins.findall-keeps-multiplicity</code></small> | pass | pass |
| Decompose a compound term<br><small><code>builtins.univ-decomposes-a-compound</code></small> | fail | pass |
| Respect operator precedence<br><small><code>syntax.operator-precedence-in-a-comparison</code></small> | fail | pass |
| Preserve lists of every tested length<br><small><code>syntax.a-list-is-a-list-at-every-length</code></small> | pass | pass |
| Keep integers, floats and atoms distinct<br><small><code>value-fidelity.an-integer-a-float-and-an-atom-are-three-facts</code></small> | fail | pass |
| Preserve compound arguments in returned values<br><small><code>value-fidelity.a-compound-argument-survives-the-boundary</code></small> | pass | pass |
| Find reachable nodes along a chain<br><small><code>recursion.transitive-closure-over-a-chain</code></small> | pass | pass |
| Finish left-recursive reachability<br><small><code>recursion.left-recursion-terminates-and-is-complete</code></small> | pass | pass |
| Report an infinite answer set as unfinished<br><small><code>recursion.an-infinite-answer-set-must-not-be-called-complete</code></small> | fail | unknown |
| Avoid treating an open generator as false<br><small><code>errors.an-open-generator-must-not-read-as-false</code></small> | fail | unknown |
| Keep returned lists independent of engine state<br><small><code>mutation.a-returned-answer-list-is-the-callers-to-keep</code></small> | fail | pass |
| Report arithmetic on a non-number as an error<br><small><code>errors.arithmetic-on-a-non-number-is-an-error</code></small> | fail | pass |
| Explain a rule-derived fact<br><small><code>capability.rule-level-explanation-of-a-derived-fact</code></small> | pass | fail |
| Answer why a fact holds and refuse an absent target<br><small><code>capability.why-a-fact-holds</code></small> | pass | fail |
| Provide an evidence chain for a derived fact<br><small><code>capability.evidence-chain-for-a-derived-fact</code></small> | fail | fail |

## Supplemental bounded probes

To distinguish unobserved default behavior from an inability to report exhaustion, the two unbounded cases were also run on the rewrite with explicit limits: **20,000 resolution steps and at most 32 answers**, default depth unchanged.

| Case | Observed status | Returned answers | Recorded steps |
|---|---|---:|---:|
| Infinite natural numbers | `EXHAUSTED` | 32 | 20,001 |
| Open-list generator | `EXHAUSTED` | 32 | 66 |

These demonstrate the status channel under bounded settings. They do **not** replace the two unknown default runs in the headline, establish a general latency bound, or measure compatibility with the old engine's limits. Counts can exceed a step ceiling by the step that detects exhaustion.

## Oracle and coverage limits

The frozen corpus uses **12 SWI-only expectations, one mixed SWI/host-API expectation, and eight recorded adjudications**. The SWI-backed outputs were obtained again during this run. The corpus calls the latter judgments “human adjudication,” but their authorship is not established here; they are treated as recorded judgments, not independently verified human review.

The cases were selected with knowledge of both engines and several target old defects. They do not cover story time, source-sentence provenance, game hooks, or every deliberate dialect difference. They cannot establish that all old requirements migrated. See [the migration summary](../docs/MIGRATION.md) for that separate question and [the revised benchmarks](benchmarks-revised-2026-09-25.md) for performance.

## Rerun

Requires the pinned, clean source/harness revisions in both local clones, Python 3.12+, the predecessor's runtime dependencies, and SWI-Prolog. Private engine code is still required.

```powershell
python -B evidence/rerun-comparison.py --old-repo <old-checkout> --new-repo <rewrite-checkout> --output comparison.json
python -B evidence/rerun-comparison.py --new-repo <rewrite-checkout> --self-test
```

The output records revisions, script/corpus hashes, environment, start/end timestamps, per-case oracle data, verdicts, worker observations, timeout phases and supplemental settings. `complete: true` distinguishes a finished run from a partial checkpoint.
