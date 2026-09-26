# Prompt 3: two-way audit of code and tests

September 15, 2026 · [All three prompts](README.md) · Previous: [test-migration audit](2-test-migration-audit-2026-09-14.md)

> As I wrote it, from `prompt.md` in the rewrite's repository (AkiyaBlocks-CyclopsStorm, private for now), commit `beb6179`. Two changes: local folder paths are replaced with repository names, and numbered section titles are shown as headings.

---

REPOSITORY:\
AkiyaBlocks-CyclopsStorm

Perform a comprehensive, bidirectional audit of the current implementation and its unit tests:

1. Work from EVERY test toward the behavior it claims to verify.
2. Work from EVERY production component back toward the tests that should protect it.

Identify faulty tests, weak assertions, logical fallacies, missing coverage, and implementation defects. Develop a careful remediation plan, adversarially review that plan, then implement and verify it.

Do not stop at findings, a proposal, a representative sample, or the first green test run. Carry the task through the complete audit, reviewed plan, implementation, and final adversarial verification.

This is a correctness and test-quality exercise, not a test-count or coverage-percentage exercise. Choose the detailed methods and tools yourself, respecting the repository’s architecture and conventions.

### 1. ESTABLISH THE BASELINE AND AUDIT SCOPE

Read the repository instructions, current architectural and behavioral documentation, implementation, test configuration, fixtures, and test runners.

Inspect the working tree and preserve unrelated changes. Establish the existing test baseline and distinguish pre-existing failures from failures introduced or discovered during this work.

Inventory all unit tests, including parameterized cases, generated tests, skipped tests, expected failures, and tests outside the obvious directories. Reconcile the source inventory with actual test collection so undiscovered or accidentally overwritten tests do not disappear from the audit.

Inventory the first-party production code as well. Include relevant host boundaries, loaders, error handling, and supporting code, not just the central reasoning algorithms.

Maintain a compact audit ledger showing what has been inspected, what behavior is involved, findings, planned action, and verification evidence. Batch work sensibly, but ensure every test and production component receives an explicit disposition rather than a blanket “reviewed” label.

The historical BadScienceFiction-CyclopsStorm repository may be consulted as read-only context if needed. Its implementation and tests are not automatically authoritative, and the destination must remain independent of it.

### 2. AUDIT EVERY TEST FOR MEANING, CORRECTNESS, AND STRENGTH

For each test, identify the requirement or invariant it is intended to protect. Trace what it actually executes, including shared fixtures, helpers, mocks, and result transformations.

Ask two separate questions:
- Is the expected behavior correct and relevant to the current implementation’s intended contract?
- Would this test fail for a plausible violation of that behavior?

Look for:
- Tautologies, circular expectations, and expected values derived from the same potentially faulty logic being tested.
- Vacuous success, including assertions that pass because no results were produced or the important branch never executed.
- Weak assertions that do not establish the claimed behavior, missing negative cases, and incomplete checks of returned answers.
- Mocks that replace the behavior supposedly under test or merely verify their own configuration.
- Swallowed exceptions, overly broad exception expectations, and skips or expected failures that conceal unrelated defects.
- Setup errors, misleading names or comments, incorrect parameterization, and tests that exercise a different code path from the one claimed.
- Sorting, deduplication, normalization, or helper behavior that hides ordering, multiplicity, identity, provenance, or other meaningful differences.
- Shared state, fixture leakage, accidental ordering dependencies, and environmental assumptions.

Do not use simplistic rules such as “every test needs an assert statement” or “all mocks are bad.” Exception tests, interaction tests, and intentional smoke tests can be meaningful. Evaluate what each test actually proves.

Classify tests as sound, needing correction, needing strengthening, redundant with identified coverage, obsolete with justification, or blocked by missing or disputed behavior.

Do not retire a requirement merely because its test fails or the destination does not implement it yet. Do not preserve an incorrect expectation merely because it came from the original suite.

### 3. AUDIT THE CODE BACKWARD TO COVERAGE

Independently review every production component and identify the behaviors, invariants, branches, boundaries, failure modes, and interactions that need protection.

Then locate the tests that meaningfully establish those properties. Reading or executing a line is not evidence that its behavior has been checked.

Look for:
- Untested behavior and tests that reach code without asserting its effects.
- Missing boundary, negative, malformed-input, and error-propagation cases.
- State transitions and sequences of operations absent from fresh-instance tests.
- Interactions that isolated component tests cannot establish.
- Architectural promises that have no executable protection.
- Dead, unreachable, or obsolete code mistakenly treated as useful functionality.

For CyclopsStorm, challenge the relevant contracts around variable identity, unification, substitutions, facts and rules, answer ordering, recursive evaluation, supported negation and control constructs, temporal boundaries, competing fluent effects, persistence, provenance, mutation, caching, and query-state isolation.

Check the distinction between complete logical failure and incomplete computation or execution failure wherever the engine promises it.

Derive cases from actual supported or required behavior. Do not invent new language features merely to create tests.

