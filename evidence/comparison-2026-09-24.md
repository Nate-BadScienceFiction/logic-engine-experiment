# Implementation comparison

> **Superseded scoring.** A [fresh rerun with corrected timeout and refusal scoring](comparison-revised-2026-09-25.md) gives old 11 pass / 10 fail and rewrite 16 pass / 3 fail / 2 unknown. The original report below is retained unchanged apart from these editorial notes.

> **Note (September 25, 2026).** This is the raw harness report, kept as the record. Its speed paragraph attributes the earlier engine's apparent ~3,500× advantage to the defect in its cross-query answer cache. That does not hold: the speed came from the cache itself, which would stay fast with the defect fixed. Timings for both engines are in [the evidence overview](README.md).

Git revisions: old `e62758c23f66b26fa92c6d2dafaaf6bf3466499f`, new `9be7804c933cc8a3c51af3d8a5e4f54b012c8be6`

SWI-Prolog oracle: `C:\Program Files\swipl\bin\swipl.exe` (SWI-Prolog version 10.0.2 for x64-win64)

Scheduled cases: **21**
Third-party oracle coverage: **57.1%** (fully ISO or SWI-Prolog; the rest include human adjudications)

## How to read this

* **The corpus is not a random sample.** It was authored with knowledge of
  both engines, so the pass percentages measure *this corpus*, not the
  engines in general. Cases were deliberately added for capabilities the
  NEW engine lacks, to keep the selection from favouring the rewrite; the
  `old pass new fail` cell is where those land.
* **No oracle is taken from either engine's own documents.** The corpus
  loader refuses that by name. Each case cites ISO, a SWI-Prolog
  transcript, or a recorded human adjudication.
* **There is no single winner score, deliberately.** Read the paired table.
* **Capability cases are weaker evidence than answer cases**: they show a
  predicate answers something, not that the answer is right. Each carries a
  negative control, so a predicate that answers *everything* fails.
* **No timing is reported.** A warm repeated-query benchmark on these two
  engines makes the old one look ~3,500x faster; that number is its
  cross-query answer cache handing the caller its own internal list, and
  appending to a returned result makes a later query answer with a fact the
  program does not entail. A speedup from a defect is worse than no number.

## Per engine

| metric | old | new |
|---|---:|---:|
| pass | 10 | 18 |
| fail | 11 | 3 |
| unknown | 0 | 0 |
| contract pass % | 47.6 | 85.7 |
| assessed % | 100.0 | 100.0 |
| **unsound completeness claims** | 2 | 0 |
| unobservable bindings | 0 | 0 |

## Paired outcomes

| cell | cases |
|---|---:|
| both pass | 9 |
| both fail | 2 |
| old pass new fail | 1 |
| old fail new pass | 9 |
| unknown pairs | 0 |

## Every non-pass, with its reason

* `builtins.arithmetic-integer-division-on-negatives` [old]: raised while loading: ValueError: Failed to parse clauses: 1:36: Expected DOT, got IDENT
* `builtins.sort-deduplicates-msort-does-not` [old]: expected [{M=[a, b, b], S=[a, b]}], observed []
* `builtins.univ-decomposes-a-compound` [old]: raised while loading: ValueError: Failed to parse clauses: 1:18: Expected term, got DOT
* `syntax.operator-precedence-in-a-comparison` [old]: expected [{X=3}], observed []
* `value-fidelity.an-integer-a-float-and-an-atom-are-three-facts` [old]: expected [{X=1}, {X='1'}, {X=1.0}], observed [{X=1}]
* `recursion.an-infinite-answer-set-must-not-be-called-complete` [old]: returned 2 answers and reported no status at all for an infinite answer set
* `errors.an-open-generator-must-not-read-as-false` [old]: returned 0 answers and reported no status at all for an infinite answer set
* `mutation.a-returned-answer-list-is-the-callers-to-keep` [old]: a caller-inserted marker appeared in a later answer list
* `errors.arithmetic-on-a-non-number-is-an-error` [old]: answered 0 rows for a goal that is malformed; an empty answer set reads as 'false', which it is not
* `capability.rule-level-explanation-of-a-derived-fact` [new]: probe answered nothing; the capability is absent
* `capability.why-a-fact-holds` [old]: negative control control answered 1 rows; a capability that answers everything is not evidence of anything
* `capability.why-a-fact-holds` [new]: probe answered nothing; the capability is absent
* `capability.evidence-chain-for-a-derived-fact` [old]: negative control control answered 1 rows; a capability that answers everything is not evidence of anything
* `capability.evidence-chain-for-a-derived-fact` [new]: probe answered nothing; the capability is absent

## Oracle notes

* `mutation.a-returned-answer-list-is-the-callers-to-keep`: SWI supplies the row expectation; the returned-list isolation check is an independent host API judgment. This mixed case is excluded from third-party oracle coverage.
