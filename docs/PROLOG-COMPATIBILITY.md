# Prolog features: SWI-Prolog and the rewrite

The rewrite supports a useful subset of Prolog, with important differences in defaults, recursion and available libraries. This comparison records **34 executable probes** against the September 2026 rewrite and SWI-Prolog 10.0.2. It describes observed behavior on those examples, not complete ISO conformance or a general correctness score.

[Raw programs, answers and errors](../evidence/prolog-features-2026-09-25.json) · [Reproduction script](../evidence/probe-prolog-features.py) · [Engine design and known gaps](ENGINE.md) · [Performance measurements](../evidence/benchmarks-revised-2026-09-25.md).

## How to read the comparison

**Match** means the tested behavior agrees. **Different default** means ordinary use differs, sometimes with an option to change it. **Restricted** means the rewrite rejects a program SWI can run. **Unavailable in probe** means the feature did not work through the tested syntax or predicate; the row records whether it failed quietly or raised an error. A quiet failure marked complete is especially easy to mistake for a meaningful negative answer.

Each row names its probe ID in the linked raw results. SWI links explain the reference behavior; the transcripts establish what the installed version actually did. Multiple predicates in one row are only checked in the modes shown in the probe. A match does not establish every argument mode, edge case, or interaction with tabling.

## Terms, syntax and answers

