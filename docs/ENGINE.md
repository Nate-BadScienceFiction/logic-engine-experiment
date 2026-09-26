# The engine, precisely

*For readers who know Prolog, or want to.* This page covers the current engine, the September 2026 rewrite (commit `9be7804`): what it does, where it departs from ISO Prolog and SWI-Prolog, and where it's known to fall short. Behavior described here was checked by running programs against that commit, with SWI-Prolog 10.0.2 as the reference. Terms are in the [glossary](GLOSSARY.md).

## In brief

A small, deterministic Python kernel (about 7,400 lines, no runtime dependencies) for a Prolog dialect aimed at story worlds:

- **Two execution paths.** Non-recursive predicates run by ordinary SLD resolution with backtracking. Recursive predicates are detected and tabled automatically, then evaluated by naive fixpoint iteration. On that path cut is rejected, and answers are sets.
- **Stratified negation, checked per predicate before any query runs.**
- **A native Event Calculus** (`holds_at/2`) with explanations produced by the same procedure that answers the query.
- **Every result carries a status:** `COMPLETE` or `EXHAUSTED`.

It deliberately isn't a general-purpose Prolog. By default, undefined and unsupported predicates fail quietly, with status `COMPLETE`. [Known gaps](#known-gaps) lists the places where it can be wrong without saying so.

## Facts, rules and story events

Facts record relationships; rules infer new ones:

```prolog
parent(alice, bob).    parent(alice, carol).    parent(bob, dave).
grandparent(X, Z) :- parent(X, Y), parent(Y, Z).
```

Ask `grandparent(alice, Who)`. The engine finds bob among alice's children, then dave among bob's children. It backs up to try carol, who has no recorded children. The answer is `dave`, a relationship nobody explicitly wrote down. Backtracking explores those alternatives; tabling remembers answers for recursive rules, subject to the finiteness and budget limits below.

