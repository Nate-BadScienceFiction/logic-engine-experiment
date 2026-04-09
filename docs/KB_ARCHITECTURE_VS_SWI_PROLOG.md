# Cyclops Storm vs SWI-Prolog: Architectural Comparison

**Last Updated:** 2026-04-09
**Purpose:** Architectural comparison of Cyclops Storm (Event Calculus reasoner) vs SWI-Prolog (general-purpose Prolog)
**For:** People choosing between Cyclops Storm and SWI-Prolog for narrative/temporal reasoning vs general Prolog work
**See also:** `docs/KB_API_AND_DESIGN.md` for the Cyclops Storm API reference and internal design

---

## Executive Summary

- **Cyclops Storm**: Python-based Event Calculus reasoner specialized for temporal logic and narrative reasoning with first-class belief state tracking
- **SWI-Prolog**: C-based general-purpose Prolog runtime optimized for ISO compliance and raw performance
- **Core Trade-off**: Python maintainability & EC specialization vs C speed & ecosystem maturity
- **Use Cyclops Storm** when Event Calculus reasoning, narrative analysis, and Python integration are essential
- **Use SWI-Prolog** when you need general logic programming with significantly better performance

---

## At a Glance: Comparison Matrix

| Feature | Cyclops Storm | SWI-Prolog |
|---------|---------|------------|
| **Performance** | Python (significantly slower) | C (optimized WAM) |
| **EC Reasoning** | Native, first-class | Library-based |
| **Python Integration** | Native API | FFI (janus) |
| **Tabling** | Variant-based + selective (`:- table`) | Variant + subsumptive |
| **Maintainability** | Modular Python | Monolithic C |
| **ISO Compliance** | Prolog subset | Full ISO Prolog |
| **Narrative Reasoning** | Specialized (belief states, provenance) | Not built-in |
| **Test Suite** | ~6,000 tests, 99%+ pass | 10,000+ tests |

---

## Section 1: Why Logic Programming?

Logic programming shines when your problem is **relationships + rules**, and you want to ask **many different questions** over the same knowledge.

In imperative code, you write procedures that answer one question at a time. In Prolog, you state the rules of the world, then query them. The same code can *verify* ("is Alice allowed?"), *generate* ("who is allowed?"), and *audit* ("show all access paths")—without rewriting logic.

### A Tiny Example: Access Control

```prolog
% Facts
has_role(alice, engineer).
has_role(bob,   intern).
inherits(engineer, staff).
inherits(intern, staff).
perm(staff, repo, read).
perm(engineer, repo, write).
denied(bob, prod, _).

% Rules
role(U, R) :- has_role(U, R).
role(U, R2) :- has_role(U, R1), inherits(R1, R2).
allowed(U, Res, Act) :- role(U, R), perm(R, Res, Act), \+ denied(U, Res, Act).
```

Now ask it three ways:

```prolog
?- allowed(alice, repo, write).   % Verify: yes
?- allowed(Who, repo, read).      % Generate: Who = alice ; bob
?- allowed(Who, Res, Act).        % Audit: enumerate all grants
```

Same 11 lines of rules—many questions.

### The Connection to Event Calculus

Cyclops Storm applies this pattern to **time**. Instead of "who can access what," you ask "what holds when":

```prolog
?- holds_at(in_room(agent, kitchen), t3).   % Verify state at time
?- holds_at(What, t5).                       % Generate: what's true at t5?
?- initiates(Event, holding(agent, key)).    % Audit: what causes key possession?
```

The EC predicates (`happens`, `holds_at`, `initiates`, `terminates`) are the temporal version of `allowed`—declarative rules you query from any angle.

---

## Section 2: Conceptual Comparison—What Each Is For

### 2.1 Design Philosophy & Primary Use Cases

Cyclops Storm is a **domain-specific Event Calculus reasoner**, NOT a general-purpose Prolog system. It targets:

1. **Event Calculus (EC) reasoning** - causal rules, fluents, temporal propagation
2. **Belief state management** - tracking what holds at different time points with provenance
3. **Narrative reasoning** - extracting and reasoning about story events
4. **Python integration** - native API, works with NumPy, pandas, scikit-learn

SWI-Prolog is a **general-purpose logic programming runtime** optimized for:

1. **ISO Prolog compliance** - full standard implementation
2. **Performance** - C-based WAM with JIT compilation
3. **Ecosystem maturity** - 30+ years, extensive libraries (HTTP, XML, RDF, CLP)
4. **Constraint solving** - CLP(FD), CLP(R), CLP(Q)

| Aspect | Cyclops Storm | SWI-Prolog |
|--------|---------|------------|
| **Primary Use Case** | Event Calculus temporal reasoning | General-purpose logic programming |
| **Implementation** | Python (100% pure Python) | C with Prolog runtime |
| **Query Model** | Python API + Prolog-like syntax | Native Prolog shell/API |
| **Extensions** | EC predicates (`happens`, `holds_at`, `initiates`) | ISO Prolog + SWI extensions |
| **State Management** | Explicit belief state tracking | Implicit via database |
| **Time Model** | First-class temporal reasoning | Library-based constraints |

### 2.2 Event Calculus vs General Prolog: A Concrete Example

**The Problem**: Track an agent's location across multiple room changes over time.

**Cyclops Storm Approach** (explicit time points, 2-arity causal rules, ground initiates/terminates):
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
# → [{}]  ✓ move at t5 initiates bedroom
```

**Key Features**:
- Automatic state persistence (frame problem solved via inertia)
- Historical queries ("what held at time t3?")
- Provenance tracking ("why does agent hold key at t5?")
- No manual bookkeeping required

**SWI-Prolog Approach** (manual state management):
```prolog
% Requires dynamic predicates and manual assertion/retraction
:- dynamic current_room/2.
current_room(agent, kitchen).  % Initial state

