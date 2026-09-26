# Prompt 1: design brief

September 13, 2026 · [All three prompts](README.md) · Next: [test-migration audit](2-test-migration-audit-2026-09-14.md)

> As I wrote it, from `prompt.md` in the rewrite's repository (AkiyaBlocks-CyclopsStorm, private for now), commit `f575672`. Two changes: local folder paths are replaced with repository names, and numbered section titles are shown as headings.

---

SOURCE REPOSITORY:\
BadScienceFiction-CyclopsStorm

DESTINATION REPOSITORY:\
AkiyaBlocks-CyclopsStorm

Design and implement a ground-up Python successor to CyclopsStorm’s reasoning kernel, translating the required functionality from the source repository into the destination repository.

This is an architecture-first replacement, not a file-by-file translation, cosmetic reorganization, or additional abstraction layer around the existing engine.

The source repository provides semantic requirements, domain knowledge, useful algorithms, and regression cases. It is NOT the blueprint for the new internal architecture.

The objective is a coherent, deterministic, embeddable reasoning engine that is easier to understand, verify, and extend. Favor clear semantic boundaries, explicit ownership of state, and a small number of cohesive components over frameworks, elaborate class hierarchies, and layers of forwarding methods.

Choose the detailed architecture, algorithms, package organization, and implementation sequence yourself. Challenge the directions below where necessary, but explain substantive departures.

### 1. SOURCE AND DESTINATION RULES

Treat BadScienceFiction-CyclopsStorm as read-only. Do not refactor, rename, move, delete, or modify its tracked files. Preserve it as the working reference implementation.

Put the successor implementation, translated tests, required model assets, documentation, and development tooling in AkiyaBlocks-CyclopsStorm.

Inspect both repositories and their instructions before making changes. Preserve unrelated work. If the destination already contains an implementation, assess it rather than assuming the directory is empty or replacing its contents wholesale. If the destination does not exist, create it without disturbing the source.

The destination must become a self-contained project. Its normal installation, execution, and tests must not require the source repository to be present.

Copy authored .pl models and necessary fixtures unchanged where needed. Do not rewrite domain knowledge to accommodate the replacement. Distinguish production assets from test-only fixtures and migrate only what has a clear purpose.

An optional differential-testing harness may reference the source repository explicitly. Keep that dependency outside the replacement kernel and its ordinary unit tests. Prefer isolated execution when comparing implementations so their imports, environments, and global state cannot interfere.

Maintain a concise migration map showing which source responsibilities are reimplemented, intentionally reused, replaced by a simpler approach, deferred, or omitted with justification. Map responsibilities and behavior, not necessarily individual files.

### 2. UNDERSTAND THE PRODUCT BEFORE DESIGNING ITS REPLACEMENT

Study the actual models, consumer interfaces, production execution paths, meaningful tests, and previous assessments. Verify historical findings against current code rather than assuming they remain accurate.

First extract a concise behavioral specification and representative workload set. Establish what CyclopsStorm must mean and do, independently of how the current implementation achieves it.

Distinguish:
- Intended semantics and externally important behavior.
- Compatibility requirements that consumers actually depend on.
- Known defects, contradictory expectations, and unresolved semantics.
- Internal mechanisms that exist only because of the current architecture.

Pay particular attention to variable identity, unification, clause ordering, facts combined with rules, recursive evaluation, negation and procedural control, temporal reasoning, mutation, provenance, and result completeness.

Do not treat every existing test as an architectural requirement. Separate tests of meaningful behavior from tests coupled to private methods, incidental object structures, or historical workarounds.

Translate useful behavioral tests into the destination’s testing structure. Preserve their semantic intent without reproducing dependencies on the old implementation’s private machinery.

Keep the scope focused on CyclopsStorm’s actual requirements. Do not expand this into a general-purpose Prolog implementation or embed AkiyaBlocks-specific gameplay into the reasoning kernel merely because of the destination repository’s name.

### 3. DESIGN FROM SEMANTICS AND OWNERSHIP, NOT THE OLD MODULE TREE

Before substantial implementation, produce a concise architecture brief grounded in the behavioral specification.

