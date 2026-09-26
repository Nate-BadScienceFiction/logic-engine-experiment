# How the engine grew

*The long version of the story in the [README](../README.md).* This page covers what the engine could do at each stage, what it took to get there, and what went wrong along the way. It's organized by what became *possible*, not by which module was rewritten.

**Sources.** Dates and counts come from the engine's private repositories: commit history, the test log the project kept from the start, and small programs run against saved snapshots of each engine. The test counts are "passing pytest cases" as logged at the time. They measure activity more than quality; [evidence/README.md](../evidence/README.md#what-the-test-counts-mean) explains why. Where something is my inference rather than a record, I say so.

## Same programs, three engines

The most direct way to see what changed is to run small, textbook programs on saved snapshots of each engine, with SWI-Prolog 10.0.2 as the reference.

| Program and query | SWI-Prolog | Feb 2026 | Aug 2026 | Rewrite, Sep 2026 |
|---|---|---|---|---|
| `c(X) :- X = 1, !.`  `c(2).`  → `c(X)` | 1 | 1, 2 | 1, 2 | 1 |
| `max(X,Y,X) :- X >= Y, !.`  `max(_,Y,Y).`  → `max(3,2,M)` | 3 | 2, 3 | 2, 3 | 3 |
| `e(a,b). e(b,c). e(c,d).`  `lp(X,Y) :- lp(X,Z), e(Z,Y).`  `lp(X,Y) :- e(X,Y).`  → `lp(a,Y)` | b, c, d (with tabling) | b | b, c, d | b, c, d |
| `item(a). item(b). blocked(b).`  `s(X) :- \+ blocked(X), item(X).`  → `s(X)` | none | a | a | none |
| `p(1). p('1'). p(1.0).`  → `p(X)` | 1, '1', 1.0 | not run | 1 | 1, '1', 1.0 |
| `t(X) :- X is a + 1.`  → `t(X)` | type error | not run | no answers | type error |

How to read it:

- **Cut.** The first two rows are the classic uses of cut: stop trying later clauses. The earlier engine never pruned a later *fact* clause, before or after the move to its own repository.
- **Left recursion.** Left recursion over a chain was incomplete in February, then complete again by August.
- **The negation row is a difference in meaning, not simply a bug.** Prolog evaluates goals left to right, so `\+ blocked(X)` fails while `X` is still unbound. The earlier engine reordered the goals and answered `a`, which is what the rule *means* declaratively, but not what Prolog does. The rewrite chose Prolog's behavior.
- **Sources.** The Feb and Aug columns are my runs, except the last two Aug cells, which come from the published comparison. The rewrite column is my runs.

## At a glance

| Stage | Dates | Passing tests | Python source | Headline |
|---|---|---:|---:|---|
| Prototype | Aug 2025 | hundreds | ~13,000 lines | Stories become facts that change over time |
| Rapid growth | Sep–Oct 2025 | 525 → 2,552 | → ~54,000 | Most of the Prolog basics; tabling |
| Consolidation | Nov 2025–Feb 2026 | → 3,846 | → ~61,000 | One path for negation; explanations; tools |
| Own repository | Feb–Aug 2026 | → 6,691 peak → 6,660 | → ~54,000 | Bug waves, AI audits, deletions, a host API |
| Rewrite | Sep 2026 | 540 → 1,144 | ~7,400 | Rebuilt from a brief, old engine as reference, verification first |

Source sizes are non-test Python in each source tree. The earlier tree also held a parser, a command-line game and tools, so the rewrite's figure isn't an engine-for-engine comparison.

---

## 1. A weekend prototype (August 2025)

I'd been writing short science-fiction stories on Substack, and I wanted to see whether their worlds could live in a logic engine: who is where, what they know, what changed and why. Over a weekend, Claude Code and GPT-5 helped me turn a few stories into Prolog-style facts, plus a Python engine to reason over them. I [wrote about it](https://natecombs.substack.com/p/fly-by-wire-coding-with-ai) at the time as "fly-by-wire coding": the code arrived faster than I could read it, and I steered by asking the agents to analyze what they'd built.

