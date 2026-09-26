# Building it with AI agents

*For people using coding agents on real software.* The short version: agents produced plausible code and plausible tests faster than I could check either, and for most of a year I measured progress with the one number they were best at inflating. What follows is what's in the record: commits, test logs, review reports, and programs I ran. It covers one person, one project, and a moving set of models.

## Who did what

| Phase | Built by (from commit trailers) | Reviewed by | My role |
|---|---|---|---|
| Aug 2025–Feb 2026 | Claude via Claude Code: "Claude" (Oct), then Opus 4.5 and 4.6 | GPT-5 and 5.2, cited as reviewer in 14 commit messages | Direction, prompts, stories, commits |
| Feb–Aug 2026 | Opus 4.6, 4.7, 4.8, then Opus 5 (about 160 trailers; 41 commits have none) | One Codex review; the June audits by Fable 5 and Opus 4.8 | Same, plus deciding what the audits meant |
| Sep 2026 rewrite | Opus 5 on the 5 commits that carry a trailer; the first kernel commit has none | Agents only; no human code review is recorded | Wrote [three prompts](prompts/README.md) (Sep 13–15, ~540 lines) setting goals, non-goals and the verification regime; gated every commit |

I read far less of the code than I directed. Early on I [called this](https://natecombs.substack.com/p/fly-by-wire-coding-with-ai) "fly-by-wire coding": stay a step or two ahead, and steer by instrumenting and asking.

The retained record does not establish whether the first overnight run was unattended or which model wrote the first kernel commit. Spending by phase was not recorded.

## The scale

| | Earlier engine (Aug 2025–Aug 2026) | Rewrite (Sep 2026) |
|---|---|---|
| Commits touching engine code | ~320 in the sandbox era, ~160 in its own repository | 5 (plus docs and harness) |
| Days with engine commits | ~125 | 4 (6 days with any commit) |
| Python source (non-test) | peaked at ~61,000 lines | ~7,400 lines |
| Test code | ~96,000 lines at the end | ~13,000 lines |
| Passing tests | peaked at 6,691 | 1,144 (+253 harness self-tests) |

None of this measures productivity. I didn't record hours, and commit timestamps aren't hours worked.

## Failure modes, and what caught them

| Failure mode | A real example from this project | What caught it | A practice you can steal |
|---|---|---|---|
| **Silence**: plausible, incomplete answers, no error | Depth limits that cut off valid answers. Tabling whose completeness loop never ran. Recursion truncated at depth 50 with only a `print()` warning | A second model reading status reports (Oct 2025); AI audits (Jun 2026) | Make "didn't finish" a first-class result, not an empty list |
| **Tests that can't fail** | Two tests loosened "at most one trust level" from `<= 1` to `>= 1` and printed a warning whenever the bug fired. Event Calculus tests passed with the Event Calculus switched off | The old engine's own August test hardening; later, the rewrite's audit reading every test for what it could detect | Mutation testing; reverting each fix to check its test goes red |
| **Tests blind in one direction** | Cut tests that asked only yes-or-no questions. Tabling tests that all recursed rightward | Probing with textbook programs against an outside reference | An oracle (here, SWI-Prolog) plus deliberately adversarial cases |
| **Sediment**: the old path left beside the new | Five negation paths, five parsers, two evaluators, six cache layers. About 5,200 lines deleted in one day in June 2026 | The June audits | Delete as part of every refactor; audit for code with no callers |
| **Local fixes for global problems** | A speed fix keyed on the murder-mystery benchmark's predicate name. A loop "fixed" by rerouting one predicate | Code review by other agents, eventually | Grep for benchmark and test names in production code |
| **Confident wrong diagnoses** | Investigation notes backed one theory with "Confidence: 90%," and a commit summary "determined it requires senior architectural expertise." The fix was clearing stale caches between queries, written up as "Confidence: 100% (all tests passing)." It cost 36% in speed, and the workaround keyed cache clearing on predicate names | Me, rereading and redirecting | Ask for the cheapest experiment that would disprove the theory. Treat "all tests passing" as a claim, not a proof |
| **Self-reports that inflate** | "SLG-style tabling." Integration with NumPy and pandas that didn't exist. One debugging write-up claimed 270 new tests; the test log shows about a hundred added across the whole day | Checking claims against code and logs, for this write-up | Treat agent-written docs and summaries as claims to verify |

I don't think these patterns are unique to AI. They're what happens to any fast-growing codebase with weak feedback. Here they piled up faster than I could spot them.

## How verification changed

| Period | What "verified" meant |
|---|---|
| Aug–Dec 2025 | The test count went up and the suite was green |
| From Sep 2025 | A second model reviewed the first model's work |
| Jun 2026 | AI audits: static reads, then 324 agents reproducing and adversarially checking findings |
| Jul–Aug 2026 | The old engine hardened its own tests: tests that couldn't fail were rewritten, and assertion-free tests were given something to check |
| Sep 2026 | A written brief first; every test must be able to fail; an outside referee |

The rewrite's version, in specifics. Most of these were required by my prompts; the agents chose how to carry them out.

- **Mutation testing.** Deliberately break one line at a time, and some test should go red.
  - First campaign: 36 breakages, 26 caught on the first run. The survivors exposed a systematic blind spot: no test put a choice point before any construct that opens a fresh cut barrier.
  - Second campaign: 28 of 30 caught. Both survivors were fixtures that couldn't tell two behaviors apart.
  - The latest: 41 of 60 caught. Of the 19 survivors, 13 were real gaps, each now tested, and 6 were provably equivalent.
- **Broken engines.** Run the whole suite against four fake engines: one that answers nothing, one that says yes to everything, one that always reports "stopped early," and one that ignores changes after its first query. They turned 623, 626, 666 and 28 of 1,021 tests red respectively. Most of the 398 tests that stayed green against the empty engine never query the engine at all, because they test the parser and term types; the rest expect an error or a "no."
- **Refuters.** Five reviewers ran in parallel, one each on the solver, the Event Calculus and API, the syntax layer, the test suite, and the architecture against its own claims. Each was told that re-reporting a documented limit counts as a failed review. A sixth got the resulting repair plan and was told to refute it. It stopped three fixes. One, an over-broad stratification rule, would have wrongly rejected valid recursive rules written with a soft cut, "and the full suite, the benchmarks and the differential suite all stayed green with that fix in place."
- **Scope, not just presence.** A reviewer given only a finished diff found that a status repair had been implemented against program-wide state. After it, one bad clause made *every* query report "stopped early," including `1 =:= 1`. The repair's own test "pinned the fix's presence and not its scope."
- **An outside referee.** Both engines were compared on 21 cases: 12 SWI-only expectations, one mixed SWI/host-API expectation and eight recorded adjudications. The original scoring was replayed across saved versions; the [corrected endpoint rerun](../evidence/comparison-revised-2026-09-25.md) no longer counts external timeouts as passes.

The June audit, for scale: 324 agents, about 15.6 million tokens, and about two hours of wall-clock time. Of its 295 raw findings, 18 were refuted outright and about 150 downgraded on verification. That leaves 1 critical, 5 high, 40 medium and about 229 low. Roughly half the raw findings were overrated until a skeptic reread the code.

## What the rewrite's checking missed

- **Timeouts counted as passes.** The comparison harness counted a timeout as "stopping" on two endless-search checks, so the engine's own "stopped early" status was never observed ([details](../evidence/README.md#the-21-check-comparison)).
- **A refusal counted as a wrong answer.** The harness couldn't decode the old engine's "No derivation path found" and scored it as an answer.
- **A known-wrong answer pinned as correct.** A conformance test asserts a known wrong Event Calculus answer as a "documented limit."
- **A departure nobody noticed.** The engine's docs describe its timed effect rules, but never say that they depart from the classical Event Calculus. A reviewing agent working on this write-up found the consequence, using a textbook toggle and SWI-Prolog.
- **No saved record of the reviews.** Mutation and review tallies disagree between documents, and the reviewers' raw reports weren't saved.

## What I can't claim

- **Whether starting over, or the model, did the work.** The rewrite's attributed commits name a newer model (Opus 5) than built most of the earlier engine. It had the old engine as a read-only reference, a year of lessons, and far more detailed direction from me. I can't separate those effects. One weak hint that the model isn't the whole story: Opus 5 also made the old engine's last 23 commits, in August. Those fixed several basics, but left clause-level cut and operator precedence wrong.
- **Any speed-up factor.** I didn't record effort or cost.
- **A controlled comparison.** The 21 cross-checks were written knowing both engines, and they cover neither story time nor provenance.
- **Anything general.** This is one developer's project. The practices above are ones I'd use again; I don't know how well they transfer.

On transfer: the oracle trick needs a reference. Here that was SWI-Prolog; elsewhere it might be a spec, an older system, or a slow but obviously correct implementation. The broken-engine and revert-the-fix checks need nothing but the test suite.

## Further reading

What I wrote along the way:

- [Fly-By-Wire Coding with AI](https://natecombs.substack.com/p/fly-by-wire-coding-with-ai) (Aug 2025)
- [Fly-By-Wire Debugging](https://natecombs.substack.com/p/fly-by-wire-debugging) (Sep 2025)
- [When Heuristics Bite Back](https://natecombs.substack.com/p/when-heuristics-bite-back) (Oct 2025)
- [Marching to Nines with a Robot](https://natecombs.substack.com/p/marching-to-nines-with-a-robot) (Nov 2025)
- [My Brief History of AI Coding](https://medium.com/ai-advances/my-brief-history-of-ai-coding-e9b0accc1593) (Feb 2026)
- [What Fable Found in My Logic Engine](https://natecombs.substack.com/p/what-fable-found-in-my-logic-engine) (Jun 2026)