Explain:
- The authoritative internal representations.
- Where each important semantic decision belongs.
- Who owns mutable state and how long that state lives.
- The permitted dependency directions.
- How a complete query executes.
- How knowledge changes affect subsequent queries.
- Where host compatibility and presentation concerns stop and the kernel begins.

Consider a credible simpler alternative and explain why the selected design is preferable. Do not manufacture a long menu of architectures.

Do not assume an existing subsystem, class, registry, cache, or routing mechanism deserves an equivalent in the new design. Ask whether the responsibility is necessary and whether the mechanism can disappear entirely.

Where separate agents are available, have the initial architecture proposal start from the behavioral specification and workloads rather than the old package layout. Then use a reviewer familiar with the source implementation to identify missed requirements.

The purpose is to reduce architectural imitation without discarding hard-won semantic knowledge.

Keep the design idiomatic to Python. Use explicit types, straightforward functions, and small objects where they clarify the model. Do not simulate a Rust ownership system or optimize for a hypothetical future language port.

### 4. ARCHITECTURAL OUTCOMES TO ACHIEVE

Establish one authoritative semantic model. Different input formats and execution representations may be useful, but conversions must be explicit and consistent. Avoid propagating interchangeable strings, legacy wrappers, and partially normalized objects throughout reasoning.

Ensure that top-level queries and equivalent goals inside rules agree wherever their semantics should agree. Multiple evaluation strategies may be appropriate; multiple competing definitions of the same operation are not.

Make query-local state explicit and isolated from shared knowledge. A query must not accidentally inherit another query’s substitutions, partially evaluated tables, or transient control state.

Distinguish story time from knowledge-base revision. Make the relationship between mutation, caches, tables, and query visibility explicit rather than dependent on scattered invalidation conventions.

Give temporal effects, conflict resolution, and persistence clear responsibilities. Their interaction with ordinary rule evaluation should use defined interfaces and execution context rather than unrestricted access to one another’s internals.

Treat provenance and explanation requirements as part of the design. Do not reconstruct semantic truth from incidental logging output, and do not let explanation generation require unbounded enumeration of proof histories.

Distinguish complete logical failure from incomplete computation, resource exhaustion, cancellation, unsupported semantics, and execution errors. Never silently translate these into an empty answer set.

Keep compatibility at the boundary. The new kernel must execute independently of the old reasoning implementation.

Prefer removing the need for a mechanism over introducing another coordinator to manage it. Introduce registries, extension systems, shared mutable services, and additional caching layers only for demonstrated requirements.

### 5. CHALLENGE THE ARCHITECTURE BEFORE LARGE-SCALE MIGRATION

Use an adversarial architecture review before expanding implementation.

The reviewer should look specifically for:
- Old coupling reproduced under new names.
- Multiple sources of semantic truth.
- Circular dependencies or components reaching into private state.
- Hidden global or shared query state.
- Compatibility logic leaking into the kernel.
- Caches compensating for unclear ownership or execution rules.
- Excessive fragmentation into trivial classes and forwarding layers.
- A design that handles ordinary examples but cannot explain difficult cases.

Walk representative difficult scenarios through the proposed design, including mutual recursion, variable scoping, procedural control interacting with backtracking, temporal boundaries, competing fluent effects, and a query repeated after mutation.

Explain where the relevant invariants are enforced. A box-and-arrow diagram alone is not sufficient.

Resolve material architectural objections before broad implementation. Record unresolved semantic decisions honestly rather than concealing them behind generic interfaces.

Do not require certainty about every future feature. Make reversible decisions, implement a challenging vertical slice, and revise the architecture when evidence warrants it.

### 6. IMPLEMENT AN INDEPENDENT VERTICAL SLICE

Create a clearly organized Python package in AkiyaBlocks-CyclopsStorm with an import namespace that does not collide with the source implementation.

Start with a bounded but substantial end-to-end milestone: authored input is loaded, queries execute with meaningful variable bindings, representative recursive and temporal behavior is exercised, mutations are handled, and structured results are returned.

Include cases that can expose weaknesses in the architecture, not just trivial fact retrieval. Clearly identify supported, deferred, and unsupported language features.