The Event Calculus adds changes over time. An event such as Harriet's hack switches a property such as the vending machine being offline on or off. The engine follows that property's persistence through the named story moments. Its explanation identifies the initiating event and, when recorded in the model, a supporting sentence. The [timed-rule example below](#story-time-the-event-calculus) explains the limits of this interpretation.

## Quick reference

For a feature-by-feature table with SWI references and recorded executable probes, see [Prolog compatibility](PROLOG-COMPATIBILITY.md). The summary below describes the broader design; that page identifies exactly which examples were verified.

| Area | Behavior | Versus ISO / SWI |
|---|---|---|
| Syntax | ISO operator table, fixed | No `op/3`. `"abc"` reads as the atom `abc`; no strings, no `0'c` |
| Unification | Trail-based; **occurs check on** | Off by default in SWI. `X = f(X)` fails |
| Numbers | `1 = 1.0` fails; `1`, `'1'`, `1.0` are distinct | As ISO |
| Resolution | SLD, depth-first, clause order; one ordered clause list per predicate; first-argument indexing | Standard, for non-recursive predicates |
| Answers | **Deduplicated at the top level by default**; `ask(goal, distinct=False)` reports SLD multiplicity for untabled goals | SWI reports every derivation. `findall/3` keeps duplicates, so top level and rule body can disagree on multiplicity |
| Control | `,` `;` `->` `*->` `\+`/`not` `!` `call/1..8` `once` `ignore` `forall` | No `catch/throw` |
| Cut | Local to the clause; local inside if-then-else conditions and `call/N` | **Rejected in any recursive (tabled) predicate**, which is more conservative than XSB. If-then-else and `once/1` are allowed |
| Negation | ISO `\+`: no reordering, no floundering check | Programs must be stratified *per predicate*; see below |
| Arithmetic | `//` truncates, `div` floors, typed errors | `X is a + 1` raises a type error, as in SWI |
| Built-ins | 74 built-in predicates (counting `once/1`, `forall/2`, `ignore/1` and `holds_at/2`): lists, `findall/bagof/setof/aggregate_all`, `sort/msort`, `=..`, `functor/arg/copy_term`, atom and number conversion | No `assert/retract` as goals, exceptions, I/O, DCG, modules, constraints, `dif/freeze`, threads |
| Unknown predicates | **Fail with status `COMPLETE`** by default | ISO raises an existence error; `KnowledgeBase(unknown_fails=False)` does too |
| Recursion | Tabled automatically; left and mutual recursion terminate | See [Tabling](#tabling) for the conditions |
| Result status | Every result is `COMPLETE` or `EXHAUSTED` | SWI can do similar things per call (`call_with_inference_limit/3`, tabling restraints); here it's on every answer |
| Time | Native `holds_at/2` over `happens/initiates/terminates` | Not part of Prolog; see [Story time](#story-time-the-event-calculus) |
| Explanation | `explain(fluent, time)`, `spans_for(fact)` | No rule-level proof trees |

## Negation and stratification

`\+ G` succeeds if `G` has no solution. As in ISO, it binds nothing and doesn't check for floundering. The engine also doesn't reorder goals around negation. The earlier engine did, which sometimes gave the declaratively right answer, but not Prolog's.

Before any query runs, the program is checked for stratification: no predicate may depend on its own negation through any non-monotone construct. Those constructs are `\+`, `forall`, aggregates, if-then-else and soft-cut *with an else branch*, and `ignore/1`. The check looks through `^/2` and statically known `call/N` goals.

The check works at the level of predicates, not ground atoms. So programs that are safe only because of their data are rejected (in the literature, programs that are modularly but not predicate-stratified):

```prolog
move(a, b).  move(b, c).
win(X) :- move(X, Y), \+ win(Y).
% SemanticConflict: negation is not stratified: {win/1} depends on its own negation
```

SWI answers this program (`win(b)`), and with tabling it would use the well-founded semantics. This engine refuses it rather than guess. A dependency hidden behind a runtime `call/1` can slip past the static check. It's caught at run time and reported as `EXHAUSTED`, which overloads a status that otherwise means "a budget ran out."

## Tabling

Recursive strongly connected components are tabled automatically (`auto_table=True`); `:- table` also works. Tables are keyed by call variant and filled by naive iteration. All the tables in a stratum iterate together until nothing changes, which makes left and mutual recursion complete:

```prolog
road(a, b). road(b, c). road(c, a). road(c, d).
reach(X, Y) :- reach(X, Z), road(Z, Y).
reach(X, Y) :- road(X, Y).
% ?- reach(a, W).   W = b ; c ; a ; d      (terminates despite the cycle)
```

The conditions and costs:

- **Termination needs finiteness.** Recursion terminates and is complete when there are finitely many call variants and answers. An infinite answer set, such as `nat(z). nat(s(X)) :- nat(X).`, runs until the budget, as it would under tabling in SWI.
- **Answers from tabled predicates are sets.** Their order and multiplicity differ from plain SLD resolution.
- **Tables are query-local.** Nothing is reused across queries.
- **There's no semi-naive evaluation,** so later passes can repeat work on answers already found. The cost depends on the rules, call variants and term sizes; answer count alone does not determine it. The algorithm is closer to iterated (linear) tabling than to SLG.
- **No answer subsumption and no incremental tabling.**
- **Cut is rejected in tabled predicates, and the rejection is global.** Loading succeeds, but from then on *every* query on that knowledge base raises `SemanticConflict`, even `1 =:= 1`, until the clause is removed. A predicate that fails the stratification check does the same. Set `auto_table=False` to allow cut; left recursion then runs until the budget.
- **Tabling everything recursive has a price.** Ordinary recursive list code pays for it:

  | Query | Auto-tabled | `auto_table=False` |
  |---|---:|---:|
  | Splitting a 100-element list with a user-defined `append/3` | 4.3 s | 0.05 s |
  | Same, 50 elements | 0.4 s | 0.01 s |

  A left-recursive all-pairs "reaches" rule over a 160-link chain (12,880 answers) exhausts the default budget at 11,169 answers, correctly marked `EXHAUSTED`. The same rule written right-recursively finishes in 0.3 seconds, and the left-recursive form over 80 links completes in 1.6.

## Result status

Every query result carries a status (the code calls it `Completion`; it has nothing to do with Clark's completion):

- `COMPLETE`: the search ran to the end.
- `EXHAUSTED`: a budget ran out. The defaults are 2,000,000 resolution steps and a depth of 1,200. The answers found so far are returned; anything else is unknown.

`kb.query()` raises `IncompleteResult` rather than return an `EXHAUSTED` result, so an empty list never means "gave up." It can still mean "no such predicate," because of the quiet default for unknown predicates. `kb.ask()` returns partial answers with the status attached.

**Weak spots:**

- **The default budget is generous.** `nat(z). nat(s(X)) :- nat(X).` reports `EXHAUSTED` after 198 answers in about 5 seconds with a 20,000-step budget. With the default budget it would take, by extrapolation, around an hour.
- **Converting partial answers can be slow.** `gen(L) :- member(_, L).` reports `EXHAUSTED` in about 6 seconds, but converting its 1,498 partial lists to Python values takes about 100 more.
- **Integer arithmetic isn't budgeted.** `X is 10^5000000` counts as one step.

## Story time: the Event Calculus

```prolog
time(t1). time(t2). time(t3). time(t4).
before(t1, t2). before(t2, t3). before(t3, t4).
happens(switch_on, t1).    initiates(switch_on, light_on).
happens(switch_off, t3).   terminates(switch_off, light_on).
% ?- holds_at(light_on, T).    T = t2 ; t3
```

The engine implements a simplified Event Calculus in the style of the 1990s formulations (Shanahan's among them), evaluated natively rather than by Prolog axioms.

- **Vocabulary.** `happens/2`, `initiates/2,3`, `terminates/2,3` (facts or rules), `initially/1`, `holds_at/2`.
- **Time.** Time points are named by `time/1`, by `before/2`, by `happens/2`, or by the ground time in an `initiates/3`/`terminates/3` clause. Plain numbers work too. `T1 ≺ T2` means reachability in `before/2`, or numeric order. Points on unconnected chains are incomparable, and a cycle in `before/2` is reported.
- **When effects are visible.** A fluent initiated at *T1* and terminated at *T2* holds on (*T1*, *T2*]: strictly after it starts, up to and including the moment it ends. This is the standard reading. A rule body that asks `holds_at(G, T)` therefore sees the state *before* anything that happens at `T`.
- **Simultaneity.** `tie_break="init_wins"` (the default) or `"term_wins"` decides a tick where the same fluent is both initiated and terminated.
- **Exclusive fluents.** Only by declaration. `exclusive_fluent(f)` means `f` holds at most one value per slot, where a slot is the functor plus every argument except the last. Initiating `f(a, v2)` ends `f(a, v1)`. On a contested tick the first-authored initiation wins.

**Where it departs from the classical Event Calculus.** In the textbook axioms, the third argument of `initiates/3` and `terminates/3` is the *occurrence time* of an event that must also appear in `happens/2`. Here it's the time the effect lands, and `happens/2` isn't required. That lets a model be written entirely in the `/3` form. But conditional effect rules written the classical way mean something different:

```prolog
happens(flip, 1).  happens(flip, 3).  time(1). time(2). time(3). time(4). time(5).
initiates(flip, on, T)  :- \+ holds_at(on, T).     % a toggle
terminates(flip, on, T) :- holds_at(on, T).
% Classical reading (SWI with the textbook axioms):  on holds at 2, 3
% This engine:                                       on holds at 2, 4, explained by a
%                                                    termination at 2, when flip didn't happen
```

The answer comes back `COMPLETE`, with no warning. The same applies to any conditional timed rule. `terminates(check, on, T) :- holds_at(g, T).` fires at every moment `g` holds, not only when `check` happens. Even `terminates(check, on, _)` misfires.

Here, a timed effect rule has to say when its event happens:

```prolog
terminates(check, on, T) :- happens(check, T), holds_at(g, T).
```

The rewrite's own docs describe the 3-argument forms but never flag this departure from the classical reading.

## Explanations and provenance

- **`kb.explain(fluent, time)`** says why a fluent does or doesn't hold. It comes from the same decision procedure as `holds_at`, not reconstructed afterwards. The reasons are `initially`, `initiated` (by which event, when), `clipped` (by which event, when), `never_initiated`, and `unexplained` (a budget ran out).
- **`kb.spans_for(fact)`** returns the source-text spans the model records as supporting a fact, through authored `fact_id/2` and `supports/2` facts.
- **There are no rule-level derivations.** The engine doesn't record which clauses and bindings produced an answer. It has no `why/1`, `derivation/1` or `evidence_chain/1`, which is why it fails the three explanation probes in the [comparison](../evidence/README.md#the-21-check-comparison). And `explain()` on a fact that isn't a fluent reports `never_initiated`, even when the fact is true.

## Known gaps

| Gap | Example | Fails loudly? |
|---|---|---|
| Unknown or unsupported predicates fail | `catch(p, _, true)`, `assertz(q(1))` → no answers | **No**: status `COMPLETE`. Use `unknown_fails=False` while authoring |
| Timed effect rules use the effect-time reading | The toggle above | **No** |
| Effects at time points the model never names are invisible | `terminates(off, f, T2) :- happens(off, T), T2 is T + 1.` with `T2` unnamed | **No**: a conformance test pins this as a known limit |
| `explain()` on a non-fluent | `explain("anc(tom, bob)", …)` → `never_initiated` | **No** |
| Predicate-level stratification | `win/move` above | Yes, but globally: every query on the knowledge base raises `SemanticConflict` |
| Cut in a recursive predicate | `r(X,Y) :- e(X,Y), !.` plus a recursive clause | Yes, but globally, as above |
| Auto-tabling slows recursive list code | User-defined `append/3` on 100 elements: 4.3 s | No error; turn off `auto_table` for such code |
| Left-recursive closures over long chains exceed the default budget | All-pairs "reaches" over a 160-link chain | Yes (`EXHAUSTED`); the right-recursive form is fine |
| Infinite answer sets | `nat/1` | Yes (`EXHAUSTED`), but only after the budget, which can take a long time |
| No rule-level explanations | `why/1` | Yes: the predicate doesn't exist (and fails quietly, see row 1) |
| No concurrency support | Querying while another thread adds facts | Not designed for it; deferred |

## The host API

```python
from cyclops import KnowledgeBase

kb = KnowledgeBase()                     # options: occurs_check, tie_break, unknown_fails, auto_table, ...
kb.load(text) / kb.consult(path)         # add clauses
kb.query(goal)                           # answers as Python values; raises if the search didn't finish
kb.ask(goal, limits=..., distinct=...)   # Solutions: answers + status + notes
kb.holds(goal)                           # bool; raises if it gave up before finding an answer
kb.explain(fluent, time)                 # see above
kb.assert_(clause) / kb.retract(clause); kb.snapshot() / kb.restore(s)
```

- **Answer order** is part of the contract and is tested across processes and hash seeds.
- **JSON output** tags atoms and compounds and includes the status.
- **Game hooks.** `affords(Action, Site)`, `guard(Action, Order, Condition, Message)` and `action_label/2` let a host ask "may I do this here, and if not, what do I say?" Guards are checked in the author's order, and the first unmet one supplies the message. An action the site doesn't offer *abstains*, which is different from being denied.

## Performance

Revised full-binding timings on one Windows machine, September 25, 2026. Both engines materialize every requested variable; the rewrite uses native answer terms, with Python value conversion measured separately. See the [method, exact-answer checks, batch ranges and raw timings](../evidence/benchmarks-revised-2026-09-25.md).

| | Rewrite, automatic tabling | Rewrite, `auto_table=False` | SWI-Prolog 10.0.2 |
|---|---:|---:|---:|
| Naive reverse of a 30-element list | 107.88 ms | 9.20 ms | 0.00807 ms |
| All solutions of 6-queens | 507.74 ms | 205.68 ms | 0.55199 ms |
| All splits of a 100-element list | 4,201.41 ms | 18.60 ms | 0.22084 ms |

These measurements include query setup and result construction, and do not isolate interpreter overhead. SWI executes compiled goals; the rewrite parses each query. The list-split SWI and Python-conversion measurements varied substantially. The original placeholder-answer SWI ratios are superseded.

The earlier story-model audit measured about 20 ms to load 748 facts and 1–16 ms for example queries/explanations; those particular observations were not retimed in this benchmark run. There is no cross-query answer cache. The old engine's cache was fast and had a separate result-aliasing bug: fixing that bug would not eliminate the caching advantage.

## Design in one paragraph

There is one term representation, one reader, and one clause list per predicate holding facts and rules together. One solver serves top-level queries and rule bodies, and there is one `holds_at`. All long-lived state belongs to the program and is versioned by a single revision counter. Everything query-local lives in a context created per query and thrown away. Derived data (static analysis, the timeline, diagnostics) is tagged with the revision it came from, so staleness is detected by comparing one integer.

| Part | Lines |
|---|---:|
| Kernel: 17 modules for terms, syntax, bindings, program, solver, built-ins, arithmetic, tabling, analysis, temporal | 6,691 |
| Host boundary: values, JSON, affordances | 519 |
| Package `__init__` files | 216 |
| **Total** | **7,426** |
| Tests: 38 files; 1,144 correctness cases, plus 253 for the comparison harness | 13,137 |

## What changed from the earlier engine

The [migration drill-down](MIGRATION.md) supplies the measured comparison, test dispositions and capability gaps; the [revised 21-case run](../evidence/comparison-revised-2026-09-25.md) separates observed correctness from timeout uncertainty.

**Semantics the rewrite chose differently:**

- ISO `\+` with no goal reordering;
- ISO precedence for `,`, `;` and `\+`;
- `1` and `1.0` kept distinct;
- `//` truncates;
- exclusivity only by declaration;
- no `why`/`derivation`/`evidence_chain` predicates.

**Removed:**

- two-evaluator routing;
- a seven-stage query pipeline;
- a handler registry;
- a six-level cache hierarchy;
- five parsers.

**Left out:** the text parser, the command-line game, the narrative tools and the analysis tools.

**Deferred:** semi-naive tabling, cross-query caching, rule-level explanation and concurrency.

[HISTORY.md](HISTORY.md) runs the same programs on both.

## Compared with SWI-Prolog

SWI-Prolog is a complete, fast, largely ISO-conformant system with nearly 40 years of engineering behind it. For almost anything, use SWI; for Python, its `janus` bridge works well.

This engine is for one job: reasoning about authored story worlds, with answers you can explain. For that job it offers:

- a native Event Calculus whose explanations come from the decision procedure itself;
- source-sentence provenance;
- a result status on every answer by default;
- a small, dependency-free Python package.