move(Agent, NewRoom, Time) :-
    retract(current_room(Agent, _OldRoom)),
    assert(current_room(Agent, NewRoom)),
    assert(happened_at(move(Agent, NewRoom), Time)).

% Problem: No automatic state persistence
% Cannot ask "what held at time t3?" without manual bookkeeping
% Must record every state transition explicitly
```

**The Difference**: Cyclops Storm treats time as a first-class concept; SWI-Prolog treats it as data you manage yourself.

### 2.3 Semantic Contract: Cyclops Storm's Prolog Subset

Cyclops Storm implements a **restricted Prolog subset** optimized for Event Calculus. This section defines exactly what "Prolog-ish" means here.

#### Operational Semantics

| Operation | Cyclops Storm Behavior | ISO Prolog Difference |
|-----------|------------------|----------------------|
| **Unification** | Recursive with **occurs check always on**. Immutable substitutions (new dict per binding). | ISO: occurs check off by default (`unify_with_occurs_check/2` for explicit). Cyclops Storm safer but slower. |
| **Backtracking** | Generator-based DFS with explicit choice point stack. Yields solutions incrementally. | ISO: WAM trail-based. Cyclops Storm equivalent semantics, significantly slower. |
| **Disjunction** | `(A ; B)` and n-ary `(A ; B ; C ; ...)` supported via `OrNode`. Left-associative parsing; evaluates branches left-to-right, backtracks into alternatives. | ISO-compliant. |
| **Cut (`!`)** | Supported. Routed to DFS engine which has native cut via goal stack pruning. | ISO: full ancestor cut. |
| **NAF (`\+`)** | Closed-world assumption. **Requires ground arguments** (see floundering below). Subproof isolation. | ISO-compliant when ground. |
| **Time Pruning** | `cutoff_time` parameter limits temporal horizon. Events beyond cutoff ignored in `holds_at`, `initiates`, `terminates`. EC-specific, no ISO equivalent. | N/A—EC extension. |

#### Supported vs Unsupported ISO Behaviors

| Feature | Status | Notes |
|---------|--------|-------|
| First-order terms | ✅ Supported | `foo(X, bar(Y, Z))` |
| Variables | ✅ Supported | Explicit UID-based identity |
| Atoms, integers, floats | ✅ Supported | Standard representation |
| Lists | ✅ Supported | `[H|T]`, `[]`, `[a,b,c]` |
| Arithmetic (`is/2`) | ✅ Supported | `X is 3 + 4`, `Y is X * 2`, `Z is -(X)` (unary minus via expression), `-10` (negative number literals) |
| Comparison (`<`, `>`, `=<`, `>=`) | ✅ Supported | Numeric comparison |
| Equality (`=`, `\=`) | ✅ Supported | Unification-based |
| Arithmetic equality (`=:=`, `=\=`) | ✅ Supported | Evaluates both sides arithmetically, compares results |
| Member, append, length | ✅ Supported | Built-in list predicates |
| String/atom predicates | ✅ Supported | `atom_concat/3`, `atom_number/2`, `atom_length/2`, `sub_atom/5`, `atom_chars/2` |
| Findall, bagof, setof | ⚠️ Partial | `findall/3` and `setof/3` supported; `bagof/3` not implemented |
| Assert/retract | ❌ Unsupported | Use Python API: `engine.add()`, epoch-based |
| Module system | ❌ Unsupported | Single namespace |
| DCG notation | ❌ Unsupported | No grammar rules |
| Exceptions | ❌ Unsupported | No `catch/throw` |
| Meta-predicates (`call/N`) | ❌ Unsupported | No `call/1` or higher-order predicates |

#### NAF Groundness & Floundering

**Rule**: `\+ Goal` **requires `Goal` to be ground** after substitution application.

| Scenario | Result | Rationale |
|----------|--------|-----------|
| `\+ member(3, [1,2,3])` | Fails (3 is member) | Ground, safe evaluation |
| `\+ member(X, [1,2,3])` | **Flounders → backtrack** | Unbound `X` makes NAF undefined |
| `p(X), \+ q(X)` | Safe if `p(X)` binds `X` first | Left-to-right evaluation grounds `X` |
| `\+ q(X), p(X)` | **Flounders** | `X` unbound when NAF evaluated |

**Flounder Policy**: Non-ground NAF triggers immediate backtrack (no binding, no error). A `NAFFlounderingWarning` is logged to aid debugging.

**Why This Matters**: Write `positive_goal(X), \+ negative_check(X)` not the reverse.

#### Stratification Analysis

Cyclops Storm includes compile-time stratification checking via `StratificationAnalyzer`:

```python
from kb.engine.evaluation import check_stratification
result = check_stratification(rules, strict=True)
# Detects: p :- \+ q. q :- \+ p.  # Non-stratifiable (odd loop)
```

Non-stratifiable programs have undefined NAF semantics. The analyzer builds the predicate dependency graph, finds strongly connected components (Tarjan's algorithm), and flags any SCC containing negative edges.

---

## Section 3: Architecture & Data Model

### 3.1 Cyclops Storm Architectural Overview

```
KBEngine (kb_engine.py) ─── Facade
│
├── IndexedFactStore → FactStore ─ Ground truth facts with indexing
├── TemporalReasoner ─ Time ordering and causality
├── RuleCompiler ──── Rule indexing and optimization
├── PredicateEvaluator ─ Unified fact+rule evaluation (delegates to Reasoner)
│
├── Reasoner (kb_reasoner.py) ─── Inference Coordinator
│   ├── DFS Engine (backtracking.py) ─ WAM-lite backtracking, cut
│   ├── Legacy Engine (LegacyDerivedEvaluator) ─ EC evaluation, tabling
│   ├── Routing
│   │   ├── RoutingFSM + QueryAnalyzer (DFS vs Legacy selection)
│   │   ├── EngineRouter (dispatch)
│   │   └── FrameManager (mid-rule engine lock)
│   ├── SequenceEvaluationCoordinator ─ Strategy-based body evaluation
│   ├── Tabling (TablingCoordinator → TableManager) ─ SLG-style
│   ├── NegationOppositeHandler ─ Fluent negation logic
│   └── Temporal Components
│       ├── FluentEvaluator (holds_at)
│       ├── PersistenceEvaluator (clipping checks)
│       ├── ExclusivityHandler (mutual exclusion)
│       ├── EventCalculusCore (EC operations)
│       └── EventCalculusQueries, SimultaneousEventHandler
│
├── EpochCacheManager ─ Cache invalidation
└── Query Pipeline, Parsing, Handler Registry
```

**Component Roles**:
- **IndexedFactStore**: Wraps `FactStore` with additional indexes; ground truth, lookup by functor
- **TemporalReasoner**: Enforces before/after ordering, cutoff time pruning
- **Routing** (on Reasoner): Routes pure Prolog → DFS (faster), EC → Legacy (full semantics)
- **Tabling** (on Reasoner): Variant-based memoization for recursive queries (producer/consumer protocol), runs in Legacy engine
- **EpochCacheManager** (on KBEngine): Cache invalidation; each `add()` calls `clear_all()`, eagerly clearing all five cache levels and bumping the epoch

### 3.2 Data Model: Terms & Variables

**Cyclops Storm** — Frozen Dataclasses (Immutable):
```python
@dataclass(frozen=True)
class Var:
    name: str
    uid: int  # Unique identifier (no X vs X$1 issues)

