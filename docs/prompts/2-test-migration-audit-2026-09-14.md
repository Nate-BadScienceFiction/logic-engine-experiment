# Prompt 2: test-migration audit

September 14, 2026 · [All three prompts](README.md) · Previous: [design brief](1-design-brief-2026-09-13.md) · Next: [two-way audit of code and tests](3-two-way-audit-2026-09-15.md)

> As I wrote it, from `prompt.md` in the rewrite's repository (AkiyaBlocks-CyclopsStorm, private for now), commit `467dbb8`. Two changes: local folder paths are replaced with repository names, and numbered section titles are shown as headings.

---

Treat this as a **test migration and adversarial coverage audit**, not a bulk copy. Every source test must receive a disposition, but matching the old test count is not the objective: the new suite should provide stronger evidence that the new engine behaves correctly.

SOURCE REPOSITORY:\
BadScienceFiction-CyclopsStorm

DESTINATION REPOSITORY:\
AkiyaBlocks-CyclopsStorm

Translate the source repository’s unit tests into a comprehensive, trustworthy test suite for the destination’s rearchitected Python implementation.

Review EVERY individual source test for relevance, correctness, quality, and coverage. Adapt useful tests to the new architecture, replace weak tests with meaningful checks, retire obsolete implementation-specific tests with justification, and fill coverage gaps.

This is not a mechanical migration or an exercise in reproducing the source test count. The objective is confidence in the destination’s intended behavior and architectural invariants.

Choose the detailed testing approach and organization yourself, respecting the destination’s existing conventions. Complete the inventory and audit rather than stopping after a representative sample.

### 1. ESTABLISH THE BASELINE AND COMPLETE INVENTORY

Read the instructions in both repositories and inspect their current implementations, documentation, tests, fixtures, and test configuration.

Treat BadScienceFiction-CyclopsStorm as read-only. Preserve unrelated destination changes. Keep any source execution or mutation experiments isolated from the original repository.

Run the destination’s existing relevant tests to establish a baseline. Record pre-existing failures separately from problems introduced or discovered by this task.

Inventory all source unit tests, including parameterized and generated cases, skipped tests, expected failures, and tests outside the obvious directories. Inspect shared fixtures and helpers that affect what those tests actually exercise.

Also inventory existing destination coverage. Do not add a redundant test simply because the equivalent source test has not been copied over.

Distinguish test definitions from collected test cases. Confirm that the inventory is complete against actual test discovery where possible, and report discovery failures rather than treating undiscovered tests as absent.

Maintain a concise migration ledger identifying each source test, the behavior it is intended to protect, its disposition and rationale, and the corresponding destination coverage or unresolved gap.

Several source tests may map to one stronger destination test, or one source test may require several replacements. Preserve traceability in either case. Parameterized cases may share a rationale only when their individual behavioral coverage has been considered.

### 2. DOUBLE-CHECK EACH TEST AGAINST THE DESTINATION

For every source test, perform two distinct reviews.

RELEVANCE AND SEMANTIC REVIEW:\
Determine what requirement the test actually protects, whether that requirement applies to the destination, and whether its expected result is justified.

Distinguish intended public behavior and genuine internal invariants from obsolete classes, private methods, historical workarounds, or accidental behavior.

Inspect the code path exercised, not just the test name and comments. Compare the test with the destination’s actual architecture and documented behavior.

QUALITY AND COVERAGE REVIEW:\
Determine whether the test would detect a plausible defect in the behavior it claims to protect.

Look for assertion-free tests without a meaningful no-error contract, tautologies, swallowed exceptions, circular expectations, mocks that only verify themselves, weak type or non-null checks, and assertions that succeed vacuously when the engine returns nothing.

A test need not contain a literal assert statement to be meaningful. Exception checks and deliberate smoke tests can be valid. The question is whether an incorrect implementation can pass unnoticed.

Check that setup, fixtures, helpers, and result normalization do not hide the behavior under test. Sorting results, for example, is inappropriate when answer order is part of the contract.

Use dispositions such as adapt, already covered, replace or consolidate, retire as obsolete, and blocked by missing behavior. Explain each decision.

Do not label a behavior obsolete merely because the destination has not implemented it yet.

### 3. MIGRATE BEHAVIOR WITHOUT RESTORING THE OLD ARCHITECTURE

Write tests against appropriate destination interfaces and invariants. Prefer public behavior for semantic requirements and focused internal tests where they genuinely protect the new design.

Do not recreate old classes, compatibility shims, private APIs, or dependency structures solely to accommodate source tests.

The destination architecture determines how behavior is exercised. Intended semantics determine what results are correct. Neither the source implementation nor the destination’s current output is automatically the truth.

Reuse sound fixtures and independently justified expectations where appropriate. Keep required test assets self-contained in the destination. Do not change authored .pl models to make tests pass.

Create small, understandable regression fixtures where needed and permitted. Avoid importing large legacy fixtures when a focused example would isolate the behavior more clearly.

Ordinary destination tests must not require the source repository, import its reasoning internals, or fall back to its engine. Keep optional differential comparisons separate and explicit.