Do not build a large collection of empty abstractions or placeholder subsystems. Make the architecture executable early and expand it through verified behavior.

The replacement must not import the old kernel’s reasoning internals or silently fall back to the old engine for unsupported queries. Select the old or new backend explicitly for a complete workload or session.

Reuse existing code only when it is genuinely self-contained, semantically understood, independently tested, and fits the new design without bringing its old dependencies with it.

Do not rewrite a sound leaf algorithm merely for novelty. Equally, do not migrate a subsystem wholesale merely because it already exists. Record significant reuse decisions in the migration map.

Keep host adapters thin. Do not rewrite unrelated applications, narrative tools, or interfaces as part of this initial kernel replacement.

### 7. PROVIDE WINDOWS .BAT TEST RUNNERS

Provide convenient .bat files in the destination repository for running tests on Windows.

At minimum, provide:
- run_unit_tests.bat: runs the unit-test suite.
- run_tests.bat: runs the complete correctness suite, including relevant integration and conformance tests.

Keep performance benchmarks opt-in rather than part of the default correctness run. Add other scoped runners only where they are useful.

The batch files must:
- Work when invoked from a different working directory.
- Handle repository paths containing spaces.
- Use the project’s documented Python environment reliably.
- Forward additional test-runner arguments for selecting or diagnosing tests.
- Return the underlying test command’s exit status so failures remain visible to callers and automation.
- Report missing environment setup or dependencies clearly.
- Avoid unconditional pauses, hidden dependency installation, and swallowed errors.

Keep the launchers thin. They should invoke the same test configuration used by ordinary command-line development, not maintain a second definition of the test suite.

Document environment setup and a few practical commands for running all unit tests, selecting a subset, and running the full correctness suite.

The normal runners must work without BadScienceFiction-CyclopsStorm being installed or present. Any optional comparison runner that uses the source repository must be clearly separate and accept a configurable source location.

Execute and verify the .bat runners on Windows when available. If native Windows verification is unavailable, state that limitation explicitly rather than claiming they were tested.

### 8. VERIFY SEMANTICS AND ARCHITECTURE

Build portable conformance scenarios containing authored input, operations, queries, expected ordered answers, and relevant error/completion and provenance expectations.

Use the old engine as a comparison implementation, not an infallible oracle. Investigate differences against the behavioral specification and independently derived expectations.

Do not preserve known defects solely to achieve parity. Do not weaken assertions, silently change semantics, or modify models to make the replacement appear compatible. Record intentional behavioral changes explicitly.

Test semantic boundaries and interactions, not just components in isolation. Include checks for query-state isolation, repeated execution, mutation, ordering, and equivalent query forms.

Add lightweight architectural checks where useful, such as preventing imports from the legacy kernel and enforcing important dependency boundaries. Use behavioral tests for architectural properties that cannot be established by import checks alone.

Use an independent testing pass. Challenge critical tests to establish that they detect plausible incorrect behavior. Keep source-mutating experiments out of the original repository and isolate parallel edits or mutation testing in separate worktrees where appropriate.

Measure representative performance after correctness is established. Report meaningful regressions and bottlenecks, but do not distort the architecture around speculative optimization.

### 9. COMPLETE A RUNNABLE FIRST MILESTONE

Do not stop at a proposal or an empty package. Leave a runnable, tested foundation in AkiyaBlocks-CyclopsStorm that demonstrates the architectural approach.

Maintain concise documentation covering the behavioral contract, architectural decisions, migration map, current limitations, and how to run verification through the supplied .bat files.

At the milestone, report:
- What the new engine can actually do.
- Which source responsibilities have been migrated and which remain.
- Which architectural problems the new design eliminates and how.
- What tests, comparisons, and Windows launcher checks were run.
- Remaining semantic questions and compatibility gaps.
- The exact commands for running unit tests and the correctness suite.
- The next bounded implementation stage.

Proceed autonomously on reversible choices. Respect repository policies, preserve unrelated work, and obtain permission for destructive operations, commits, or pushes when required.

Guiding principle:\
Translate the intended behavior into a deliberately chosen architecture.\
Preserve the semantic knowledge, not the history of the first implementation.