@dataclass(frozen=True)
class Term:
    functor: str
    args: tuple  # Immutable!
```

- **Immutability**: Prevents aliasing bugs, safe concurrent access
- **Explicit UIDs**: Eliminates variable identity confusion
- **Introspection**: Full Python `repr()`, debugger support, easy serialization
- **Trade-off**: Heavier per-object than C tagged pointers

**SWI-Prolog** — Tagged Pointers (C):
- Type info in pointer low bits, compact 8-byte variables
- Pointer arithmetic, no allocation for small integers
- Structure sharing via pointers (unify without copying)
- Trade-off: harder to debug, no safety guarantees, C memory management

### 3.3 State Management Comparison

#### Substitution Handling

| Aspect | Cyclops Storm | SWI-Prolog |
|--------|---------|------------|
| **Model** | Immutable dictionaries | Trail-based mutation |
| **Backtracking** | Return previous dict | Undo trail entries |
| **Memory** | Heavier (Python dict per binding) | Lighter (pointer per binding) |
| **Aliasing bugs** | Impossible (immutable) | Possible (shared refs) |
| **Debugging** | Full `repr()` at any point | Trail inspection needed |

#### Database Modification

| Aspect | Cyclops Storm | SWI-Prolog |
|--------|---------|------------|
| **Fact addition** | Eager cache clear (`clear_all()`) | `assert/1`, `assertz/1` |
| **Fact removal** | Eager cache clear (`clear_all()`) | `retract/1`, `abolish/1` |
| **Cache safety** | Automatic invalidation | Manual management |
| **Concurrency** | Thread-safe epochs | Transaction-based |

Cyclops Storm's EpochCacheManager ensures cache coherence:
```python
engine.add("person(alice)")           # caches cleared, epoch bumped
engine.add_facts(["person(bob)",
                   "friend(bob, carol)"])  # caches cleared once (after all facts stored)
```

SWI-Prolog uses direct database modification:
```prolog
:- dynamic person/1.
assertz(person(alice)).
retract(person(bob)).
% Tabled predicates need explicit abolish_all_tables/0
```

#### Temporal State (Belief States)

This is Cyclops Storm's key differentiator—first-class temporal state tracking with provenance.

| Aspect | Cyclops Storm | SWI-Prolog |
|--------|---------|------------|
| **Time model** | First-class time points | User-managed |
| **State queries** | `holds_at(F, T)` built-in | Manual implementation |
| **Provenance** | Automatic causal chains | Not built-in |
| **Frame problem** | Solved (inertia axiom) | Manual axioms needed |

#### Cache Invalidation

| Strategy | Cyclops Storm | SWI-Prolog |
|----------|---------|------------|
| **Granularity** | Global (all caches) | Table-level |
| **Trigger** | `clear_all()` on mutation | Manual or incremental |
| **Method** | Eager (physical clear on mutation) | Eager or lazy |
| **Correctness** | Guaranteed | User responsibility |

Cyclops Storm eagerly clears all five cache levels on every mutation via `clear_all()`—simple and correct, no partial invalidation bugs. A lighter-weight `bump_epoch()` exists for lazy invalidation but is not currently used by the default `add()` path. SWI-Prolog's incremental tabling (`:- table pred/N as incremental`) is more fine-grained but requires explicit declarations.

---

## Section 4: Core Runtime Behavior

### 4.1 Unification

| Aspect | Cyclops Storm | SWI-Prolog |
|--------|---------|------------|
| **Model** | Pure functional (returns new dict) | In-place mutation (pointer binding) |
| **Occurs check** | Always on (safe) | Off by default (fast) |
| **Memory** | Heavier (Python dict) | Lighter (pointer) |
| **Structure sharing** | No (copies) | Yes (pointers) |

SWI-Prolog is significantly faster. Cyclops Storm trades speed for safety (no aliasing bugs) and Python debugger support.

### 4.2 Backtracking & Choice Points

| Aspect | Cyclops Storm | SWI-Prolog |
|--------|---------|------------|
| **Implementation** | Python generators + explicit choice point stack | WAM bytecode + trail |
| **Clause indexing** | Linear scan by default (first-argument indexing behind `ENGINE_INDEXING` flag) | First-argument indexing |
| **Cut** | Supported (DFS engine, goal stack pruning) | Full ancestor cut |
| **Tail call opt** | No | Yes |

SWI-Prolog is significantly faster for pure Prolog. Cyclops Storm gains maintainability and EC-specific optimizations.

### 4.3 Tabling (SLG Resolution)

**Cyclops Storm** — Variant-Based with Producer/Consumer Protocol and Selective Tabling:

```prolog
% Prolog-style directive support
:- table reaches/2.           % Single predicate
:- table ancestor/2, path/2.  % Multiple predicates (comma-separated)