The earliest surviving commit (Aug 30, 2025, a port from an earlier repository that isn't part of this record) shows what the prototype could do:

- **Story time.** An Event Calculus: events happen at time points and *initiate* or *terminate* fluents (facts that can change), and a fluent persists until something ends it. It already had tie-break rules for simultaneous starts and stops.
- **Provenance from the start.** Generated facts could carry an ID pointing back to the span of story text they came from.
- **Rules, sort of.** Rules were evaluated a whole set of answers at a time, with goals reordered for efficiency. That's closer to a database query than to Prolog.

It had no Prolog-style backtracking, no cut and no arithmetic. On that snapshot, a left-recursive rule crashed Python's stack, a clause with a cut returned nothing, and `Y is X * 2` returned nothing.

## 2. Growing up fast (September–October 2025)

**Passing tests 525 → 2,552. Source roughly 13,000 → 54,000 lines.**

Most of the Prolog basics arrived in these two months:

| Date | Capability |
|---|---|
| Aug 31 | Disjunction (`;`) evaluated at run time |
| Sep 4 | A depth-first, backtracking evaluator (a goal stack with choice points) |
| Sep 6–7 | Cut parsed and handled |
| Sep 8–9 | Proper variable identity during unification |
| Sep 14 | A router choosing between the original set-at-a-time evaluator and the new backtracking one |
| Sep 23–27 | `forall`, if-then-else, `member`/`append`/`length`/`sort`/`findall`, list syntax, `between`, atom built-ins, integer division |
| Oct 12 | Tabling, so recursive rules terminate |
| Oct 17 | Caches invalidated by an "epoch" counter |

One detail explains a lot of what follows. The router sent almost every query to the *original* evaluator. The backtracking engine only saw a short allowlist of predicates and, eventually, queries containing a cut. So for most of its life the earlier engine had Prolog's syntax and unification but not its execution model: it deduplicated answers and reordered goals.

It was a noisy two months:

- **Sep 8–9.** A refactor of variable identity took the suite from 25 failures to a worst point of 317 failures and 105 errors. The first all-green commit came eleven days later.
- **Oct 10–12.** An import reorganization plus the new tabling code briefly produced 827 failures.
- **Runtime.** A full test run went from about 18 seconds to several minutes. 59 logged runs took six and a half minutes or more, and the slowest took 13.

### The fix was the bug

By October the engine would sometimes vanish into runaway recursion, with the CPU pinned for minutes. The first remedy was a set of depth limits:

- a maximum evaluation depth of 100;
- a transitive-depth limit, raised from 10 to 20 to make a murder-mystery scenario work;
- a cap of 10 consecutive failures.

The runaways stopped. Path queries also started coming back short, with valid links missing from ancestor chains, and nothing said so.

I fed a pile of Claude's status reports to GPT-5, which had no access to the code. It diagnosed "unbounded recursion masked as 'maybe progress'" and suggested tabling. Claude implemented it on Oct 12. I [wrote that up](https://natecombs.substack.com/p/when-heuristics-bite-back) under the heading "the 'fix' was the bug."

The sequel didn't make the article. Two things went wrong.

**The depth limits never left.** They stayed in the code as a backstop, and in April 2026 one cap was raised from 20 to 50. At the end, a 60-link chain still came back with no path, and the only sign was a line printed to the console.

**The tabling wasn't complete.** The docs called the new code "SLG resolution," but it was answer memoization without the part that makes tabling complete: a recursive call got whatever partial answers existed, and the "fixpoint" loop never actually ran. Left-recursive queries returned incomplete answers (a snapshot from just before the change was already incomplete too). Every tabling test recursed the other way, so the suite stayed green. It took until June 2026, and an AI audit, to find that the "saturation loop that ensures completeness" had never run.

## 3. Consolidation, and what the tests couldn't see (November 2025–February 2026)

**Passing tests 2,552 → 3,846. Source roughly 54,000 → 61,000 lines.**

- **Negation, untangled.** A February consolidation found five separate code paths for negation as failure, each with its own rules about unbound variables, and merged them.
  - One path had used a Python idiom, `any(answers)`, since September. An answer that binds no variables is an empty dict, and Python treats an empty dict as false, so "yes, true, nothing to bind" read as "no."
  - A January change removed a "HACK" that let negation run on partly bound goals. It had been carried along through several refactors.
  - A stratification analyzer was written but only ever called from tests.
- **Explanations.** A query explainer (October), an explanation module (November) and a timeline explainer (December) grew out of the original provenance IDs.
- **Tools around the engine.**
  - "The Spider," a story-graph viewer (December).
  - A code analyzer that mapped the codebase for the agents (September to December).
  - A loop detector nicknamed Harriet (October), never wired into the engine.
- **A jump that wasn't new capability.** On Jan 6, passing tests went from 3,116 to 3,473 because 368 white-box test functions for internals were back-filled.

The last snapshot before the move to a dedicated repository (Feb 21, 2026) still got the basics in the table above wrong. The tests missed them for specific reasons:

- **Cut.** Cut tests mostly asked yes-or-no questions, such as "is `c(1)` true?", which can't reveal an extra answer.
- **Recursion.** Recursion was tested in one direction only.
- **Benchmark special-casing.** In October a correctness fix cleared the caches before every query, which cost 36% on an engine-switching benchmark. To win it back, the engine cleared caches only for certain queries, chosen partly by predicate name, including `theory`, the murder-mystery benchmark's predicate. Correctness now depended on a list of names. The benchmark itself had been edited to make it satisfiable.

## 4. Its own repository (February–August 2026)

**Passing tests 3,846 → 6,691 (May 6) → 6,660. Source roughly 61,000 → 54,000 lines.**

The engine moved into a dedicated repository on Feb 22.

- **March: bug waves.** Commit messages claim about 160 issues fixed between late February and March 20, some with regression tests and some without. New capabilities included:
  - `why/1`, `derivation/1` and `evidence_chain/1` (Mar 4);
  - numeric equality `=:=`;
  - recursion detection over strongly connected components;
  - a parser rewrite.

  The suite grew by about 2,500 tests in March alone, the biggest month on record.
- **April–May: speed.** An answer cache and indexing were switched on by default (Apr 24). The cache handed every caller the same internal list, so a caller that appended to a result changed what the next identical query returned. A test pinned that behavior as a "contract," and it was never fixed. The caching itself was worth having. On a repeated query it made this engine about a hundred times faster than the rewrite, and copying each answer before handing it out would have fixed the bug while keeping nearly all of that speed ([evidence](../evidence/README.md#what-isnt-measured)).
- **June: the audits.** Several AI reviews ran on June 12–13.
  - **Fable 5.** A static read by Claude (Fable 5), split across 14 reviewers, with no tests run. Its verdict: the engine worked for the shipped stories, and its "failure mode just outside that envelope is **silence**."
  - **A 324-agent review.** Another review used 324 agents over about two hours. Its 295 raw findings went through adversarial verification: 18 were refuted outright and about 150 downgraded, leaving 1 critical, 5 high, 40 medium and about 229 low. Its headline: the engine was "largely correct on its shipped KB," and "Its real disease is structural."
  - **The critical finding** was tabling: the completeness loop had never run. It was fixed on June 14. The same day, about 5,200 lines of dead code were deleted, along with roughly 260 tests (about 4% of the suite) that had only ever exercised that code.

  I [wrote about the review](https://natecombs.substack.com/p/what-fable-found-in-my-logic-engine) and decided on consolidation rather than a rewrite. That decision lasted about three months.
- **July–August: more basics.**
  - The backtracking evaluator had been dropping every alternative after the second.
  - Clauses containing a cut had always failed on that path.
  - Answer order depended on Python's hash seed, so it could change between runs.
  - A top-level if-then-else always returned no answers.
  - Inside a rule body, one matching fact could hide every rule answer.
  - Some Event Calculus tests still passed with the Event Calculus switched off.
  - A small host API landed in August, with "can I do this here?" game hooks.

**Where it ended, Aug 30, 2026** (from probes of that snapshot, beyond the table at the top):

- Simple left recursion was complete, but mutual left recursion found 1 of 4 answers.
- Recursion deeper than 50 levels was silently cut off, with only a printed warning.
- The natural numbers came back as `{0, 1}`, and `nat(3)` failed.
- `findall` over a conjunction returned an empty list.
- `s :- \+ s.` answered true.
- Division by zero failed silently instead of raising an error.
- Adding facts while other threads queried produced exceptions and wrong empty answers. (The rewrite doesn't support concurrent updates at all.)

By the audits' account it still handled its shipped stories, and it still passed 6,660 tests.

## 5. Starting over (September 2026)

**Tests 540 → 1,144 (a new suite). Source about 7,400 lines.**

In September I tried the other strategy: start over. Over three days I wrote [three prompts](prompts/README.md), about 540 lines in all, and had agents build a new engine from them in a new repository, without importing or copying the old code. Besides goals and non-goals, the prompts prescribed how to check the work: an adversarial architecture review, mutation testing in separate worktrees, an audit of the old tests, and negative cases that distinguish a correct engine from "an always-empty or always-successful one." The old repository stayed available as a read-only "working reference implementation." The first prompt describes it as a source of "semantic requirements, domain knowledge, useful algorithms, and regression cases," not a blueprint. The detailed behavioral contract, architecture notes and list of limitations were written by the agents, as part of the first kernel commit. The first prompt asked for:

- one semantic model;
- rule-body goals and top-level queries that agree;
- query-local state that can't leak;
- story time kept separate from knowledge-base edits;
- provenance designed in rather than scraped from logs;
- a hard line between "false" and "didn't finish."

Its non-goals were just as explicit. The first was "Do not expand this into a general-purpose Prolog implementation." Test-count parity was another.

| When (2026) | What happened |
|---|---|
| Sep 13, 19:51 | Seed prompt committed |
| Sep 14, 05:56 | First kernel commit: kernel, docs and 540 tests, after an adversarial architecture review and 36 deliberate mutations (10 defects fixed before the commit). Replayed later, this commit already passes 17 of the 21 cross-checks |
| Sep 14, evening | Second prompt: a test-migration and adversarial coverage audit |
| Sep 15 | Old suite audited file by file; 842 tests. Third prompt that evening: audit the suite and kernel "in both directions" |
| Sep 16 | Audit "in both directions": about 20 more defects; 1,023 tests |
| Sep 22 | Five parallel AI reviewers, plus a sixth told to refute the fix plan: 5 wrong answers, a crash, a state leak; 1,144 tests |
| Sep 22 | Comparison harness against the old engine, with SWI-Prolog as referee |
| Sep 24 | Harness hardened; results published |

**What happened to the old tests.** The migration audit went through all 6,778 test cases in the old suite:

| The rewrite's classification (made file by file) | Cases | Share |
|---|---:|---:|
| Kernel behavior: adapted, already covered, or consolidated | 2,519 | 37% |
| Tested machinery the rewrite removed | 3,421 | 50% |
| Application layers left out (game, CLI, tools) | 800 | 12% |
| Blocked on a deferred feature | 38 | <1% |

These are the rewrite's own judgments of its predecessor's tests, and tests of internals weren't worthless in their time. The audit also found:

- a test fixture that swapped in a fake engine answering hard-coded values;
- a helper that returned only true or false, so a whole family of tests "could not tell one answer from twenty";
- two tests that checked "at most one trust level at a time" loosened from `<= 1` to `>= 1`, printing a warning whenever the bug they were meant to catch occurred.

**The original comparison (historical scoring).** 21 small programs were run on both engines. 12 were refereed by SWI-Prolog (several also cite the ISO standard); 8 were judged by recorded rulings; 1 combined an SWI answer with a judgment about the Python API. Under the original rules, the rewrite passed 18 and the old engine 10. The [September 25 rerun with corrected scoring](../evidence/comparison-revised-2026-09-25.md) records old **11 pass / 10 fail** and rewrite **16 pass / 3 fail / 2 unknown**. The figures below describe the original report, not the current score. [evidence/README.md](../evidence/README.md#the-21-check-comparison) has the breakdown. The short version:

- **Timeouts.** Two of the rewrite's passes were test-runner timeouts on endless searches.
- **A miscounted refusal.** One of the old engine's failures is a refusal the harness couldn't decode. A stricter count gives it 11.
- **One-sided coverage.** The checks test places where the old engine departs from ISO, but not the rewrite's own departures, nor story time, provenance or the game hooks.
- **Missed old-engine bugs.** The corpus missed some of the old engine's deepest bugs. Its cut check puts the cut in the middle of a clause body, which the old engine handled.

**What the rewrite gave up:**

- rule-level "why";
- cross-query caching;
- cut inside recursive predicates;
- programs that are safe only because of their data;
- concurrent updates;
- the text parser, command-line game and tools.

**What it still gets wrong, without saying so:**

- **Timed effect rules.** Its Event Calculus reads them in a non-classical way, so a classical "toggle" or conditional effect rule gets a different answer.
- **Unsupported built-ins.** Things like `catch/3` quietly fail unless you turn on strict mode.

It also slows down sharply on some recursive code. [ENGINE.md](ENGINE.md#known-gaps) lists these and the rest.

## Sources

The engine repositories are private. Links will be added when they're released.

- **Earlier engine, sandbox era** (Aug 2025–Feb 2026): `BSF2-IF-Experimental`.
- **Earlier engine, own repository** (Feb–Aug 2026): `BadScienceFiction-CyclopsStorm`, final commit `e62758c`.
- **Rewrite:** `AkiyaBlocks-CyclopsStorm`, commit `9be7804`.
- **Articles written along the way** are listed in [AI-DEVELOPMENT.md](AI-DEVELOPMENT.md#further-reading).
