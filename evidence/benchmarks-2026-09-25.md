# Speed against SWI-Prolog

> **Historical methodology, superseded.** The SWI side collected constant placeholders while Python materialized full bindings. Use the [revised full-binding measurements](benchmarks-revised-2026-09-25.md) for current comparisons. The timings and interpretation below are retained as the original report; their causal explanation was not established by profiling.

Measured September 25, 2026 · [raw timings](benchmarks-2026-09-25.json) · [original script](https://github.com/Nate-BadScienceFiction/logic-engine-experiment/blob/771be87/evidence/benchmark-vs-swi.py)

This page backed the original speed claims, before the revised methodology. It times two classic Prolog benchmarks, plus one list case that shows the cost of automatic tabling. They ran on the September 2026 rewrite (commit `9be7804`, Python 3.12.10) and on SWI-Prolog version 10.0.2, on one Windows 11 machine with an Intel processor.

## Results

Median time per run, in milliseconds. "Defaults" means automatic tabling of recursive predicates is on, as it is unless you turn it off.

| Program | Answers | This engine, defaults | This engine, `auto_table=False` | SWI-Prolog | Slower than SWI by |
|---|---:|---:|---:|---:|---:|
| Naive reverse of a 30-element list | 1 | 104.0 | 9.0 | 0.0074 | 1,206× to 14,002× |
| All solutions of 6-queens | 4 | 485.0 | 197.9 | 0.53 | 372× to 912× |
| All ways to split a 100-item list with app/3 | 101 | 3,829.5 | 30.4 | 0.0073 | 4,180× to 527,154× |

On the two classic benchmarks, naive reverse and 6-queens, the engine is 372 to 14,002 times slower than SWI-Prolog, depending on settings.

## Reading the numbers

- **Most of the gap is the interpreter.** This is a Python interpreter, and SWI-Prolog compiles to a fast virtual machine. Later work should narrow the gap, but a Python interpreter won't match SWI.
- **Automatic tabling is the other big cost.** It makes naive reverse about 12× slower, and splitting a list about 126× slower, because a tabled predicate is evaluated to a complete set of answers, by repeated passes, before any come back. Tabling only the predicates that need it, and evaluating tables incrementally, are the obvious places to gain.
- **Speed hasn't been the priority yet.** The [first rewrite prompt](../docs/prompts/1-design-brief-2026-09-13.md#8-verify-semantics-and-architecture) asked the agents to "measure representative performance after correctness is established" and not to "distort the architecture around speculative optimization."
- **Story-sized models are small.** On the 748-fact story model in the README, loading takes about 20 ms and the example queries take 1–16 ms (from the audit; [ENGINE.md](../docs/ENGINE.md#performance)).
- **This isn't a general benchmark.** It covers one machine and three small programs, timed warm.

## How it was measured

- Each engine loads a program once and answers the same query. Before timing, the script checks that the engine returns the expected number of answers.
- After two warm-up passes, it times five batches of repeated runs:

  | | Naive reverse | 6-queens | List split |
  |---|---:|---:|---:|
  | This engine, defaults | 10 runs | 3 runs | 1 run |
  | This engine, `auto_table=False` | 50 runs | 5 runs | 20 runs |
  | SWI-Prolog | 20,000 runs | 1,000 runs | 5,000 runs |

- The figure reported is the median of the five batch averages. Batches differed by at most 15%.
- Times are wall-clock. The engine is timed with Python's `perf_counter`; SWI-Prolog with `get_time/1` around a failure-driven loop of `findall/3`, whose small overhead is included.

## The programs

```prolog
% Naive reverse; the query reverses the list 1..30.
app([], L, L).
app([H|T], L, [H|R]) :- app(T, L, R).
nrev([], []).
nrev([H|T], R) :- nrev(T, RT), app(RT, [H], R).
% ?- nrev([1,2,...,30], R).       1 answer
% ?- app(X, Y, [1,2,...,100]).    101 answers: every way to split the list
```

```prolog
% All solutions of 6-queens, by permutation and check.
sel(X, [X|T], T).
sel(X, [H|T], [H|R]) :- sel(X, T, R).
perm([], []).
perm(L, [H|T]) :- sel(H, L, R), perm(R, T).
safe([]).
safe([Q|Qs]) :- noattack(Q, Qs, 1), safe(Qs).
noattack(_, [], _).
noattack(Q, [Q1|Qs], D) :- Q =\= Q1 + D, Q =\= Q1 - D, D1 is D + 1, noattack(Q, Qs, D1).
queens(Ns, Qs) :- perm(Ns, Qs), safe(Qs).
% ?- queens([1,2,3,4,5,6], Qs).    4 answers
```

## Original rerun command

The current `benchmark-vs-swi.py` implements the revised method. To reproduce this historical method, use the original script linked above.

```
python evidence/benchmark-vs-swi.py <path to the AkiyaBlocks-CyclopsStorm checkout> --json timings.json
```

The engine's repository is private for now, so this can't be rerun from this repository alone. The script is here so the method can be checked.