Organize tests according to the destination’s responsibilities. Preserve distinctions among unit, integration, semantic conformance, and performance tests rather than calling everything a unit test.

### 4. FILL HOLES FROM THE DESTINATION OUTWARD

Do not limit this task to gaps visible in the source suite. Inspect the destination implementation and its behavioral contract for requirements that have no meaningful tests.

Build a concise coverage map connecting required behavior and important invariants to tests. Use code-coverage reports as supporting evidence where useful, not as proof of correctness or a percentage to optimize blindly.

Investigate missing branches, boundaries, negative cases, and interactions. Pay particular attention to:
- Variable identity, unification, substitutions, clause ordering, and mixed facts and rules.
- Recursive evaluation, mutual recursion, negation, and supported procedural control.
- Temporal boundaries, competing effects, persistence, and historical queries.
- Mutation, knowledge revisions, cache validity, and query-state isolation.
- Deterministic answers, provenance, malformed input, and completion or error status.

These are review prompts, not a fixed test checklist. Derive the actual cases from the destination’s requirements and supported features.

Test equivalent query forms where they should agree. Include relevant sequences of operations, not just fresh-engine queries. Check cold and repeated execution, mutation followed by querying, and multiple independent engine instances where applicable.

Ensure tests of “all results satisfy a condition” also establish the expected existence and completeness of results. Include negative cases that distinguish a correct implementation from an always-empty or always-successful one.

Add coverage for architectural promises unique to the rewrite, including independence from the source engine and isolation of transient query state.

### 5. HANDLE FAILURES AND SEMANTIC DISAGREEMENTS HONESTLY

Investigate failures rather than adjusting expected values to match current output.

Classify discrepancies as test defects, source defects, destination defects, intentional semantic changes, missing functionality, or unresolved requirements.

Use documented contracts, authored examples, and independently derived expectations to resolve disagreements. The source engine is useful comparison evidence, not an infallible oracle.

Make focused destination fixes when a valid test demonstrates a clear defect within the agreed behavior. Keep implementation changes narrow and explain them separately from test migration.

Do not broaden this task into another rearchitecture, introduce legacy fallbacks, or weaken the intended contract to obtain a green run.

Do not bury required but unimplemented behavior behind silent skips or permissive assertions. Record it explicitly as a gap. Any justified skip or expected failure must be narrowly scoped, explained, and included in the final accounting.

Where semantics cannot be responsibly resolved, document the conflicting evidence and affected cases. Do not invent an expectation and present it as established behavior.

### 6. INDEPENDENTLY CHALLENGE THE RESULTING SUITE

Use an independent reviewer or testing agent where available to review migration decisions and the destination tests, especially retired tests, consolidated coverage, and claims that a gap is now closed.

Require evidence that critical tests detect plausible incorrect behavior. Use targeted mutation checks, controlled fault injection, or another appropriate method where it adds value.

Keep these experiments isolated and restore all changes. Do not mutate the original source repository or a shared working tree used by other agents.

Review shared fixtures for leakage, hidden dependencies, and global state changes. Check that scoped test runs and the complete suite behave consistently and that test ordering does not conceal defects.

Verify that every new test is actually collected by the intended runner. A useful test that never runs is not coverage.

### 7. INTEGRATE WITH THE WINDOWS TEST RUNNERS

Preserve or provide these destination launchers:
- run_unit_tests.bat for the unit-test suite.
- run_tests.bat for the complete correctness suite.

Ensure migrated and newly added tests are included in the appropriate runs. Keep performance benchmarks opt-in and optional source comparisons separate.

The launchers must work from another working directory, handle paths containing spaces, use the documented Python environment, forward additional test arguments, and propagate failure exit codes.

Keep them thin and aligned with the project’s normal test configuration. Avoid unconditional pauses, hidden dependency installation, and swallowed errors.

Run the relevant scoped tests throughout the work, then run the complete destination correctness suite. Verify the .bat files on Windows when available; otherwise state precisely what was and was not verified.

### 8. COMPLETE THE ACCOUNTING AND REPORT

Reconcile the final migration ledger against the source inventory. Every source test must have an explicit disposition. Do not leave unexplained omissions or imply that a sample audit covered the whole suite.

Confirm that the destination remains self-contained and that no migrated tests depend accidentally on the source checkout.

Provide a concise final report covering:
- Baseline and final test results.
- Tests adapted, already covered, replaced or consolidated, retired, and blocked.
- Important weak tests corrected and how their replacements are stronger.
- Coverage holes found and filled.
- Destination defects fixed.
- Remaining gaps, skips, expected failures, and unresolved semantic decisions.
- Independent review and test-strength evidence.
- Exact commands for running the unit and complete correctness suites.

Report test definitions and collected cases clearly where counts differ. Do not use test-count parity or a coverage percentage as the primary claim of success.

Proceed autonomously on reversible choices. Respect repository policies and obtain permission for destructive actions, commits, or pushes when required.

Guiding principle:\
Every source test must be understood.\
Every retained requirement must have meaningful destination coverage.\
Every claimed gap closure must have evidence.
