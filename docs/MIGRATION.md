# What survived the rewrite

The September rewrite is substantially smaller, but it is not a drop-in replacement for the earlier repository. It preserves much of the reasoning behavior, deliberately changes some semantics, removes architecture-specific machinery, and currently leaves several useful capabilities outside its scope.

This comparison uses the earlier engine at `e62758c23f66b26fa92c6d2dafaaf6bf3466499f` and the rewrite at `9be7804c933cc8a3c51af3d8a5e4f54b012c8be6`. Measurements and the migration inventory were checked on September 25, 2026. [Raw measurements and all 235 file dispositions](../evidence/migration-measurements-2026-09-25.json) · [measurement script](../evidence/measure-migration.py).

## Measured size and structural complexity

| Metric | Earlier package: `src/kb/` | Rewrite: `src/cyclops/` |
|---|---:|---:|
| Python files, including package initializers | 187 | 25 |
| Physical lines | 54,387 | 7,426 |
| Function and method definitions | 2,065 | 353 |
| Class definitions | 320 | 54 |
| Median function span | 14 lines | 7 lines |
| 90th-percentile function span | 48 lines | 34 lines |
| Longest function span | 284 lines | 221 lines |
| Python files under `tests/`, including helpers | 276 | 38 |
| Physical lines under `tests/` | 96,478 | 13,137 |

The package has **86.3% fewer physical lines**. Counts include comments, docstrings and blanks. Functions include methods and nested definitions; their spans run from the definition line to its AST end line. The 90th percentile selects index `floor(0.9 × (n − 1))` in sorted spans. Counts come from pinned Git snapshots, not whatever happens to be in the working directories.

**Scope matters.** The old `src/kb/` includes a command-line game, ontology tools and other application code alongside the engine. It is not a pure reasoning-core denominator. All old Python under `src/` totals **61,715 lines in 198 files**, including another **7,328 lines in 11 files** under `src/tools/`. The rewrite's complete Python `src/` tree is the 7,426-line package. Neither comparison proves that the same feature set became 86.3% simpler.

These measurements describe size and function length, not cyclomatic complexity, runtime complexity, maintainability, or correctness. The architectural evidence for simplification is more specific: fewer representations and dispatch paths, removal of dual-engine routing, one ordered clause store, and less long-lived mutable state. Large functions remain: the longest rewrite function still spans 221 lines. For execution costs, see the [revised benchmarks](../evidence/benchmarks-revised-2026-09-25.md); for answer behavior, see the [rescored comparison](../evidence/comparison-revised-2026-09-25.md).

## Responsibilities: kept, changed and omitted

| Responsibility | Earlier implementation | Rewrite disposition and consequence |
|---|---|---|
| Terms and unification | Multiple representations and unification paths | Reimplemented with shared term types and trail-based bindings; occurs check on by default |
| Facts, rules and clause order | Separate storage and evaluation infrastructure | One ordered clause sequence per predicate, with first-argument indexing |
| Goal evaluation | Two evaluators plus routing and strategy machinery | Shared solver machinery; SLD execution for untabled goals and fixpoint evaluation for tabled goals |
| Cut and negation | Distributed across evaluator paths | Consolidated behavior; recursive/tabled cut rejected, negation no longer reordered |
| Recursive reasoning | Tabling plus legacy depth limits | Automatic recursive-component tabling; query-local tables and explicit exhaustion status |
| Temporal reasoning | Several `holds_at` paths, separate explanation queries | One native temporal decision procedure with explanations; timed effects retain a non-classical interpretation |
| Source-text provenance | Fact IDs/supports and an additional `source/2` lookup path | `spans_for` supports fact IDs/supports; direct `source/2` lookup needs an authored query |
| General rule explanations | Partial `derivation`, `why` and `evidence_chain` support | Removed; temporal `explain` is not a replacement for a non-temporal proof tree |
| JSON and game affordances | Host integration layer | Reimplemented: tagged values, allow/deny/abstain, and first unmet guard message |
| Result caching | Cross-query answer caching, including a returned-list aliasing bug | No cross-query answer cache; repeated queries recompute, while analysis/timeline data are revision-tagged |
| Parser and query infrastructure | Parallel parsers, handlers and a multi-stage pipeline | One syntax reader and shared term representation; old internal APIs disappear |
| Authoring diagnostics | Singleton-variable, unused-predicate and arity checks | Deferred; these are real missing capabilities, not obsolete architecture |
| Games and tools | Rooms, CLI, gameplay, narrative applications and code analysis | Omitted from the kernel; hosts must supply them separately |

Removing machinery does not remove its useful contracts. Tests for cache *objects* can retire while tests that mutations become visible, returned values remain isolated, and repeated queries stay deterministic must survive.

## Do all the old tests apply?

**No.** Many behavioral requirements remain applicable, but the old tests import classes and private methods that no longer exist. Other tests assert semantics the rewrite intentionally changed, and some exercise applications outside its scope. The old suite also contains integration, narrative and performance tests; its headline count is not a count of isolated unit tests.

The rewrite's private `docs/TEST_MIGRATION_LEDGER.md` assigns each source file one disposition. Its appendix and every test-definition count were independently rechecked against the pinned predecessor. The case counts below are the ledger's historical pytest collection counts, not a fresh execution of the old suite.