| Feature | SWI-Prolog | Rewrite: observed behavior | Evidence |
|---|---|---|---|
| Facts, rules and conjunction | Infers `g(a,c)` through two related facts. [Control](https://www.swi-prolog.org/pldoc/man?section=control) | **Match:** the same inference succeeds. | `rules` |
| Cyclic unification | `X = f(X)` succeeds with the default occurs-check setting. [Unification](https://www.swi-prolog.org/pldoc/man?section=compare) | **Different default:** returns no answers; occurs checking is enabled. | `occurs-check` |
| Integer versus float | `1` does not unify with `1.0`. [Unification](https://www.swi-prolog.org/pldoc/man?section=compare) | **Match:** `1 \= 1.0` succeeds. | `numeric-types` |
| Double-quoted text | `atom("abc")` is false under the default string syntax. [Strings](https://www.swi-prolog.org/pldoc/man?section=string) | **Different default:** succeeds; double quotes produce an atom. | `double-quotes` |
| Character-code literal | `0'a` evaluates to 97. [Syntax](https://www.swi-prolog.org/pldoc/man?section=syntax) | **Unavailable in probe:** query parsing raises `SyntaxErrorInSource`. | `character-code` |
| Defining operators | `op(500,xfy,likes)` succeeds. [op/3](https://www.swi-prolog.org/pldoc/doc_for?object=op/3) | **Unavailable in probe:** no answers, status complete. | `operators` |
| Duplicate answers | Two `p(a)` clauses yield two answers to `p(X)`. [Collecting solutions](https://www.swi-prolog.org/pldoc/man?section=allsolutions) | **Different default:** `ask` returns one; `ask(..., distinct=False)` returns two for this untabled predicate. | `duplicates`, `duplicates-opt-out` |

The duplicate comparison concerns the Python query boundary: it does not mean duplicates disappear inside every Prolog construct. The `findall/3` probe below preserves them.

## Control, recursion and errors

| Feature | SWI-Prolog | Rewrite: observed behavior | Evidence |
|---|---|---|---|
| Cut in an untabled predicate | A cut in the first clause removes the later alternative. [Cut](https://www.swi-prolog.org/pldoc/man?section=control) | **Match:** returns only `a`, not `b`. | `cut` |
| If-then-else | A failing condition selects the else branch. [Control](https://www.swi-prolog.org/pldoc/man?section=control) | **Match** on the tested branch. | `if-then-else` |
| Soft cut (`*->`) | Preserves both successful condition bindings in the example. [Control](https://www.swi-prolog.org/pldoc/man?section=control) | **Match:** returns `a` and `b`. | `soft-cut` |
| Negation as failure | Failed inner search leaves `X` unbound. [Negation](https://www.swi-prolog.org/pldoc/man?section=control) | **Match** on the binding-isolation example. | `negation` |
| Calling goals and taking one solution | `call/3` and `once/1` succeed in the example. [Meta-calls](https://www.swi-prolog.org/pldoc/man?section=metacall) | **Match** for these forms; higher call arities are not covered here. | `meta-call` |
| Left recursion with tabling | With an explicit `table path/2` directive, finds both reachable nodes. [Tabling](https://www.swi-prolog.org/pldoc/man?section=tabling) | **Different default:** automatically tables the recursive predicate and finds the same two nodes without a directive. | `left-recursion` |
| Cut in a recursive predicate | The untabled example succeeds and prunes its recursive alternative. [Cut](https://www.swi-prolog.org/pldoc/man?section=control) | **Restricted:** automatic tabling causes a `SemanticConflict`. This does not compare cuts inside SWI tables. | `recursive-cut` |
| Recursion through negation | The finite `win(b)` example succeeds under ordinary execution. [Negation](https://www.swi-prolog.org/pldoc/man?section=control) | **Restricted:** rejects the predicate's dependency on its own negation with `SemanticConflict`. | `recursive-negation` |
| Undefined predicate | Raises an existence error. [Prolog flags](https://www.swi-prolog.org/pldoc/man?section=flags) | **Different default:** no answers, status complete. With `unknown_fails=False`, raises `UnknownPredicateError`. | `unknown`, `unknown-strict` |
| Prolog exception handling | `catch(throw(ball),ball,true)` succeeds. [Exceptions](https://www.swi-prolog.org/pldoc/man?section=exception) | **Unavailable in probe:** no answers, status complete. Python exceptions from the engine are a separate mechanism. | `exceptions` |

The left-recursion probe has a finite set of calls and answers. It establishes neither unrestricted termination nor full equivalence with SWI's SLG tabling and well-founded negation. Resource limits and the rewrite's static restrictions remain relevant; see [Tabling](ENGINE.md#tabling) and [Negation](ENGINE.md#negation-and-stratification).

## Arithmetic and data predicates

| Feature | SWI-Prolog | Rewrite: observed behavior | Evidence |
|---|---|---|---|
| Negative integer division | `-10 // 3` is `-3`; `-10 div 3` is `-4`. [Arithmetic](https://www.swi-prolog.org/pldoc/man?section=arith) | **Match:** truncation and floor division differ correctly. | `arithmetic` |
| Invalid arithmetic | `X is a + 1` raises an evaluable-type error. [Arithmetic](https://www.swi-prolog.org/pldoc/man?section=arith) | **Match in error category:** raises Python `TypeCheckError`; the exception representation differs. | `arithmetic-error` |
| List operations | Append, membership and length satisfy the example's exact constraints. [Lists](https://www.swi-prolog.org/pldoc/man?section=lists) | **Match** for `append/3`, `member/2`, `length/2` in the tested modes. | `lists` |
| `findall/3` | Collects `[a,a]` from duplicate clauses. [All solutions](https://www.swi-prolog.org/pldoc/man?section=allsolutions) | **Match:** preserves multiplicity inside the collected list. | `findall` |
| `bagof/3` and `setof/3` | Produces `[b,a,a]` and `[a,b]`, respectively. [All solutions](https://www.swi-prolog.org/pldoc/man?section=allsolutions) | **Match** on this example; free-variable grouping and existential qualification are not exercised. | `bagof-setof` |
| Sorting | `sort/2` removes duplicates; `msort/2` retains them. [Term ordering and sorting](https://www.swi-prolog.org/pldoc/man?section=compare) | **Match** on the tested atom list. Mixed-type ordering is not tested here. | `sort` |
| Term inspection | Decomposes `f(a,b)` and reads its functor, arity and second argument. [Terms](https://www.swi-prolog.org/pldoc/man?section=manipterm) | **Match** for `=../2`, `functor/3`, `arg/3` in these modes. | `term-inspection` |
| Atom operations | Concatenation, length and atom-to-number conversion succeed. [Atoms](https://www.swi-prolog.org/pldoc/man?section=manipatom) | **Match** for the tested calls to `atom_concat/3`, `atom_length/2`, `atom_number/2`. | `atom-conversion` |

## Database, libraries and extensions

| Feature | SWI-Prolog | Rewrite: observed behavior | Evidence |
|---|---|---|---|
| Updating facts from a Prolog goal | Asserts, queries and retracts a fact. [assertz/1](https://www.swi-prolog.org/pldoc/doc_for?object=assertz/1) | **Unavailable in probe:** the conjunction fails quietly at `assertz/1`; later goals are not reached. The Python update API is separate. | `dynamic-database` |
| DCG grammars | Expands `s --> [a]` and recognizes `[a]` with `phrase/2`. [DCGs](https://www.swi-prolog.org/pldoc/man?section=DCG) | **Unavailable in probe:** loading does not raise an error, but `phrase(s,[a])` returns no answers, complete. Accepted syntax alone does not demonstrate DCG support. | `dcg` |
| Module-qualified calls | `lists:member(a,[a])` succeeds. [Modules](https://www.swi-prolog.org/pldoc/man?section=modules) | **Unavailable in probe:** returns no answers, complete. | `modules` |
| Integer constraints | With `library(clpfd)` loaded, `X #= 2, X #> 1` succeeds. [CLP(FD)](https://www.swi-prolog.org/pldoc/man?section=clpfd) | **Unavailable in probe:** constraint syntax raises `SyntaxErrorInSource`. | `constraints` |
| Disequality constraint | `dif(X,a), X=b` succeeds. [dif/2](https://www.swi-prolog.org/pldoc/doc_for?object=dif/2) | **Unavailable in probe:** returns no answers, complete. | `dif` |
| Delayed goals | `freeze(X,X=b), X=b` succeeds. [Coroutining](https://www.swi-prolog.org/pldoc/man?section=coroutining) | **Unavailable in probe:** returns no answers, complete. | `freeze` |
| Prolog output | `write(probe_output)` prints text and succeeds. [write/1](https://www.swi-prolog.org/pldoc/doc_for?object=write/1) | **Unavailable in probe:** no output and no answers, complete. | `io` |

These probes cover selected Prolog-facing operations. They do not evaluate the Python embedding API, story-time reasoning, source-sentence provenance, or explanation quality. Those are documented separately in [Engine](ENGINE.md#the-host-api) and the [migration comparison](MIGRATION.md). The older 21 shared cross-checks compare the two Python engines; this feature inventory is a separate experiment and does not change their scores.

## Verification and reproduction

Run September 25, 2026 in America/New_York (September 26 UTC), using Python 3.12.10 on Windows 11, SWI-Prolog 10.0.2, and clean rewrite commit `9be7804c933cc8a3c51af3d8a5e4f54b012c8be6`. The SWI documentation links are live reference pages and may describe a newer release; version-specific observations come from the saved run.

Each of the 34 probes runs in a fresh subprocess for each engine, with a ten-second external deadline. No probe timed out. The rewrite uses a new `KnowledgeBase` and default `ask` settings, except the explicitly labeled duplicate and strict-unknown probes. SWI starts with `-f none`; only the left-recursion probe adds a table directive and only the constraint probe adds a library directive. Standard SWI autoloading remains enabled.

The script records source programs, query strings, options, rewrite statuses and native answers, SWI canonical answer transcripts, errors, environment, timestamps and the script hash. The SWI wrapper collects instantiated copies of the whole goal; the rewrite records variable bindings. These representations are deliberately retained separately. The table's comparisons were reviewed against both transcripts; the script does not compute a compatibility percentage. Several queries contain exact-value constraints, while others expose values or duplicate counts for inspection.

```powershell
python -B evidence/probe-prolog-features.py --repo "C:/path/to/AkiyaBlocks-CyclopsStorm" --output "prolog-features.json"
```

The clean pinned private checkout is required. The script defaults to `C:/Program Files/swipl/bin/swipl.exe`; use `--swipl` for another installation. It changes neither engine. These examples are a reproducible starting point for compatibility work, not an exhaustive feature specification: threads, transactions, foreign interfaces, every built-in, and combinations of features remain outside this run.