Use code coverage as a navigation aid, not proof of correctness. Use unit tests for isolated responsibilities and integration or conformance tests where the property crosses boundaries. Do not force every missing check into the unit-test category.

### 4. DEVELOP AND ADVERSARIALLY REVIEW THE PLAN

Before substantial changes, consolidate the findings into a prioritized remediation plan.

For each change, identify:
- The defect or coverage gap and supporting evidence.
- The intended behavior and why that expectation is justified.
- Whether the remedy belongs in tests, fixtures, production code, documentation, or test infrastructure.
- The risks and the evidence required to verify completion.

Prioritize semantic correctness and tests that can pass against broken behavior. Avoid adding redundant tests or undertaking unrelated refactoring.

Have an independent reviewer or agent challenge the plan where available. Otherwise perform a distinct adversarial review pass.

The reviewer should try to refute findings, expose unjustified expectations, identify missing interactions, and determine whether proposed tests could still pass with an incorrect implementation.

Revise the plan before implementation. Record substantive disagreements and their resolution. Do not treat reviewer agreement as a substitute for evidence.

### 5. IMPLEMENT THE REVIEWED CHANGES

Implement the approved-by-review plan in coherent, verifiable batches.

Correct faulty tests, strengthen weak ones, add missing coverage, and repair fixtures or helpers that undermine multiple tests. Preserve traceability when consolidating or retiring tests.

When valid tests expose clear destination defects, make focused production fixes consistent with the intended contract. Keep those changes distinguishable from test corrections.

Do not change expected values to match current output without independent justification. Do not weaken assertions, rewrite authored models, introduce legacy fallbacks, or broadly redesign the engine to obtain a green suite.

When requirements genuinely conflict or remain unresolved, investigate the available evidence and document the issue explicitly. Do not invent certainty or silently encode a new semantic policy.

Ensure all new tests are collected and included in the appropriate runners. Keep performance benchmarks opt-in and historical-engine comparisons separate from ordinary correctness tests.

### 6. VERIFY THAT THE TESTS CAN DETECT ERRORS

For critical tests and important gap closures, demonstrate sensitivity to plausible defects using targeted mutation checks, controlled fault injection, pre-fix execution, or another appropriate technique.

Challenge both new tests and existing tests retained as important evidence. A green test against the correct implementation alone does not establish that it protects the intended behavior.

Keep source-mutating experiments isolated. Do not allow parallel agents or reviewers to contaminate one another’s working trees. Restore all experimental changes before final verification.

Check test isolation through appropriate scoped, full-suite, and alternate-order runs. Verify that fixtures and mocks do not leave global state behind.

Use an independent review pass to inspect the implementation changes and resulting assertions. Pay particular attention to removed tests, relaxed expectations, newly introduced skips, and claims that a difficult gap has been closed.

### 7. RUN THE FINAL VERIFICATION AND AUDIT YOUR OWN CONCLUSIONS

Preserve or update the destination’s Windows runners:
- run_unit_tests.bat
- run_tests.bat

Verify that they invoke the intended suites, include the new tests, accept additional test arguments, and propagate failure exit codes. They must not depend on the historical repository.

Run the unit suite and complete correctness suite after the final substantive changes. Run the project’s relevant configured quality checks. Verify the batch files on Windows when available and distinguish native verification from inspection or non-Windows execution.

Adversarially review the final diff, audit ledger, coverage claims, and proposed completion report.

Specifically ask:
- Was every inventoried test and production component actually reviewed?
- Does each claimed fix have evidence beyond a passing test?
- Could an always-empty, always-successful, stale-state, or otherwise plausible broken implementation still satisfy the important assertions?
- Were requirements accidentally weakened or meaningful cases lost?
- Are any tests uncollected, unjustifiably skipped, or dependent on unavailable assets?
- Do the final reported results correspond to the final working tree?

Correct any issues found and rerun affected verification. Do not stop while actionable, in-scope defects remain.

### 8. COMPLETION AND REPORTING

Finish only after the complete inventories have been reconciled, the reviewed remediation plan has been implemented, and final verification has been performed.

For genuinely external blockers or unresolved requirements, complete all unblocked work and state precisely what remains. Never describe a blocked audit or unverified change as complete.

Provide a concise final report covering:
- Baseline and final test results.
- Audit scope and accounting for all tests and production components.
- Important test defects corrected.
- Coverage gaps filled and production defects fixed.
- Adversarial findings and evidence that critical tests detect errors.
- Remaining failures, justified skips, expected failures, blockers, or semantic questions.
- Exact commands for running the unit and complete correctness suites.

Distinguish test definitions from collected parameterized cases when reporting counts. Do not present test-count growth or a coverage percentage as the principal evidence of success.

Proceed autonomously on reversible decisions. Respect repository policies, preserve unrelated work, and obtain permission for destructive actions, commits, or pushes when required.

Guiding principle:\
A test is valuable because of the incorrect behavior it can detect.\
Coverage is meaningful only when the right behavior is actually asserted.\
Completion requires evidence, not merely a green summary.
