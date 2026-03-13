# KB Engine API and Design Document

**Last Updated:** 2026-03-13
**Status:** Beta

---

## Table of Contents

1. [Overview](#overview)
2. [Cyclops Storm vs Standard Prolog](#cyclops-storm-vs-standard-prolog)
3. [Architecture](#architecture)
4. [Query Flow](#query-flow)
5. [The Two-Part Reasoning System](#the-two-part-reasoning-system)
6. [Strategy-Based Evaluation](#strategy-based-evaluation)
7. [Negation-as-Failure (NAF)](#negation-as-failure-naf)
8. [Event Calculus](#event-calculus)
9. [Tabling](#tabling)
10. [Provenance (Deep Dive)](#provenance)
11. [Core Components](#core-components)
12. [Data Model](#data-model)
13. [Glossary](#glossary)

---

## Overview

The KB Engine is a hybrid logic programming and temporal reasoning system. It combines Prolog-style unification and backtracking with Event Calculus for fluent reasoning over time. The system supports negation-as-failure, SLG-style tabling for recursive queries, and a full provenance system that traces conclusions back through rule derivation chains and temporal reasoning to source text — a capability absent from standard Prolog implementations.

---

## Cyclops Storm vs Standard Prolog

Cyclops Storm is **not** a general-purpose Prolog implementation. It is a domain-specific reasoning engine that borrows Prolog's core (unification, backtracking, Horn clauses) and extends it with temporal reasoning.

| Category | Cyclops Storm adds | Standard Prolog has, Cyclops Storm lacks |
|---|---|---|
| **Temporal reasoning** | Event Calculus built-ins (`holds_at`, `initiates`, `terminates`, `happens`, `before`, `initially`) | — |
| **Provenance** (no Prolog equivalent) | Source text attribution (`fact_id/2`, `supports/2`, `span/4`, `sent/2`), rule derivation tracing (`derivation/1`), unified explanation (`why/1`), recursive evidence trees (`evidence_chain/1`), canonical key normalization | — |
| **Architecture** | Dual-engine routing (DFS/Legacy), epoch caching | — |
| **Tabling** | SLG-style via `:- table` directive | (Some Prologs have tabling; not ISO) |
| **Builtins (partial)** | `findall/3`, `between/3`, `atom_concat/3`, `atom_number/2`, `sort/2`, `length/2`, `last/2`, `keysort/2`, `forall/2` | — |
| **Control & meta** | — | `bagof/3`, `setof/3`, `call/1-N`, `assert/retract` |
| **Type & term inspection** | `var/1`, `atom/1` (DFS engine) | `functor/3`, `arg/3`, `=../2`, `copy_term/2` |
| **I/O & modules** | — | `write/1`, `read/1`, module system |
| **Syntax & misc** | — | `op/3`, DCG (`-->/2`), exception handling (`catch/throw`), bitwise ops |

---

## Architecture

```
KBEngine (Facade)
│
├── Query Pipeline (7 stages)
│   CacheLookup → Validation → Parsing → Routing → Execution → Projection → Metrics
│
├── Parsing Layer
│   KBTokenizer → KBParser → core.Term → kb_model.Term conversion
│
├── Storage Layer
│   IndexedFactStore → FactStore (predicate index, temporal index, provenance index)
│
├── Handler Registry
│   ├── Temporal: HoldsAtHandler, InitiatesHandler, TerminatesHandler,
│   │            HappensHandler, BeforeHandler, TimeHandler, EventHandler,
│   │            ActionHandler, InitiallyHandler
│   ├── Provenance: DerivationHandler, WhyHandler, EvidenceChainHandler,
│   │              FactIdHandler, SupportsHandler
│   ├── Control: NegationHandler, DisjunctionHandler, ConjunctionHandler,
│   │           ForallHandler
│   ├── Builtins: BuiltinHandler (findall, sort, length, etc.)
│   ├── Comparison: ComparisonHandler (is, =, <, >, etc.)
│   └── Default: GeneralPredicateHandler
│
├── PredicateEvaluator ─ Unified fact+rule evaluation (delegates to Reasoner)
│
├── Reasoner (Inference Coordinator)
│   ├── DFS Engine ─── pure logic, cut, fast backtracking
│   ├── Legacy Engine ─ temporal reasoning, tabling, complex control flow
│   ├── Routing
│   │   ├── RoutingFSM + QueryAnalyzer (DFS vs Legacy selection)
│   │   ├── EngineRouter (dispatch)
│   │   └── FrameManager (mid-rule engine lock)
│   ├── SequenceEvaluationCoordinator (generator-based strategy dispatch)
│   │   ├── CutSequenceStrategy
│   │   ├── DisjunctionSequenceStrategy
│   │   ├── NAFSequenceStrategy ←── canonical NAF evaluator
│   │   ├── IfThenElseSequenceStrategy
│   │   └── LiteralSequenceStrategy
│   ├── Tabling (SLG-style)
│   │   TablingCoordinator → TableManager → FixpointDriver → VariantKey
│   └── Temporal Components
│       ├── FluentEvaluator (holds_at)
│       ├── PersistenceEvaluator (clipping checks)
│       ├── ExclusivityHandler (mutual exclusion)
│       ├── EventCalculusCore (EC operations)
│       └── EventCalculusQueries (initiation/termination queries)
│
└── Caching
    EpochCacheManager (memo, query, holds, reasoner_holds, reasoner_derived, tabling)
```

---

## Query Flow

A query passes through seven pipeline stages in `QueryExecutionPipeline`:

```
engine.query("holds_at(alarm, t2)")
        │
        ▼
┌─ 1. CacheLookup ──────────── check query cache; short-circuit on hit
│
├─ 2. Validation ────────────── syntax and semantic checks
│
├─ 3. Parsing ───────────────── tokenize → parse → core.Term → kb_model.Term
│                                extract query variables for projection
│
├─ 4. Routing ───────────────── select handler (holds_at → HoldsAtHandler,
│                                general predicate → GeneralPredicateHandler,
│                                negation → NegationHandler, etc.)
│
├─ 5. Execution ─────────────── handler dispatches to Reasoner
│                                → engine routing (DFS vs Legacy)
│                                → unification, rule evaluation, backtracking
│
├─ 6. Projection ────────────── project results to query variables only
│                                deduplicate, clean variable references
│
└─ 7. Metrics ───────────────── record execution time, result count, cache stats
        │
        ▼
   List[Dict[str, Any]]  (variable bindings)
```

**Fact Addition Flow:**
```
engine.add("parent(alice, bob).")
    → parse clause
    → classify (fact / rule / temporal)
    → store in IndexedFactStore
    → compile rules via RuleCompiler
    → invalidate caches (clear_all via EpochCacheManager)
```

---

## The Two-Part Reasoning System

The Reasoner routes each query to one of two engines: **DFS** (depth-first search) for pure logic, or **Legacy** for temporal reasoning and complex control flow.

### What Goes Where

| Query type | Engine | Example |
|---|---|---|
| Simple fact lookup (allowlisted) | DFS | `person(alice)`, `child(bob)` |
| Rule with cut (`!`) | DFS | `max(X, Y, X) :- X >= Y, !.` |
| `holds_at` / temporal predicates | Legacy | `holds_at(in_room(agent, kitchen), t3)` |
| Tabled recursive predicate | Legacy | `path(X, Y) :- edge(X, Z), path(Z, Y).` |
| NAF in complex context | Legacy | `flies(X) :- bird(X), \+penguin(X).` |
| Default (unknown predicate) | Legacy | Any predicate not explicitly routed to DFS |

**Key principle:** Legacy is the safe default. DFS is an optimization for predicates that are proven safe — pure logic with no temporal dependencies, no tabling, and no complex control flow.

### DFS Engine
- Bootstrapped backtracking search (`EngineBootstrapper`)
- Native cut support via goal stack pruning
- Uses `Goal` objects and `VariableRenamer`

### Legacy Engine
- Generator-based evaluation through `_evaluate_sequence_gen` and `_evaluate_literal_gen`
- Full Event Calculus integration
- SLG-style tabling via `TablingCoordinator`
- Handles complex control flow (forall, disjunctions)

### Frame Management
`FrameManager` prevents mid-rule engine switches. When a rule like `grandparent(X, Z) :- parent(X, Y), parent(Y, Z)` starts evaluating on one engine, the frame locks to that engine for the entire rule body.

---

## Strategy-Based Evaluation

The `SequenceEvaluationCoordinator` dispatches body items to specialized strategies during rule evaluation. Each strategy receives the current item, remaining items, substitution, and context, and yields substitutions lazily.

```python
# Dispatch order (first match wins):
CutSequenceStrategy          # Cut → commits choice point, raises CutCommit
DisjunctionSequenceStrategy  # OrNode → evaluates all branches
NAFSequenceStrategy          # Negation → canonical NAF evaluator
IfThenElseSequenceStrategy   # IfThenElse → commit semantics on condition
LiteralSequenceStrategy      # Literal → evaluate + continue with remaining
```

All NAF evaluation — regardless of entry point — converges on `NAFSequenceStrategy`, ensuring consistent semantics.

---

## Negation-as-Failure (NAF)

NAF implements closed-world negation: `\+Goal` succeeds when `Goal` has no solutions.

### Example: The Classic Default Reasoning Pattern

```prolog
bird(tweety).
bird(opus).
penguin(opus).
flies(X) :- bird(X), \+penguin(X).
```

```python
engine.query("flies(tweety)")  # → [{}]            tweety flies (bird, not penguin)
engine.query("flies(opus)")    # → []              opus doesn't fly (penguin)
engine.query("flies(X)")       # → [{'X': 'tweety'}]
```

### Safe Pattern: Ground Before Negating

NAF has undefined semantics when variables are unbound (the "floundering" problem). Ground your variables before the negation:

```prolog
% SAFE — X is bound by person(X) before NAF checks
eligible(X) :- person(X), \+excluded(X).

% UNSAFE — X is unbound when NAF fires
bad(X) :- \+excluded(X), person(X).
```

The engine detects floundering and fails safely when outer-scope variables remain unbound inside a NAF goal. Variables that appear *only* inside the NAF are existentially quantified and do not trigger floundering.

### NAF Evaluation Flow

```
NAFSequenceStrategy.evaluate_gen(negation, remaining, subst, context)
        │
        ▼
   1. FLOUNDERING CHECK
      Are outer-scope variables ground?
      │
      ├─ Unbound outer vars → fail (yield nothing)
      └─ All ground → continue
        │
        ▼
   2. APPLY SUBSTITUTION to inner goal
        │
        ▼
   3. CHECK INNER GOAL (short-circuits on first solution)
      │
      ├─ Inner has solution → NAF FAILS (yield nothing)
      └─ Inner has no solution → NAF SUCCEEDS
        │
        ▼
   4. CONTINUE with remaining body items
```

---

## Event Calculus

Temporal reasoning implements the Event Calculus axioms: events happen at times, events initiate and terminate fluents, and fluents persist by inertia until terminated.

### Predicates

| Predicate | Meaning |
|---|---|
| `initially(F)` | Fluent F holds at the initial time |
| `happens(E, T)` | Event E occurs at time T |
| `initiates(E, F)` | Event E starts fluent F |
| `terminates(E, F)` | Event E ends fluent F |
| `holds_at(F, T)` | Fluent F holds at time T |
| `before(T1, T2)` | T1 precedes T2 |

### Example: Location Tracking

A complete lifecycle — initial state, event, persistence, termination, re-query:

```prolog
% Time ordering
before(t1, t2). before(t2, t3). before(t3, t4). before(t4, t5). before(t5, t6).

% Agent starts in kitchen
initially(in_room(agent, kitchen)).

% Agent moves to living room at t2
happens(move(agent, living_room), t2).
initiates(move(agent, living_room), in_room(agent, living_room)).
terminates(move(agent, living_room), in_room(agent, kitchen)).

% Agent moves to bedroom at t5
happens(move(agent, bedroom), t5).
initiates(move(agent, bedroom), in_room(agent, bedroom)).
terminates(move(agent, bedroom), in_room(agent, living_room)).
```

```python
engine.query("holds_at(in_room(agent, kitchen), t1)")
# → [{}]  ✓ initially in kitchen

engine.query("holds_at(in_room(agent, living_room), t3)")
# → [{}]  ✓ move at t2 initiates living_room, persists to t3

engine.query("holds_at(in_room(agent, kitchen), t3)")
# → []    ✗ move at t2 terminated kitchen

engine.query("holds_at(in_room(agent, living_room), t4)")
# → [{}]  ✓ living_room persists by inertia (no terminating event between t2 and t4)

engine.query("holds_at(in_room(agent, bedroom), t6)")
# → [{}]  ✓ move at t5 initiates bedroom, persists to t6
```

The **frame problem** is solved by inertia: fluents unaffected by an event persist unchanged. If the agent also `initially(holding(agent, key))`, the key persists at all time points regardless of move events.

### holds_at Evaluation

```
holds_at(F, T)
    │
    ▼
 Check: initially(F) and no terminating event before T
    │                          │
    YES → TRUE                 NO
                               │
                               ▼
                          Find initiating events before T:
                          initiates(E, F), happens(E, T1), before(T1, T)
                               │
                               ▼
                          For each initiation, check persistence:
                          No terminating event between T1 and T?
                               │
                               ├─ Persists → TRUE
                               └─ Clipped  → try next initiation
```

**Key components:**
- `FluentEvaluator` — implements `holds_at` lookup, including provenance-aware variant
- `PersistenceEvaluator` — checks for clipping between initiation and query time
- `ExclusivityHandler` — mutual exclusion between competing fluents
- `EventCalculusCore` — core operations: `persists()`, `kills()`, `fluents_compete()`
- `EventCalculusQueries` — queries for initiations/terminations at or before a time

---

## Tabling

SLG-style tabling memoizes recursive query results and detects cycles, preventing infinite loops on recursive predicates.

### Example: Transitive Closure

Without tabling, a cyclic graph causes infinite recursion:

```prolog
edge(a, b). edge(b, c). edge(c, a).   % cycle: a → b → c → a

:- table path/2.
path(X, Y) :- edge(X, Y).
path(X, Y) :- edge(X, Z), path(Z, Y).
```

```python
engine.query("path(a, X)")
# → [{'X': 'b'}, {'X': 'c'}, {'X': 'a'}]  — terminates despite cycle
```

Without `:- table path/2`, the query `path(a, X)` would loop forever: `path(a,X) → edge(a,b), path(b,X) → edge(b,c), path(c,X) → edge(c,a), path(a,X) → …`

### How It Works

1. **First call** to a tabled variant becomes the **producer** — it evaluates the goal and accumulates answers in a table
2. **Recursive calls** to the same variant become **consumers** — they read from the table instead of re-evaluating, breaking the cycle
3. **Fixpoint iteration** re-evaluates until no new answers appear, guaranteeing completeness
4. **Variant keys** normalize variable names (`path(X,Y)` and `path(A,B)` map to the same table entry)

Components: `TablingCoordinator` manages the protocol, `TableManager` stores producer/consumer tables, `FixpointDriver` iterates to fixpoint, `VariantKey` normalizes queries for cache lookup.

---

## Builtin Examples

### Batch Fact Addition

`add_facts()` adds multiple facts with a single cache invalidation (not one per fact). Internally calls `cache_manager.clear_all()` once after all facts are stored:

```python
engine.add_facts(["person(alice)", "person(bob)", "friend(alice, bob)"])
# cache cleared once after all facts loaded
```

`add_rules()` works similarly for rules:

```python
engine.add_rules([
    "ancestor(X, Y) :- parent(X, Y)",
    "ancestor(X, Z) :- parent(X, Y), ancestor(Y, Z)"
])
```

### findall/3

Collect all solutions for a goal into a list:

```python
engine.add("color(apple, red). color(banana, yellow). color(cherry, red).")
engine.query("findall(X, color(X, red), L)")
# → [{'L': Term('[]', ('apple', 'cherry'))}]
```

Note: list results use the internal `Term('[]', (...))` representation.

### Arithmetic and Comparison

```python
engine.query("X is 3 + 4 * 2")       # → [{'X': 11.0}]
engine.query("between(1, 5, X)")      # → [{'X': 1}, {'X': 2}, ..., {'X': 5}]
engine.query("sort([3,1,2,1], X)")    # → [{'X': Term('[]', (1, 2, 3))}]
engine.query("length([a,b,c], N)")    # → [{'N': 3}]
```

### Snapshot and Restore

Save and restore KB state for speculative reasoning:

```python
snap = engine.snapshot()
engine.add("temporary_fact(x).")
engine.query("temporary_fact(x)")  # → [{}]
engine.restore(snap)
engine.query("temporary_fact(x)")  # → []
```

---

## Provenance

### Why This Matters — What SWI-Prolog Doesn't Have

Standard Prolog implementations, including SWI-Prolog, are opaque reasoners. They tell you *what* is true but not *why*, *how*, or *where the evidence comes from*. There is no built-in mechanism to:

- Trace a derived fact back through the rule chain that produced it
- Link a fact to the source text (document, sentence, character span) it was extracted from
- Explain temporal reasoning — why a fluent holds at a particular time through initiation, persistence, and non-termination
- Build recursive evidence trees from a conclusion down to its leaf evidence

SWI-Prolog's `prolog_stack/1` shows the call stack during execution, and libraries like `pengines` can trace resolution steps, but neither produces a structured provenance record that connects conclusions to source evidence. The Cyclops Storm provenance system fills this gap at three levels.

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────┐
│  Layer 3: Query Handlers                            │
│  derivation/1, why/1, evidence_chain/1              │
│  fact_id/2, supports/2                              │
│  (engine/query/provenance_handlers.py)              │
│  (engine/query/query_handlers.py)                   │
├─────────────────────────────────────────────────────┤
│  Layer 2: Provenance Collection (on-demand)         │
│  DerivationRecord in rule evaluation template       │
│  TemporalProvenanceNode in fluent evaluator         │
│  explain_holds_at_structured in explainer           │
│  (engine/derived_evaluation/template.py)            │
│  (engine/reasoning/temporal/fluent_evaluator.py)    │
│  (engine/debugging/explanation.py)                  │
├─────────────────────────────────────────────────────┤
│  Layer 1: Storage & Indexing                        │
│  FactStore: fact_ids, supports, source_by_term,     │
│             by_term (canonical index)               │
│  canonical_key() normalization                      │
│  spans_for_term() multi-path lookup                 │
│  (kb_store.py, engine/indexing/canonical.py)        │
└─────────────────────────────────────────────────────┘
```

**Layer 1** is populated at load time when `.pl` files contain `fact_id/2`, `supports/2`, and `source/2` facts. **Layer 2** is activated on demand — the `provenance_collector` field on `EvaluationContext` defaults to `None`, and recording is gated behind a `None` check, so normal queries have zero provenance overhead. **Layer 3** is the user-facing API: query handlers registered in the handler registry.

### Query Handlers

| Handler | Query | Returns |
|---|---|---|
| `derivation/1` | `derivation(ancestor(tom, bob))` | Which rules fired, bindings used, supporting facts |
| `why/1` | `why(holds_at(light_on, t2))` | Unified explanation — auto-detects base/derived/temporal |
| `evidence_chain/1` | `evidence_chain(ancestor(tom, bob))` | Recursive evidence tree from conclusion to source text |
| `fact_id/2` | `fact_id(initiates(e1, f), F)` | Maps facts to stable provenance IDs |
| `supports/2` | `supports(S, f_trust)` | Links text spans to provenance IDs |

### Example: Source Text Attribution

Link domain facts to their origin in natural language text:

```prolog
% Domain fact
initiates(rescue, trust_level(alice, bob, high)).

% Provenance metadata
fact_id(initiates(rescue, trust_level(alice, bob, high)), f_rescue).
supports(span_42, f_rescue).
span(span_42, doc_chapter3, 100, 145).
sent(span_42, 'Alice risked her life to save Bob.').
```

```python
# Step 1: Find the fact's provenance ID
engine.query("fact_id(initiates(rescue, trust_level(alice, bob, high)), F)")
# → [{'F': 'f_rescue'}]

# Step 2: Find supporting text spans
engine.query("supports(S, f_rescue)")
# → [{'S': 'span_42'}]

# Step 3: Get span position and sentence text
engine.query("span(span_42, Doc, Start, End)")
# → [{'Doc': 'doc_chapter3', 'Start': 100, 'End': 145}]

# All at once with a compound query:
engine.query(
    "fact_id(initiates(rescue, trust_level(alice, bob, high)), F), supports(S, F)"
)
# → [{'F': 'f_rescue', 'S': 'span_42'}]
```

### Example: Asking "Why Does This Hold?"

The `why/1` handler auto-detects fact type and returns structured explanations.

**Base fact** — directly asserted, not derived from rules:

```python
engine.add("parent(tom, bob).")
engine.query("why(parent(tom, bob))")
# → [{'term': 'parent(tom,bob)', 'type': 'base',
#      'explanation': [{'reason': 'base_fact',
#                       'detail': 'parent(tom,bob) is a base fact in the KB'}],
#      'source_spans': []}]
```

**Derived fact** — produced by rule evaluation:

```python
engine.add("parent(tom, bob).")
engine.add("ancestor(X, Y) :- parent(X, Y).")

engine.query("why(ancestor(tom, bob))")
# → [{'term': 'ancestor(tom,bob)', 'type': 'derived',
#      'explanation': [{'reason': 'rule_derivation',
#                       'rule_id': ('ancestor', 2, 0),
#                       'rule_text': 'ancestor(X,Y) :- parent(X,Y).',
#                       'bindings': {'X$1': 'tom', 'Y$2': 'bob'},
#                       'supporting_facts': [...]}],
#      'source_spans': []}]
```

**Temporal fact** — produced by Event Calculus reasoning:

```python
engine.add("time(t0). time(t1). time(t2).")
engine.add("before(t0, t1). before(t1, t2).")
engine.add("event(switch_on).")
engine.add("happens(switch_on, t1).")
engine.add("initiates(switch_on, light_on).")

engine.query("why(holds_at(light_on, t2))")
# → [{'term': 'holds_at(light_on,t2)', 'type': 'temporal',
#      'explanation': [{'reason': 'initiated_by',
#                       'detail': 'switch_on initiates light_on at t1',
#                       'initiating_event': 'switch_on',
#                       'initiation_time': 't1',
#                       'supporting_facts': ['happens(switch_on, t1)',
#                                            'initiates(switch_on, light_on)']}],
#      'source_spans': []}]
```

The temporal explanation traces the full Event Calculus chain: `switch_on` happened at `t1`, it initiates `light_on`, and nothing terminated it before `t2`. The `supporting_facts` field lists the `happens/2` and `initiates/2` facts that make up the causal chain. If provenance metadata was loaded for those supporting facts, the `source_spans` field connects back to source text.

### Example: Evidence Chains

The `evidence_chain/1` handler builds a recursive tree from a conclusion down to leaf evidence. Each node has a `type` and `children`. Base facts are leaves; rule applications and temporal reasoning steps are internal nodes.

```python
engine.add("parent(tom, bob).")
engine.add("ancestor(X, Y) :- parent(X, Y).")

engine.query("evidence_chain(ancestor(tom, bob))")
# → [{'term': 'ancestor(tom,bob)', 'type': 'derived',
#      'source_spans': [],
#      'children': [{'type': 'rule_application',
#                    'rule_id': ('ancestor', 2, 0),
#                    'rule_text': 'ancestor(X,Y) :- parent(X,Y).',
#                    'bindings': {...},
#                    'children': [{'term': 'parent(tom,bob)',
#                                  'type': 'base_fact', ...}]}]}]
```

For temporal facts, the chain traces back to `happens/2` and `initiates/2` base facts:

```python
engine.query("evidence_chain(holds_at(light_on, t2))")
# → [{'term': 'holds_at(light_on,t2)', 'type': 'temporal',
#      'children': [{'term': 'happens(switch_on,t1)', 'type': 'base_fact', ...},
#                   {'term': 'initiates(switch_on,light_on)', 'type': 'base_fact', ...}]}]
```

The chain has a depth limit of 10 and cycle detection to prevent infinite loops on recursive rules.

### Data Flow

**At load time** (`.pl` files parsed by `FactProcessor`):

```
fact_id(term, id)   →  store.fact_ids[id] = term
                       store.by_term[canonical_key(term)].add(id)

supports(span, id)  →  store.supports[span].add(id)

source(term, span)  →  store.source_by_term[canonical_key(term)].add(span)
```

**At query time** (`spans_for_term` lookup):

```
query term
  ├─→ canonical_key(term) → by_term → fact_ids
  │     └─→ for each fact_id → supports → span_ids
  └─→ canonical_key(term) → source_by_term → span_ids (fallback)
  └─→ merge all span_ids into result set
```

**On-demand provenance** (lazy, only when provenance handlers are invoked):

```
derivation(term)
  └─→ re-evaluate term with provenance_collector=[]
      └─→ template.py rule loop records DerivationRecord for each match
      └─→ return collected records as dicts

why(term)
  ├─→ classify: temporal (holds_at/2)? base? derived?
  ├─→ dispatch to appropriate explanation builder
  ├─→ enrich explanation nodes with spans_for_term
  └─→ return structured result

evidence_chain(term)
  └─→ recursive _build_chain:
      ├─→ base fact? → leaf node
      ├─→ temporal? → trace initiations/initially
      └─→ derived? → re-evaluate, recurse into supporting facts
```

### Canonical Key Normalization

`canonical_key()` normalizes surface-form variations so provenance lookups are robust to how a term was written. This is critical for real-world KBs where facts are loaded from different sources with inconsistent formatting.

| Variation | Example | Canonical Key |
|-----------|---------|---------------|
| Case | `LIKES(Alice)` vs `likes(alice)` | Same |
| Quotes | `'alice'` vs `alice` | Same |
| Numeric | `42.0` vs `42` | Same |
| Variable aliasing | `p(X, X)` vs `p(X, Y)` | **Different** (correctly) |
| Commutative | `equals(a, b)` vs `equals(b, a)` | Same (configurable via `COMMUTATIVE_PREDS` in `kb_config.py`) |

### Key Components

| Component | File | Role |
|---|---|---|
| `DerivationHandler` | `engine/query/provenance_handlers.py` | Rule derivation tracing |
| `WhyHandler` | `engine/query/provenance_handlers.py` | Unified fact explanation |
| `EvidenceChainHandler` | `engine/query/provenance_handlers.py` | Recursive evidence trees |
| `FactIdHandler` | `engine/query/query_handlers.py` | Fact ID queries (O(1) canonical lookup) |
| `SupportsHandler` | `engine/query/query_handlers.py` | Span-to-fact support queries |
| `DerivationRecord` | `engine/derived_evaluation/data_structures.py` | Derivation step data |
| `TemporalProvenanceNode` | `engine/reasoning/temporal/temporal_provenance.py` | Temporal reasoning chain data |
| `canonical_key()` | `engine/indexing/canonical.py` | Surface-form normalization |
| `spans_for_term()` | `kb_store.py` | Multi-path source span lookup |

### Design Edges

All provenance handlers require ground terms — `why(X)` returns `[]`. Wrong arity silently returns `[]`. Unknown facts fall through to `type: 'derived'` with `reason: 'no_derivation_found'`. Facts added via `engine.add()` at runtime have no automatic provenance unless you also add `fact_id/2` and `supports/2` metadata. The `source_spans` field in `why/1` results depends on loaded provenance metadata — the explanation itself works without it.

For the complete edge case catalog, see `kb_provenance_system.md`.

---

## Core Components

### KBEngine — `kb_engine.py`

Facade. Owns the query pipeline, fact manager, parsing engine, handler registry, and cache manager.

```python
engine = KBEngine()
engine.add("parent(alice, bob).")
engine.add("ancestor(X, Y) :- parent(X, Y).")
engine.add("ancestor(X, Z) :- parent(X, Y), ancestor(Y, Z).")
results = engine.query("ancestor(alice, X)")
# → [{'X': 'bob'}]
```

**Public API:** `query()`, `add()`, `add_fact()`, `add_facts()`, `add_rule()`, `add_rules()`, `consult()`, `snapshot()`, `restore()`, `clear_cache()`, `explain_holds_at()`, `timeline()`, `enable_validation()`, `set_validation_level()`, `get_validation_stats()`, `enable_semantic_analysis()`, `run_semantic_analysis()`, `get_semantic_report()`, `rebuild_temporal_indexes()`

### Reasoner — `kb_reasoner.py`

Inference coordinator. Owns both engines, all temporal components, evaluation strategies, tabling, and routing.

**Public API:** `holds_at()`, `evaluate_derived()`, `clear_cache()`, `resolve_fully()`. (`evaluate_body_with_disjunctions()` exists but has no callers — the evaluation pipeline uses `_evaluate_sequence_gen()` instead.)

### FactStore — `kb_store.py`

Indexed storage for facts, rules, temporal relations, and provenance. Maintains predicate indexes (facts by functor, rules by head functor), temporal indexes (events by time, initiations by time and functor), and provenance indexes (fact IDs by canonical key, support chains, source-to-span mappings). An `IndexedFactStore` variant in `engine/indexed_store.py` provides additional indexing capabilities.

### Parser — `kb_parser.py`

Tokenizes and parses Prolog syntax into `core.Term` AST nodes. Supports: atoms, variables, numbers (including scientific notation), strings, compound terms, lists, operators, arithmetic, cut, negation, disjunction, if-then-else.

`KBEngine` converts `core.Term` (has `.type`, `.value`) to `kb_model.Term` (has `.functor`, `.args`) via `_convert_core_term_to_model()`.

### Unifier — `kb_unify.py`

Pattern matching with variable binding. `unify(pattern, ground, subst)` returns a substitution or `None`. Supports occurs check, list unification, anonymous variables (`_`), substitution composition, and chain walking. Internal helpers `_get_functor()` and `_get_args()` handle cross-type unification between `kb_model.Term` (`.functor`, `.args`) and `core.Term` (`.value`, `.args`).

### RuleCompiler — `engine/compilation/rule_compiler.py`

Transforms rules into executable form. Extracts variables, builds dependency graphs, optimizes evaluation order, identifies tabling candidates. Integrates with `StratificationAnalyzer` to detect non-stratifiable programs (odd loops through negation) at compile time.

### Caching — `engine/caching/`

`EpochCacheManager` maintains six cache levels: memo, query, holds, reasoner_holds, reasoner_derived, and tabling. Each `add()` call triggers `cache_manager.clear_all()`, eagerly invalidating all cached entries. Batch operations like `add_facts()` invalidate once after all facts are stored.

### Handler Registry — `engine/query/handler_setup.py`

Maps predicate functors to specialized handlers. Handlers are grouped by category:

| Category | Handlers | Predicates |
|---|---|---|
| Temporal | `HoldsAtHandler`, `InitiatesHandler`, `TerminatesHandler`, `HappensHandler`, `BeforeHandler`, `TimeHandler`, `EventHandler`, `ActionHandler`, `InitiallyHandler` | `holds_at`, `initiates`, `terminates`, `happens`, `before`, `time`, `event`, `action`, `initially` |
| Provenance | `DerivationHandler`, `WhyHandler`, `EvidenceChainHandler`, `FactIdHandler`, `SupportsHandler` | `derivation`, `why`, `evidence_chain`, `fact_id`, `supports` |
| Control | `NegationHandler`, `DisjunctionHandler`, `ConjunctionHandler`, `ForallHandler` | `\+`, `;`, `,`, `forall` |
| Builtins | `BuiltinHandler` | `findall`, `sort`, `length`, `last`, `keysort`, `atom_concat`, `atom_number`, `between` |
| Comparison | `ComparisonHandler` | `is`, `=`, `\=`, `<`, `>`, `=<`, `>=`, `==`, `\==`, `=:=`, `=\=` |
| Default | `GeneralPredicateHandler` | Any unmapped predicate |

---

## Data Model

Defined in `kb_model.py` (re-exports from `kb_core.model`):

| Type | Description | Example |
|---|---|---|
| `Term(functor, args)` | Compound term | `Term('parent', (Term('alice', ()), Term('bob', ())))` |
| `Var(name, uid)` | Logic variable (uid auto-generated) | `Var('X')` |
| `NumericAtom(value)` | Number (int or float) | `NumericAtom(42)` |
| `QuotedAtom(value)` | Quoted string | `QuotedAtom('hello')` |
| `Literal(term, neg)` | Term with negation flag | `Literal(term, neg=False)` |
| `Negation(inner)` | NAF wrapper | `Negation(Literal(term))` |
| `OrNode(branches)` | Disjunction (`A ; B`) | `OrNode(((lit_a,), (lit_b,)))` |
| `Conjunction(items)` | Conjunction (preserves structure for NAF) | `Conjunction((lit_a, lit_b))` |
| `Cut()` | Cut operator | `Cut()` |
| `IfThenElse(condition, then_branch, else_branch)` | Conditional | `IfThenElse(cond, (then_lits,), (else_lits,))` |
| `Clause(head, body)` | Inference rule (aliased as `Rule`) | `Clause(head_term, (body_lit1, body_lit2))` |
| `Directive(term)` | Prolog directive (`:- table fib/1`) | `Directive(Term('table', ...))` |

**Substitution:** `Dict[Union[str, Var], Any]` mapping variable names (strings) or `Var` objects to bound values. The `Unifier.clean_substitution()` method normalizes `Var` keys to string keys for external consumption.

---

## Quick Glossary of Key Terms

| Term | Definition |
|---|---|
| **Canonical Key** | Normalized term representation for provenance lookup (case, quote, numeric equivalence) |
| **Clipping** | Interruption of fluent persistence by a terminating event |
| **Cut** | Prolog `!` operator — commits to current choice, prunes backtracking |
| **DFS Engine** | Depth-first search backtracking engine for pure logic |
| **Epoch** | Generation marker for cache invalidation |
| **Evidence Chain** | Recursive tree from derived conclusion to source text leaves |
| **Floundering** | NAF attempted with unbound outer-scope variables (undefined semantics) |
| **Fluent** | Time-varying property managed by Event Calculus |
| **Frame** | Routing lock preventing mid-rule engine switches |
| **Legacy Engine** | Iterator-based engine with temporal reasoning and tabling |
| **NAF** | Negation-as-failure — succeeds if inner goal has no solutions |
| **Provenance** | Tracking the origin of facts — which source text, which rules, which events |
| **SLG** | Selective Linear Definite clause resolution (tabling algorithm) |
| **Stratification** | Layering predicates by negation dependencies |
| **Substitution** | Variable → value mapping produced by unification |
| **Tabling** | Memoization of recursive query results with fixpoint iteration |
| **Unification** | Pattern matching that produces variable bindings |
| **Variant Key** | Normalized query form for tabling cache lookup |

---

## Detailed Glossary

This section provides in-depth explanations of key concepts. If you are new to logic programming or Event Calculus, start here. For a side-by-side comparison with SWI-Prolog, see [KB_ARCHITECTURE_VS_SWI_PROLOG.md](KB_ARCHITECTURE_VS_SWI_PROLOG.md).

### Unification

**Unification** is the core pattern-matching operation underlying all Prolog-style reasoning. Given two terms, unification finds a substitution (a mapping from variables to values) that makes the terms identical, or reports failure if no such mapping exists.

```prolog
?- f(X, b) = f(a, Y).    % X = a, Y = b
?- f(X, X) = f(a, b).    % FAILS — X can't be both a and b
?- f(X, Y) = f(Y, a).    % X = a, Y = a (chains: X→Y→a)
```

Cyclops Storm uses **immutable substitution dictionaries** — each binding creates a new dict rather than mutating in place. This prevents aliasing bugs (where two variables accidentally share the same binding) at the cost of more memory. The **occurs check** is always on, preventing circular terms like `X = f(X)` which would cause infinite loops. Standard Prolog leaves occurs check off by default for speed.

### Backtracking

**Backtracking** is Prolog's mechanism for exploring multiple solutions. When a query has multiple possible matches, the engine tries the first, and if it fails (or the user asks for more solutions), it undoes recent bindings and tries the next alternative.

```prolog
color(apple, red).
color(banana, yellow).
color(cherry, red).

?- color(X, red).
% First solution: X = apple
% Backtrack → second solution: X = cherry
% Backtrack → no more solutions
```

Cyclops Storm implements backtracking with Python generators — each choice point `yield`s a solution, and the caller can request more by advancing the generator. The DFS engine uses an explicit choice point stack; the Legacy engine uses recursive generators.

### DFS Engine

The **Depth-First Search Engine** is Cyclops Storm's faster query evaluator for pure Prolog queries. It implements classical Prolog's left-to-right, depth-first search strategy using an explicit choice point stack rather than the recursive evaluation used by the Legacy engine. The DFS engine traverses the search space by exploring each branch fully before backtracking to try alternatives, yielding solutions incrementally via Python generators. It handles unification, backtracking, disjunction (`A ; B`), cut (`!`), and limited negation-as-failure, but lacks support for Event Calculus predicates and temporal reasoning. Cut is implemented as a builtin that succeeds and commits to the current clause. Queries are routed to the DFS engine when they contain only "pure" predicates (no EC, no unsafe NAF), providing significant performance improvement over the Legacy engine for applicable queries.

### DFS Allowlist

The **DFS Allowlist** is a configuration set that specifies which user-defined predicates are safe to evaluate using the faster DFS engine. By default, Cyclops Storm conservatively routes most queries to the Legacy engine to ensure correct semantics. The allowlist mechanism allows specific predicates (e.g., `person/1`, `child/2`) to be marked as "pure Prolog"—meaning they don't depend on Event Calculus reasoning, temporal state, or features the DFS engine doesn't support. When a query involves only allowlisted predicates and built-in pure predicates, the routing FSM directs it to the DFS engine. The allowlist is currently `{person, child}` only — `sibling` is excluded due to a known DFS compound-rule backtracking bug where the engine produces 0 results for rules with 3+ conjuncts (e.g., `sibling(X,Y) :- parent(Z,X), parent(Z,Y), different(X,Y)`).

### Legacy Engine

The **Legacy Engine** is Cyclops Storm's original query evaluator, handling Event Calculus predicates, temporal reasoning, tabling, and belief state management. Unlike the DFS engine (which uses an explicit choice point stack), the Legacy engine uses recursive evaluation with Python generators. All EC predicates (`happens`, `holds_at`, `initiates`, `terminates`, `initially`, `before`) are routed to the Legacy engine, as are queries involving tabling or cutoff time. The Legacy engine also handles cut via `CutSequenceStrategy` and `CutCommit` exceptions, though the routing tables preferentially send cut-containing queries to the DFS engine. The term "Legacy" reflects the architectural evolution—newer pure Prolog queries use the faster DFS engine, while the Legacy engine remains essential for EC semantics.

### EC (Event Calculus)

**Event Calculus** is a logical formalism for reasoning about events, actions, and their effects over time. Originally developed by Kowalski and Sergot (1986) for database applications, it provides a declarative framework for specifying how events initiate and terminate time-varying properties (fluents). The core EC predicates are:

| Predicate | Meaning | Example |
|---|---|---|
| `initially(F)` | Fluent F holds at the start | `initially(in_room(agent, kitchen))` |
| `happens(E, T)` | Event E occurs at time T | `happens(move(agent, hall), t2)` |
| `initiates(E, F)` | Event E starts fluent F | `initiates(move(agent, hall), in_room(agent, hall))` |
| `terminates(E, F)` | Event E ends fluent F | `terminates(move(agent, hall), in_room(agent, kitchen))` |
| `holds_at(F, T)` | Fluent F holds at time T | `holds_at(in_room(agent, hall), t3)` |
| `before(T1, T2)` | T1 precedes T2 | `before(t1, t2)` |

Cyclops Storm uses 2-arity `initiates/2` and `terminates/2` as the standard form; a legacy 3-arity form (`initiates(Event, Fluent, Time)`) is also accepted. EC elegantly solves the *frame problem*—determining what remains unchanged after an action—through an inertia axiom: fluents persist unless explicitly terminated. Cyclops Storm implements discrete EC with explicit time points, making it suitable for narrative reasoning where events occur at specific moments in a story timeline.

### Fluents

**Fluents** are time-varying properties in Event Calculus—predicates whose truth value can change over time as events occur. The term comes from "flowing" or "flux," reflecting that these properties are not static facts but dynamic states. For example, `in_room(agent, kitchen)` is a fluent representing the agent's location, which changes when movement events occur. Fluents contrast with *static predicates* like `color(apple, red)` that don't change over time.

In Cyclops Storm, fluents are the subjects of `holds_at/2` queries and the objects of `initiates/2` and `terminates/2` causal rules. The system tracks fluent lifecycles: when they were initiated, whether they've been terminated (clipped), and the complete provenance chain explaining why a fluent holds or doesn't hold at any given time point. Fluents can also be *exclusive*—only one value can hold at a time (e.g., an agent can only be in one room).

### Frame Problem and Inertia Axiom

The **Frame Problem** is a fundamental challenge in AI: how to efficiently represent what *doesn't* change when an action occurs. Naively, you'd need explicit "frame axioms" stating that every unchanged property persists after every action—an exponential blowup. If "opening a door" doesn't affect an agent's location, you'd need a frame axiom for every property that isn't affected. With 100 fluents and 50 actions, that's 5,000 frame axioms.

The **Inertia Axiom** is Event Calculus's elegant solution: a fluent that holds at time T continues to hold at later times unless an event terminates it. Formally: `holds_at(F, T) ∧ ¬clipped(T, F, T') → holds_at(F, T')` for T < T'. In Cyclops Storm, inertia is implemented implicitly in the `holds_at` algorithm: after finding an initiation time, the system searches for terminating events; if none exist before the query time, the fluent holds. This avoids the need for explicit persistence axioms and makes temporal reasoning tractable.

### NAF (Negation as Failure)

**Negation as Failure** is Prolog's approach to negation under the closed-world assumption: a goal `\+ P` succeeds if and only if `P` cannot be proven from the knowledge base. Unlike classical logical negation, NAF doesn't require explicit negative facts—absence of proof is treated as proof of absence.

```prolog
bird(tweety). penguin(opus). bird(opus).
flies(X) :- bird(X), \+ penguin(X).

?- flies(tweety).  % YES — tweety is a bird, not a penguin
?- flies(opus).    % NO  — opus is a penguin (NAF fails)
```

This makes NAF **non-monotonic**: adding `penguin(tweety).` would cause `flies(tweety)` to stop succeeding. In Cyclops Storm, NAF is implemented by attempting to prove the inner goal in an isolated subproof; if the subproof yields no solutions, the negation succeeds with the current substitution unchanged.

NAF has important limitations: it requires ground arguments (see *Floundering*), it doesn't work well with incomplete information, and it can interact subtly with other control constructs like cut and disjunction. The Legacy engine handles NAF more robustly than the DFS engine, which is why queries with potentially unsafe NAF are routed to Legacy.

### Flounder (Floundering)

**Floundering** occurs when negation-as-failure (NAF) is applied to a goal containing unbound variables. Since NAF uses the closed-world assumption ("if we can't prove P, then ¬P"), applying it to a non-ground goal like `\+ member(X, [1,2,3])` is semantically problematic: we cannot enumerate all possible values of X to check that none are members.

Cyclops Storm implements a conservative flounder policy: when NAF encounters a non-ground goal, it immediately triggers backtracking without binding any variables or raising an error. This means queries must be written to ground variables *before* negation:

```prolog
% SAFE — X is bound by person(X) before NAF checks
eligible(X) :- person(X), \+ excluded(X).

% UNSAFE — X is unbound when NAF fires → flounders
bad(X) :- \+ excluded(X), person(X).
```

### Selective Tabling

**Selective Tabling** is Cyclops Storm's approach to applying tabling only to predicates that need it, controlled via the standard Prolog `:- table` directive. Consider a knowledge base with both simple facts and recursive rules:

```prolog
:- table reaches/2.
person(alice).
person(bob).
edge(a, b).
edge(b, c).
reaches(X, Y) :- edge(X, Y).
reaches(X, Z) :- edge(X, Y), reaches(Y, Z).
```

Here, only `reaches/2` benefits from tabling—it's recursive and would otherwise recompute the same subgoals repeatedly. The simple `person/1` facts don't need tabling overhead (table creation, answer storage, fixpoint iteration). With selective tabling, querying `person(X)` bypasses the tabling machinery entirely, while `reaches(a, X)` uses full SLG resolution with memoization.

Cyclops Storm supports two modes. When `:- table` directives are present, only registered predicates use tabling; unregistered predicates evaluate directly without table creation. When no directives exist (blanket mode), all predicates use tabling for backward compatibility. Multiple predicates can be registered in a single directive (`:- table ancestor/2, path/2.`), and programmatic registration is available via `engine.reasoner.register_tabled_predicate("pred", arity)`.

### SLG Resolution

**SLG Resolution** (Selective Linear Definite clause resolution with Generalization) is the tabling algorithm that enables efficient evaluation of recursive queries by memoizing intermediate results. Without tabling, a query like computing the transitive closure of a graph can loop infinitely or recompute the same subgoals exponentially many times.

SLG resolution uses a **producer/consumer protocol**: the first call to a tabled predicate becomes a "producer" that computes answers, while subsequent calls with equivalent (variant) arguments become "consumers" that reuse cached answers. When a consumer encounters a call that's still being evaluated (a cycle), it suspends and waits for the producer to generate answers. Cyclops Storm uses fixpoint iteration to handle recursive definitions, continuing until no new answers are produced.

### Cutoff Time

**Cutoff Time** is Cyclops Storm's temporal pruning optimization that limits the horizon of Event Calculus queries. When evaluating `holds_at(Fluent, T)` with a cutoff, the system ignores events occurring after the cutoff time, reducing the search space for initiation and termination checks. This is particularly useful for interactive narrative systems where only recent history matters, or for debugging where you want to isolate behavior within a specific time window. Cutoff time is passed through the evaluation context and affects `holds_at`, `initiates`, `terminates`, and related EC predicates.

### Epoch

**Epoch** is Cyclops Storm's cache invalidation mechanism, implemented by the `EpochCacheManager`. Each mutation to the knowledge base (adding or removing facts) calls `clear_all()`, which physically clears all six cache dictionaries in place and bumps the epoch counter. This eager invalidation approach is simple and guarantees correctness (no stale results) at the cost of coarse granularity (all caches affected by any mutation). A lighter-weight `bump_epoch()` method exists for lazy invalidation (entries become stale but are not reclaimed until re-queried), though the engine currently uses `clear_all()` by default.

```python
engine.add("person(alice).")    # caches cleared, epoch bumped
engine.add("person(bob).")      # caches cleared again
# Batch alternative: engine.add_facts([...]) clears only once
```

### Provenance

**Provenance** is Cyclops Storm's mechanism for tracking *why* a conclusion holds, not just *that* it holds. The provenance system operates at three levels:

1. **Source attribution**: `fact_id/2` and `supports/2` link facts to source text spans
2. **Rule derivation**: `DerivationRecord` objects document which rules fired and what bindings were used
3. **Temporal reasoning**: `TemporalProvenanceNode` objects trace the Event Calculus chain — which events occurred, which rules fired, which preconditions were satisfied

This supports explainability ("Why does the agent have the key at t5?"), debugging ("Which event caused this unexpected state?"), and narrative generation ("Summarize the agent's actions").

### Stratification

**Stratification** is the layering of predicates by their negation dependencies. A program is *stratifiable* if its predicates can be arranged in layers (strata) such that negation only refers to predicates in lower strata — never to predicates in the same or higher stratum.

```prolog
% Stratifiable: negation only refers "down"
bird(tweety).
penguin(opus).
flies(X) :- bird(X), \+ penguin(X).   % flies (stratum 2) negates penguin (stratum 1) ✓

% Non-stratifiable: odd cycle through negation
p :- \+ q.
q :- \+ p.   % p and q negate each other — undefined semantics ✗
```

Non-stratifiable programs have undefined NAF semantics. Cyclops Storm includes a compile-time `StratificationAnalyzer` that detects these cases via dependency graph analysis (Tarjan's algorithm for strongly connected components).