reaches(X, Y) :- edge(X, Y).
reaches(X, Z) :- edge(X, Y), reaches(Y, Z).  % Recursive - uses tabling
```

- **`:- table` directive support**: Standard Prolog syntax for declaring tabled predicates
- **Selective tabling**: Only registered predicates use tabling machinery
- **Blanket mode**: If no directives, all predicates use tabling (backward compat)
- **Variant-based**: `p(X,Y)` and `p(A,B)` share the same table
- **Fixpoint iteration**: Iterate until no new answers
- **Runs in Legacy engine**: Tabling is coordinated by `TablingCoordinator` in the Legacy evaluation path

**SWI-Prolog** — Variant + Subsumptive Tabling:
- Variant tabling (like Cyclops Storm)
- Subsumptive tabling (`p(1,X)` can reuse answers from `p(X,Y)`)
- Incremental updates (recompute only affected tables)
- Well-founded semantics (handles NAF correctly)
- Native C implementation — significantly faster

---

## Section 5: Event Calculus & Belief States—What Cyclops Storm Adds

> **This is Cyclops Storm's core value proposition.** If you're deciding between systems, this section shows what you get with Cyclops Storm that SWI doesn't provide out-of-the-box.

### 5.1 Event Calculus as First-Class

Event Calculus is a framework for temporal reasoning about events, fluents (time-varying properties), and causality. Cyclops Storm implements discrete EC with explicit time points.

**Core EC Predicates** (2-arity for initiates/terminates):

| Predicate | Meaning |
|---|---|
| `initially(F)` | Fluent F holds at the initial time |
| `happens(E, T)` | Event E occurs at time T |
| `initiates(E, F)` | Event E starts fluent F |
| `terminates(E, F)` | Event E ends fluent F |
| `holds_at(F, T)` | Fluent F holds at time T |
| `before(T1, T2)` | T1 precedes T2 |

```prolog
% Facts
happens(leave_room(agent1, room1), t3).
initially(in_room(agent1, room1)).
before(t1, t2). before(t2, t3).

% Causal rules (2-arity)
initiates(enter_room(Agent, Room), in_room(Agent, Room)).
terminates(leave_room(Agent, Room), in_room(Agent, Room)).

% Query
?- holds_at(in_room(agent1, room1), t2).
```

**The holds_at Algorithm** (Conceptual):
1. **Check initially path**: If `initially(F)` and fluent not terminated → HOLDS
2. **Find initiations**: Search for events that initiated fluent
3. **Check clipping**: For each initiation, verify fluent not terminated before query time
4. **Return first valid**: First unclipped initiation proves fluent holds

**Key Features**:
- **Frame Problem Solution**: Fluents persist unless explicitly terminated (inertia axiom)
- **Causal Rule Evaluation**: Checks both facts AND rules for `initiates`/`terminates`
- **Tie-Breaking**: Policies for simultaneous events (`init_wins`, `term_wins`)
- **Cutoff Time**: Performance optimization limiting temporal horizon
- **Pre-state vs Post-state**: T+1 semantics for event effects

**Rule-Based Causal Reasoning**: `initiates` and `terminates` can be rules, not just ground facts:

```prolog
% Conditional initiation: taking a key only works if you're in the same room
initiates(take(Agent, Key), holding(Agent, Key)) :-
    holds_at(in_room(Agent, Room), T),
    holds_at(location(Key, Room), T).
```

This allows preconditions on causality — the event's effect depends on the current state. Cyclops Storm evaluates these rules during `holds_at` checks, combining temporal reasoning with logical inference.

### 5.2 Belief State Management & Provenance

**The Problem**: Not just "does fluent F hold at time T?", but "**why** does it hold?"

**Cyclops Storm Solution**: Provenance tracking with complete causal chains.

**Example Provenance Chain**:
```
Query: Why does holds_at(holding(agent1, key), t5) return true?

Provenance:
1. initially(in_room(agent1, room1)) [t0: initial]
2. happens(take(agent1, key), t3) [t3: event]
3. initiates(take(agent1, key), holding(agent1, key))
   :- holds_at(in_room(agent1, room1), t3),  [✓ precondition satisfied]
      holds_at(location(key, room1), t3).     [✓ precondition satisfied]