| Disposition | Meaning | Files | Definitions | Historical cases |
|---|---|---:|---:|---:|
| A — Adapt | Retain the requirement through a named destination test | 25 | 593 | 696 |
| C — Already covered | Destination tests already address the file's behavior | 44 | 789 | 857 |
| R — Replace/consolidate | Rewrite weak or overlapping tests into stricter checks | 35 | 913 | 966 |
| O — Retire obsolete internals | Removed classes, private APIs or architectural mechanisms | 87 | 3,294 | 3,421 |
| X — Retire out of scope | Application layers, datasets, tooling or performance scope | 43 | 827 | 800 |
| B — Blocked/deferred | Authoring diagnostics not implemented | 1 | 38 | 38 |
| **Total** | | **235** | **6,454** | **6,778** |

**This is a file-level classification, not an assertion-by-assertion equivalence proof.** A/C/R contain 2,519 old cases, but that is not a measured count of preserved requirements. O/X contain 4,221 old cases, but some retired files also contain surviving behavior mapped elsewhere. The 38 B cases are not the total of all missing capabilities: general explanations, for example, are recorded as a gap within retired provenance files.

Current collection at the pinned rewrite finds **1,397 selected cases: 1,144 engine correctness cases plus 253 comparison-harness tests**, with **36 deselected optional cases** (8 benchmarks and 28 predecessor comparisons). These are collection counts; this publication update did not rerun the full correctness suites. The historical passing results and their limits remain in the [evidence overview](../evidence/README.md#what-the-test-counts-mean).

### Examples of migration decisions

| Old tests or requirement | What should carry forward | Why copying the test is insufficient |
|---|---|---|
| `test_cut_regression.py` | Exact answers, including pruning later clauses and caller cut boundaries | A yes/no success check cannot detect an extra answer; recursive cut is now rejected |
| `test_facts_rules_union.py` | Both facts and rules contribute answers inside rule bodies | The old fact/rule separation no longer exists, but the observable requirement remains |
| `test_member_predicate.py` | Undo a partial failed match before trying the next list element | Requires a discriminating binding test, not merely finding one successful member |
| `test_arithmetic_evaluator.py` | Correct values and typed arithmetic errors | Old expectations of `[]` for division by zero or nonnumeric arithmetic are intentionally invalid here |
| `test_naf_semantics.py` | Binding isolation and the chosen left-to-right negation behavior | The old non-ground floundering/reordering expectations differ from the new contract |
| Temporal semantics matrix | Boundary times, simultaneous initiation/termination and exclusivity | Preserve the requirement, but state the explicit exclusivity policy and effect-time interpretation |
| Router/cache/strategy unit tests | Determinism, mutation visibility, result isolation where relevant | Removed implementation classes cannot be meaningful destinations |
| `test_semantic_analysis.py` | Authoring warnings for singleton variables, unused predicates and arity | Deferred functionality; no claim of replacement coverage |
| Provenance handler tests | Source lookup and, separately, general proof explanations | Temporal explanations survive; general rule explanations do not |

The old `tests/narratives/test_dynamic_generation.py` contains **52 definitions but collects zero cases** in the audited predecessor: it skips at import because `kb_parser_extended` is absent. Its dormant definitions should not be counted as passing protection. The ledger maps surviving syntax/builtin subjects separately.

### Intentional semantic changes

- Negation is evaluated in authored goal order; it does not reorder an unbound negative goal to make it succeed.
- Integers, floating-point values and numeric-looking atoms remain distinct terms.
- Bad arithmetic raises a typed error instead of returning no answers; `//` truncates and `div` floors.
- Exclusivity requires a declaration or explicit compatibility options. An initiated `neg(F)` is ordinary domain data, not an implicit termination of `F`.
- Named times such as `t9` and `t10` do not acquire an order from their digits; authored ordering matters.
- Recursive cut and predicate-level negative cycles are rejected globally. This is a limitation even when a particular dataset would permit safe execution.
- Default top-level answer deduplication remains a dialect choice. Untabled multiplicity is available with `distinct=False`; tabled answers remain sets.

The detailed current contract is in [ENGINE.md](ENGINE.md). Passing a rewritten test must mean satisfying an explicit retained or revised requirement, not matching whatever the rewrite happens to do.

## Gaps that must remain visible

The migration ledger records seven gaps: deferred authoring diagnostics; the missing direct `source/2` provenance path; deep-term formatting that can reach Python's recursion limit; exhaustion on very long list unification; loss of otherwise available partial answers in some growing-call tabled searches; missing general rule explanations; and model-pack loading that is atomic per file rather than per pack. The precise depth observations are environment-dependent.

The later public audit also exposed timed-effect semantics that differ from classical Event Calculus. The exhaustive temporal tests use an oracle transcribed from the rewrite's own behavior specification: they can verify consistency with that specification without independently establishing classical conformance. Similarly, agreeing with an intentionally changed old test is not an independent oracle.

## What the evidence establishes

The inventory is complete at the file/definition level, and the rewrite is measurably smaller. Named destination tests and recorded review campaigns provide useful evidence of retained behavior, but do not prove every old assertion has an equivalent, or that every retired file was correctly classified. Mutation/reviewer reports described by the private documents were not independently rerun for this page.

A stronger next audit would map high-value source assertions to explicit requirements and destination cases, including surviving requirements inside O/X files, then show those cases reject plausible broken implementations. That work is not claimed by the totals above. The separate [rescored 21-case comparison](../evidence/comparison-revised-2026-09-25.md) is deliberately narrower than a migration-coverage score.

## Reproduce the measurements

Requires Python 3.12+, Git and local clones containing the pinned revisions. No source checkout is changed.

```powershell
python -B evidence/measure-migration.py --old-repo <old-checkout> --new-repo <rewrite-checkout> --output migration.json
```

The JSON includes the counting method, revisions, script and ledger hashes, directory totals, and every file disposition. Public readers can inspect those results; recreating them requires the private repositories.