4. holding(agent1, key) initiated at t3, not terminated → HOLDS at t5
```

**Why This Matters for Narrative Reasoning**:
- Explain agent actions ("Why does agent have the key?")
- Debug causal chains ("Which events led to this state?")
- Generate story summaries ("Agent entered room, took key, unlocked door")
- Validate consistency ("No contradictory state transitions")

**Key Features**:
- **Incremental construction**: Build states on-demand (not all time points upfront)
- **Provenance tracking**: Complete causal chains for explainability
- **State transitions**: Diff computation between time points
- **Exclusive fluents**: Mutex enforcement (agent in only one room)
- **Cache management**: Epoch-based invalidation with eager `clear_all()` on mutation

### 5.3 Hybrid Engine Routing

**The Challenge**: Balance performance (DFS engine) with EC semantics (Legacy engine).

**What Goes Where**:

| Query type | Engine | Example |
|---|---|---|
| Simple fact lookup (allowlisted) | DFS | `person(alice)`, `child(bob)` |
| Rule with cut (`!`) | DFS | `max(X, Y, X) :- X >= Y, !.` |
| `holds_at` / temporal predicates | Legacy | `holds_at(in_room(agent, kitchen), t3)` |
| Tabled recursive predicate | Legacy | `path(X, Y) :- edge(X, Z), path(Z, Y).` |
| NAF in complex context | Legacy | `flies(X) :- bird(X), \+penguin(X).` |
| Default (unknown predicate) | Legacy | Any predicate not explicitly routed to DFS |

**Key principle:** Legacy is the safe default. DFS is an optimization for predicates that are proven safe — pure logic with no temporal dependencies, no tabling, and no complex control flow.

**Engine Capabilities**:

| Feature | DFS Engine | Legacy Engine |
|---------|------------|---------------|
| Unification | ✓ | ✓ |
| Backtracking | ✓ | ✓ |
| NAF | ✓ (limited) | ✓ |
| Cut (!) | ✓ (goal stack pruning) | ✓ (CutSequenceStrategy + CutCommit exceptions) |
| Tabling | ✗ | ✓ |
| EC Predicates | ✗ | ✓ |
| Temporal Reasoning | ✗ | ✓ |
| Belief States | ✗ | ✓ |

---

## Section 6: Performance, Memory, and Testing

### 6.1 Performance Characteristics

Cyclops Storm is significantly slower than SWI-Prolog for pure Prolog operations (Python vs C), which is acceptable for the EC-centric interactive narrative use case.

| Operation | Cyclops Storm | SWI-Prolog |
|-----------|---------|------------|
| Pure Prolog (unification, backtracking) | Python overhead | C/WAM optimized |
| EC temporal queries (`holds_at`) | Specialized algorithms | Not built-in |

**Key trade-off**: Cyclops Storm trades raw performance for Python ecosystem integration, maintainability, and EC specialization. For interactive narrative reasoning, this is acceptable.

### 6.2 Memory Usage

Cyclops Storm uses significantly more memory than SWI-Prolog due to Python's object model and immutable substitutions.

| Aspect | Cyclops Storm | SWI-Prolog |
|--------|---------|------------|
| Variables | Heavier (Python dataclass) | Lighter (tagged pointer) |
| Substitutions | Heavier (immutable dict per binding) | Lighter (trail entry per binding) |

**Trade-off**: Cyclops Storm uses more memory but gains immutability (no aliasing bugs), introspection (debugger support), Python integration, and easy serialization.

### 6.3 Optimization Strategies

**Cyclops Storm**:
1. **Batch operations**: `add_facts()` / `add_rules()` clear caches once instead of per-fact
2. **Engine routing**: Pure queries → faster DFS engine
3. **Indexed fact store**: Lookup by functor
4. **Epoch-based caching**: Eager `clear_all()` on mutation guarantees correctness

**SWI-Prolog**:
1. **First-argument indexing**: Fast clause selection
2. **JIT compilation**: Bytecode → native code
3. **Tail call optimization**: No stack growth for recursion
4. **Structure sharing**: Unify without copying
5. **Generational GC**: Efficient memory management

### 6.4 Testing

Both systems have mature, comprehensive test suites. Cyclops Storm's ~6,000 tests with 99%+ pass rate indicates robustness for its target domain. SWI-Prolog's suite covers ISO compliance, extensions, and libraries.

---

## Section 7: Conclusions & Use Case Recommendations

### Summary

Cyclops Storm is a **specialized Event Calculus reasoner**, NOT a general-purpose Prolog system like SWI-Prolog.

**Key Differentiators**:
1. **Domain Focus**: EC reasoning, narrative analysis, belief states with provenance
2. **Python Native**: Seamless ecosystem integration (NumPy, pandas, scikit-learn)
3. **Maintainability**: Modular architecture, comprehensive tests (~6,000 tests, 99%+ pass)
4. **Selective Tabling**: `:- table` directive support
5. **Trade-offs**: Significantly slower than SWI-Prolog, but acceptable for interactive narrative reasoning

### Use Cyclops Storm When

- **Event Calculus reasoning** is a core requirement
- **Python integration** is essential (no FFI, native API)
- **Narrative/story analysis** needed (provenance, belief states)
- **Maintainability** > raw performance
- **ML/NLP integration** required (scikit-learn, spaCy, transformers)
- **Temporal logic** with explicit time points
- **Explainability** matters (provenance chains, causal reasoning)

### Use SWI-Prolog When

- **General logic programming** needed
- **Performance** is critical
- **ISO Prolog compliance** required
- **Mature ecosystem** needed (30+ years, extensive libraries)
- **Constraint solving** (CLP) required
- **Large-scale** deployment

### Final Recommendation

The choice between Cyclops Storm and SWI-Prolog is **not about better/worse—it's about fit**.

- **Choose Cyclops Storm** if your problem is **temporal reasoning about events and narratives in Python**.
- **Choose SWI-Prolog** if your problem is **general logic programming with performance requirements**.

---

## Glossary (Quick Reference)

| Term | Definition |
|---|---|
| **Backtracking** | Search strategy: try alternatives in order, undoing bindings on failure |
| **Cutoff Time** | Temporal pruning parameter that limits the horizon of EC queries |
| **DFS Engine** | Depth-first search engine for pure Prolog; handles cut, backtracking, limited NAF |
| **EC (Event Calculus)** | Logical formalism for reasoning about events, fluents, and causality over time (Kowalski & Sergot, 1986) |
| **Epoch** | Cache invalidation marker; each knowledge base mutation triggers `clear_all()`, eagerly clearing all caches and bumping the epoch counter |
| **Flounder** | When NAF is applied to a goal with unbound variables; Cyclops Storm triggers immediate backtrack |
| **Fluent** | Time-varying property in EC whose truth value changes as events occur (e.g., `in_room(agent, kitchen)`) |
| **Frame Problem** | The challenge of representing what doesn't change after an action; EC solves it via the inertia axiom |
| **Inertia Axiom** | EC principle: fluents persist unless explicitly terminated |
| **Legacy Engine** | Cyclops Storm's original evaluator; handles EC predicates, tabling, temporal reasoning, and belief states |
| **NAF** | Negation-as-failure: `\+ P` succeeds iff P cannot be proven (closed-world assumption) |
| **Provenance** | Causal chain tracking that records *why* a fluent holds, not just *that* it holds |
| **Selective Tabling** | Applying tabling only to predicates declared with `:- table`, skipping overhead for others |
| **SLG Resolution** | Tabling algorithm (producer/consumer protocol) that memoizes recursive results and detects cycles |
| **Stratification** | Layering predicates by negation dependencies; non-stratifiable programs have undefined NAF semantics |
| **Unification** | Pattern matching that produces variable bindings; the core operation of all Prolog reasoning |
| **WAM** | Warren Abstract Machine — the standard Prolog execution model (Warren, 1983); used by SWI-Prolog, not Cyclops Storm |


---

## Detailed Glossary of Key Terms

This glossary defines technical terms used throughout this document, with particular attention to concepts that may be unfamiliar to readers without a logic programming background.

### Unification

**Unification** is the fundamental pattern-matching operation underlying all Prolog-style reasoning. Given two terms, unification finds a *substitution* (a mapping from variables to values) that makes the terms identical, or reports failure if no such mapping exists.

```prolog
f(X, b) = f(a, Y)    → X = a, Y = b       % ground arguments match, variables bind
f(X, X) = f(a, b)    → FAIL                 % X can't be both a and b
f(X, Y) = f(Y, a)    → X = a, Y = a         % chains: X→Y→a
```

Cyclops Storm uses immutable substitution dictionaries and always-on occurs check (preventing circular terms like `X = f(X)`). SWI-Prolog uses in-place pointer binding with occurs check off by default, which is faster but can create circular structures if not careful.

### Backtracking

**Backtracking** is Prolog's mechanism for exploring multiple solutions. When a goal has multiple possible matches, the engine tries each in order, undoing variable bindings between attempts:

```prolog
color(apple, red). color(banana, yellow). color(cherry, red).
?- color(X, red).     → X = apple ; X = cherry
```

Cyclops Storm implements backtracking with Python generators — each choice point `yield`s a solution, and the caller can request more by advancing the generator. SWI-Prolog uses the WAM trail for efficient undo logging.

### DFS Engine

The **Depth-First Search Engine** is Cyclops Storm's faster query evaluator for pure Prolog queries. It implements classical Prolog's left-to-right, depth-first search strategy using an explicit choice point stack rather than the recursive evaluation used by the Legacy engine. The DFS engine traverses the search space by exploring each branch fully before backtracking to try alternatives, yielding solutions incrementally via Python generators. It handles unification, backtracking, disjunction (`A ; B`, including n-ary `A ; B ; C ; ...`), cut (`!`), and limited negation-as-failure, but lacks support for Event Calculus predicates and temporal reasoning. Cut is implemented as a builtin that succeeds and commits to the current clause. Queries are routed to the DFS engine when they contain only "pure" predicates (no EC, no unsafe NAF), providing significant performance improvement over the Legacy engine for applicable queries.

### DFS Allowlist

The **DFS Allowlist** is a configuration set that specifies which user-defined predicates are safe to evaluate using the faster DFS engine. By default, Cyclops Storm conservatively routes most queries to the Legacy engine to ensure correct semantics. The allowlist mechanism allows specific predicates (e.g., `person/1`, `child/2`) to be marked as "pure Prolog"—meaning they don't depend on Event Calculus reasoning, temporal state, or features the DFS engine doesn't support. When a query involves only allowlisted predicates and built-in pure predicates, the routing FSM directs it to the DFS engine. The allowlist is currently `{person, child}` only — `sibling` is excluded due to a known DFS compound-rule backtracking bug where the engine produces 0 results for rules with 3+ conjuncts (e.g., `sibling(X,Y) :- parent(Z,X), parent(Z,Y), different(X,Y)`).

### EC (Event Calculus)

**Event Calculus** is a logical formalism for reasoning about events, actions, and their effects over time. Originally developed by Kowalski and Sergot (1986) for database applications, it provides a declarative framework for specifying how events initiate and terminate time-varying properties (fluents). The core EC predicates include: `happens(Event, Time)` (an event occurs), `initiates(Event, Fluent)` (an event starts a property holding), `terminates(Event, Fluent)` (an event stops a property holding), `holds_at(Fluent, Time)` (a property holds at a time), and `initially(Fluent)` (a property holds at the initial time). Cyclops Storm uses 2-arity `initiates/2` and `terminates/2` as the standard form; a legacy 3-arity form (`initiates(Event, Fluent, Time)`) is also accepted. EC elegantly solves the *frame problem*—determining what remains unchanged after an action—through an inertia axiom: fluents persist unless explicitly terminated. Cyclops Storm implements discrete EC with explicit time points, making it suitable for narrative reasoning where events occur at specific moments in a story timeline.

### Fluents

**Fluents** are time-varying properties in Event Calculus—predicates whose truth value can change over time as events occur. The term comes from "flowing" or "flux," reflecting that these properties are not static facts but dynamic states. For example, `in_room(agent, kitchen)` is a fluent representing the agent's location, which changes when movement events occur. Fluents contrast with *static predicates* like `color(apple, red)` that don't change over time. In Cyclops Storm, fluents are the subjects of `holds_at/2` queries and the objects of `initiates/2` and `terminates/2` causal rules. The system tracks fluent lifecycles: when they were initiated, whether they've been terminated (clipped), and the complete provenance chain explaining why a fluent holds or doesn't hold at any given time point. Fluents can also be *exclusive*—only one value can hold at a time (e.g., an agent can only be in one room).

### Flounder (Floundering)

**Floundering** occurs when negation-as-failure (NAF) is applied to a goal containing unbound variables. Since NAF uses the closed-world assumption ("if we can't prove P, then ¬P"), applying it to a non-ground goal like `\+ member(X, [1,2,3])` is semantically problematic: we cannot enumerate all possible values of X to check that none are members. Different Prolog systems handle floundering differently—some delay the negation until variables become bound, some raise errors, and some produce unsound results. Cyclops Storm implements a conservative flounder policy: when NAF encounters a non-ground goal, it immediately triggers backtracking without binding any variables or raising an error. This means queries must be written to ground variables *before* negation: `member(X, Candidates), \+ excluded(X)` succeeds, but `\+ excluded(X), member(X, Candidates)` flounders. The term "flounder" evokes a fish out of water—the computation is stuck, unable to proceed meaningfully.

### NAF (Negation as Failure)

**Negation as Failure** is Prolog's approach to negation under the closed-world assumption: a goal `\+ P` succeeds if and only if `P` cannot be proven from the knowledge base. Unlike classical logical negation, NAF doesn't require explicit negative facts—absence of proof is treated as proof of absence. This makes NAF non-monotonic: adding new facts can cause previously successful negations to fail. In Cyclops Storm, NAF is implemented by attempting to prove the inner goal in an isolated subproof; if the subproof yields no solutions, the negation succeeds with the current substitution unchanged. NAF has important limitations: it requires ground arguments (see *Floundering*), it doesn't work well with incomplete information, and it can interact subtly with other control constructs like cut and disjunction. The Legacy engine handles NAF more robustly than the DFS engine, which is why queries with potentially unsafe NAF are routed to Legacy.

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

The implementation maintains a set of `(functor, arity)` tuples representing registered predicates. During query evaluation, the reasoner checks this registry before entering the tabling code path, allowing unregistered predicates to skip table lookup, producer/consumer protocol, and fixpoint iteration—resulting in faster evaluation for predicates that don't need memoization.

### SLG (SLG Resolution / Tabling)

**SLG Resolution** (Selective Linear Definite clause resolution with Generalization) is the tabling algorithm that enables efficient evaluation of recursive queries by memoizing intermediate results. Without tabling, a query like computing the transitive closure of a graph can loop infinitely or recompute the same subgoals exponentially many times. SLG resolution, pioneered by the XSB Prolog system, addresses this through a producer/consumer protocol: the first call to a tabled predicate becomes a "producer" that computes answers, while subsequent calls with equivalent (variant) arguments become "consumers" that reuse cached answers. When a consumer encounters a call that's still being evaluated (a cycle), it suspends and waits for the producer to generate answers. Cyclops Storm implements variant-based tabling where goals like `path(X, Y)` and `path(A, B)` share the same table entry (alpha-equivalent variants). The system uses fixpoint iteration to handle recursive definitions, continuing until no new answers are produced. SLG is essential for Cyclops Storm's temporal reasoning, where queries like "all times before T5" involve recursive `before/2` relationships.

### Cutoff Time

**Cutoff Time** is Cyclops Storm's temporal pruning optimization that limits the horizon of Event Calculus queries. When evaluating `holds_at(Fluent, T)` with a cutoff, the system ignores events occurring after the cutoff time, reducing the search space for initiation and termination checks.

For example, in a narrative with 1000 time points, querying `holds_at(F, t500)` with a cutoff of `t500` means the engine only considers events up to `t500`, ignoring the other 500 time points entirely. This is particularly useful for interactive narrative systems where only recent history matters, or for debugging where you want to isolate behavior within a specific time window. Cutoff time is passed through the evaluation context and affects `holds_at`, `initiates`, `terminates`, and related EC predicates.

### Epoch

**Epoch** is Cyclops Storm's cache invalidation mechanism, implemented by the `EpochCacheManager`. Each mutation to the knowledge base (adding or removing facts) calls `clear_all()`, which physically clears all five cache dictionaries in place and bumps the epoch counter. A lighter-weight `bump_epoch()` method exists for lazy invalidation (entries become stale but are not reclaimed until re-queried), though the engine currently uses `clear_all()` by default.

```python
engine.add("person(alice).")           # caches cleared, epoch bumped
engine.query("person(X)")              # computed fresh, cached
engine.add("person(bob).")             # caches cleared again
engine.query("person(X)")              # recomputed, now returns both
# Batch alternative: engine.add_facts([...]) clears only once
```

This eager invalidation approach is simple and guarantees correctness (no stale results) at the cost of coarse granularity (all caches affected by any mutation). SWI-Prolog's incremental tabling is more fine-grained but requires explicit declarations.

### Frame Problem

The **Frame Problem** is a fundamental challenge in AI and logic programming: how to efficiently represent what *doesn't* change when an action occurs. Naively, you'd need explicit "frame axioms" stating that every unchanged property persists after every action—an exponential blowup. For example, if "opening a door" doesn't affect an agent's location, you'd need `opens(Door, T), holds_at(location(Agent, Room), T) → holds_at(location(Agent, Room), T+1)` for every possible property. Event Calculus solves this elegantly via the *inertia axiom*: fluents persist by default unless explicitly terminated. Cyclops Storm implements this implicitly—`holds_at` only checks for termination events, not for preservation.

### Inertia Axiom

The **Inertia Axiom** is Event Calculus's solution to the frame problem. It states: a fluent that holds at time T continues to hold at T+1 unless an event terminates it. Formally: `holds_at(F, T) ∧ ¬clipped(T, F, T') → holds_at(F, T')` for T < T'. In Cyclops Storm, inertia is implemented implicitly in the `holds_at` algorithm: after finding an initiation time, the system searches for terminating events; if none exist before the query time, the fluent holds. This avoids the need for explicit persistence axioms and makes temporal reasoning tractable.

### Legacy Engine

The **Legacy Engine** is Cyclops Storm's original query evaluator, handling Event Calculus predicates, temporal reasoning, tabling, and belief state management. Unlike the DFS engine (which uses an explicit choice point stack), the Legacy engine uses recursive evaluation with Python generators. All EC predicates (`happens`, `holds_at`, `initiates`, `terminates`, `initially`, `before`) are routed to the Legacy engine, as are queries involving tabling or cutoff time. The Legacy engine also handles cut via `CutSequenceStrategy` and `CutCommit` exceptions, though the routing tables preferentially send cut-containing queries to the DFS engine. Result cleaning uses `_deep_walk` to recursively resolve variables inside compound terms (e.g., cons-cells from recursive list construction), not just top-level variable chains. The term "Legacy" reflects the architectural evolution—newer pure Prolog queries use the faster DFS engine, while the Legacy engine remains essential for EC semantics.

### Provenance

**Provenance** is Cyclops Storm's mechanism for tracking *why* a conclusion holds, not just *that* it holds. The provenance system operates at three levels:

1. **Source attribution**: `fact_id/2` and `supports/2` link facts to source text spans
2. **Rule derivation**: `DerivationRecord` objects document which rules fired and what bindings were used
3. **Temporal reasoning**: `TemporalProvenanceNode` objects trace the Event Calculus chain — which events occurred, which rules fired, which preconditions were satisfied

This supports explainability ("Why does the agent have the key at t5?"), debugging ("Which event caused this unexpected state?"), and narrative generation ("Summarize the agent's actions"). Provenance tracking is a key differentiator from SWI-Prolog, which doesn't provide built-in causal explanation for temporal queries. SWI-Prolog's `prolog_stack/1` shows the call stack during execution, but doesn't produce structured provenance records connecting conclusions to source evidence.

### Stratification

**Stratification** is the layering of predicates by their negation dependencies. A program is *stratifiable* if its predicates can be arranged in layers (strata) such that negation only refers to predicates in lower strata — never to predicates in the same or higher stratum.

```prolog
% Stratifiable (2 strata):
%   Stratum 1: bird/1, penguin/1
%   Stratum 2: flies/1 (negates penguin in stratum 1)
flies(X) :- bird(X), \+ penguin(X).

% Non-stratifiable (odd cycle through negation):
p :- \+ q.
q :- \+ p.   % p and q negate each other — undefined semantics
```

Non-stratifiable programs have undefined NAF semantics — different evaluation orders can produce different results. Cyclops Storm includes a compile-time `StratificationAnalyzer` that detects these cases. SWI-Prolog's well-founded semantics (WFS) can handle some non-stratifiable programs that Cyclops Storm cannot.

### WAM (Warren Abstract Machine)

The **Warren Abstract Machine** is the standard execution model for Prolog implementations, designed by David H.D. Warren in 1983. It compiles Prolog clauses to bytecode for an abstract machine with specialized registers, a trail for undo logging, and efficient first-argument indexing for clause selection. SWI-Prolog uses WAM (with JIT compilation to native code), achieving 100-1000x performance over interpreted approaches. Cyclops Storm does *not* use WAM—it's pure Python with explicit data structures—trading performance for maintainability, debuggability, and seamless Python ecosystem integration.


---

## References

**Cyclops Storm Documentation**:
- `kb/CLAUDE.md` — Project conventions and debugging guide
- `kb/docs/KB_API_AND_DESIGN.md` — API reference and internal design

**SWI-Prolog Resources**:
- SWI-Prolog Manual: https://www.swi-prolog.org/pldoc/doc_for?object=manual

**Research Papers**:
- Mueller, E. T. (2014). *Commonsense Reasoning* (2nd ed.). Morgan Kaufmann. (Event Calculus foundations)
- Shanahan, M. (1999). *The Event Calculus Explained*. AI Review, 13(1), 1-23. (EC semantics)
- Warren, D. H. D. (1983). *An Abstract Prolog Instruction Set*. Technical Note 309, SRI International. (WAM architecture)
- Chen, W., & Warren, D. S. (1996). *Tabled Evaluation with Delaying for General Logic Programs*. JACM. (XSB tabling)

---
**Last Updated**: 2026-03-19
