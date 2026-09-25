# Analyze Code Utility - Algorithm Description

**Author:** Claude Code

**Version:** 1.3

This document describes the algorithms used in `analyze_code_utility.py` for static Python code analysis.

---

## Table of Contents

1. [Cyclomatic Complexity](#1-cyclomatic-complexity)
2. [Symbol Resolution](#2-symbol-resolution)
3. [IO Boundary Detection](#3-io-boundary-detection)
4. [Blast Radius Calculation](#4-blast-radius-calculation)
5. [Priority Score Calculation](#5-priority-score-calculation)
6. [Purity Heuristic](#6-purity-heuristic)
7. [Data Flow Type Classification](#7-data-flow-type-classification)
8. [Exception Flow Analysis](#8-exception-flow-analysis)
9. [Convergence Score (Data Bottleneck Detection)](#9-convergence-score-data-bottleneck-detection)
10. [Type Transformation Detection](#10-type-transformation-detection)
11. [Call Graph Construction](#11-call-graph-construction)
12. [Local Variable Collection](#12-local-variable-collection)
13. [Call Source Classification](#13-call-source-classification)
14. [Fidelity Metrics](#14-fidelity-metrics)
15. [Feature Flags System](#15-feature-flags-system)
16. [Computational Complexity Summary](#16-computational-complexity-summary)

**Appendix:**
- [A. Output Schema Reference](#appendix-a-output-schema-reference)

---

## 1. Cyclomatic Complexity

**Purpose:** Measures the number of linearly independent paths through a function's code.

**Schema output:** `functions[].complexity` (see [Appendix A.3](#a3-functioninfo-schema))

### Algorithm

```
CYCLOMATIC_COMPLEXITY(node) =
    1 + COUNT(If) + COUNT(For) + COUNT(AsyncFor) + COUNT(While) +
    COUNT(ExceptHandler) + COUNT(IfExp) + COUNT(Assert) +
    SUM(BoolOp_branches) + SUM(Comprehension_complexity) + SUM(Match_cases)

Where:
    BoolOp_branches = |operands| - 1  for each BoolOp (and/or)
    Comprehension_complexity = 1 + |if_clauses|  per generator
    Match_cases = |cases| - 1  (Python 3.10+)
```

### Formal Definition

Let `G = (V, E)` be the control flow graph of a function where:
- `V` = set of basic blocks
- `E` = set of control flow edges

```
CC(G) = |E| - |V| + 2P

Simplified (single component):
CC = 1 + D

Where D = number of decision points
```

### Implementation Mapping

| AST Node | Complexity Contribution |
|----------|------------------------|
| `If` | +1 |
| `For` | +1 |
| `AsyncFor` | +1 |
| `While` | +1 |
| `ExceptHandler` | +1 |
| `BoolOp (and/or)` | +(n-1) where n = number of operands |
| `IfExp` (ternary) | +1 |
| `Assert` | +1 |
| `ListComp/SetComp/DictComp/GeneratorExp` | +1 per generator, +1 per if-clause |
| `Match` (Python 3.10+) | +(n-1) where n = number of cases |

---

## 2. Symbol Resolution

**Purpose:** Maps local call names to fully qualified module paths.

**Schema output:** `functions[].resolved_calls`, `functions[].unresolved_calls` (see [Appendix A.3](#a3-functioninfo-schema))

### Algorithm

```
RESOLVE_CALL(call_name, symbol_table) -> (resolved_name, is_resolved)

Input: call_name = "func" or "module.func" or "self.method" or "super().method"
Output: fully qualified name or None

1. SPLIT call_name into parts by "."
2. IF single part (simple name):
   a. CHECK from_imports[name] -> return if found
   b. CHECK imports[name] -> return if found
   c. CHECK local_defs[module.name] -> return if found
   d. CHECK class_methods[current_class][name] -> return if found
3. ELSE (dotted name with 2+ parts):
   base = parts[0], method = parts[1], rest = parts[2:]

   a. IF base == current_self_name AND current_class:
      # Handle self.method() and cls.method()
      IF method in class_methods[current_class]:
          RETURN module.class.method[.rest]

   b. IF base == "super" AND current_class:
      # Handle super().method() - resolve to current class
      IF method in class_methods[current_class]:
          RETURN module.class.method

   c. IF base in imports: return imports[base] + "." + method[.rest]
   d. IF base in from_imports: return from_imports[base] + "." + method[.rest]

4. RETURN (None, False) if unresolved
```

### Resolution Priority

```
Priority Order:
1. from_imports (highest - most specific)
2. regular imports
3. local definitions
4. class methods (if inside class context)
5. self/cls method calls (method resolution within class)
6. super() calls (parent class method resolution)
```

### Self/Cls Tracking

```
When entering a method:
    IF is_method AND first_param in ('self', 'cls'):
        symbol_table.current_self_name = first_param
    ELSE:
        symbol_table.current_self_name = None
```

---

## 3. IO Boundary Detection

**Purpose:** Identifies function calls that perform I/O, network, database, or non-deterministic operations.

**Schema output:** `functions[].boundary_flags`, `functions[].io_label` (see [Appendix A.3](#a3-functioninfo-schema))

### Algorithm

```
DETECT_IO_CALL(detection_name) -> Set[boundary_flags]

# Use resolved name when available for accurate detection
detection_name = resolved_name IF is_resolved ELSE raw_call_name

boundary_flags in {"io", "net", "db", "datetime", "random"}

For each prefix_set P:
    IF detection_name.startswith(any prefix in P):
        ADD corresponding flag to result
```

**Note:** Using the resolved name catches aliased imports like `import requests as req`
where `req.get()` would otherwise not be detected.

### Prefix Categories

| Flag | Prefixes |
|------|----------|
| `io` | `open`, `file`, `io`, `pathlib`, `os.path`, `shutil`, `tempfile`, `requests`, `urllib`, `http`, `httpx`, `aiohttp`, `sqlite3`, `psycopg2`, `pymongo`, `sqlalchemy`, `socket`, `ssl`, `ftplib`, `smtplib`, `subprocess`, `os.system`, `os.popen` |
| `net` | `requests`, `urllib`, `http`, `httpx`, `aiohttp`, `socket`, `ssl`, `ftplib`, `smtplib`, `telnetlib`, `poplib`, `imaplib` |
| `db` | `sqlite3`, `psycopg2`, `pymongo`, `sqlalchemy`, `redis`, `mysql`, `cx_Oracle`, `pymssql`, `cassandra` |
| `datetime` | `datetime`, `time`, `calendar`, `dateutil`, `arrow`, `pendulum` |
| `random` | `random`, `secrets`, `uuid`, `numpy.random` |

---

## 4. Blast Radius Calculation

**Purpose:** Measures the transitive impact of changes to a function by counting all functions that could be affected.

**Schema output:** `functions[].blast_radius` (see [Appendix A.3](#a3-functioninfo-schema))

### Algorithm (BFS)

```
BLAST_RADIUS(func_name) -> int:
    # Check cache first
    IF func_name in cache: RETURN cache[func_name]

    # BFS with fresh visited set for each function
    # (no shared state to avoid undercounting)
    visited = {func_name}
    queue = deque([func_name])

    WHILE queue NOT empty:
        current = queue.pop_front()
        FOR each caller in reverse_call_graph[current]:
            IF caller NOT in visited:
                visited.add(caller)
                queue.append(caller)

    # Result is reachable set size minus self
    radius = |visited| - 1
    cache[func_name] = radius
    RETURN radius
```

### Formal Definition

Let `RCG` be the reverse call graph (edges from callees to callers):

```
BlastRadius(f) = |ReachableSet(f, RCG)| - 1

Where:
ReachableSet(f, G) = {v in V : there exists path from f to v in G}
```

### Complexity

```
Time:  O(V + E) per function, amortized O(1) with cache
Space: O(V) for visited set and cache
```

**Note:** Each function gets a fresh visited set to ensure accurate counts.

---

## 5. Priority Score Calculation

**Purpose:** Ranks functions by risk/importance for testing and review.

**Schema output:** `functions[].priority_score` (see [Appendix A.3](#a3-functioninfo-schema))

### Formula

```
PRIORITY_SCORE(func) =
    W_fail * fail_call_count +
    W_fan_in * log(1 + fan_in) +
    W_fan_out * log(1 + fan_out) +
    W_complexity * complexity

Where (current weights):
    W_fail = 12      (test failure weight - placeholder, currently 0)
    W_fan_in = 6     (incoming call importance)
    W_fan_out = 3    (outgoing dependency)
    W_complexity = 2 (code complexity)
```

### Expanded Form

```
priority_score = 0 * 12 + 6 * log(1 + fan_in) + 3 * log(1 + fan_out) + 2 * complexity

# Using log1p for numerical stability:
priority_score = 6 * log1p(fan_in) + 3 * log1p(fan_out) + 2 * complexity
```

---

## 6. Purity Heuristic

**Purpose:** Estimates whether a function has side effects.

**Schema output:** `functions[].purity_heuristic` (see [Appendix A.3](#a3-functioninfo-schema))

### Algorithm

```
IS_PURE(func) =
    |writes_globals| = 0 AND
    |writes_attrs| = 0 AND
    |boundary_flags| = 0
```

### Interpretation

| Condition | Meaning |
|-----------|---------|
| `writes_globals = {}` | Does not modify global variables |
| `writes_attrs = {}` | Does not modify object attributes |
| `boundary_flags = {}` | Does not perform I/O, network, DB, or non-deterministic operations |

---

## 7. Data Flow Type Classification

**Purpose:** Categorizes functions by their data transformation pattern.

**Schema output:** `functions[].data_flow_type` (see [Appendix A.3](#a3-functioninfo-schema))

### Decision Tree

```
CLASSIFY_DATA_FLOW(func):

    IF contains(Yield | YieldFrom):
        RETURN "generator"

    IF NOT contains(Return):
        RETURN "sink"

    IF returns_input AND NOT modifies_params:
        RETURN "pass-through"

    IF returns_input AND modifies_params:
        RETURN "transformer"

    IF |params| > 2:  # More than self + one param
        RETURN "aggregator"

    IF has_return AND NOT returns_input:
        RETURN "generator"

    DEFAULT:
        RETURN "transformer"
```

### Type Definitions

| Type | Description |
|------|-------------|
| `generator` | Creates new data, contains yield, or returns non-input values |
| `sink` | Consumes data without returning (no return statements) |
| `pass-through` | Returns input unchanged |
| `transformer` | Modifies and returns input data |
| `aggregator` | Combines multiple inputs (>2 parameters) |

---

## 8. Exception Flow Analysis

**Purpose:** Tracks how exceptions propagate through the call graph.

**Schema output:** `exception_flow`, `functions[].raises`, `functions[].catches_exceptions`, `functions[].exception_handlers` (see [Appendix A.1](#a1-top-level-structure) and [A.3](#a3-functioninfo-schema))

### Algorithm: Exception Propagation Tracing

```
TRACE_EXCEPTION_PROPAGATION(start_func, exc_type):
    # Iterative BFS to avoid stack overflow

    seen = global cache of (exc_type, func) pairs
    IF (exc_type, start_func) in seen: RETURN
    ADD (exc_type, start_func) to seen

    queue = [start_func]
    visited = {start_func}

    WHILE queue NOT empty:
        current = queue.pop_front()

        FOR each caller in reverse_call_graph[current]:
            IF caller in visited OR (exc_type, caller) in seen:
                CONTINUE

            IF caller handles exc_type without re-raising:
                CONTINUE  # Exception is caught here

            # Exception propagates to caller
            ADD edge (current -> caller) to propagation_chains[exc_type]
            ADD caller to visited and seen
            ADD caller to queue
```

### Exception Handler Analysis

```
HANDLER_RE_RAISES(handler) =
    exists stmt in handler.body where:
        stmt is Raise AND (
            stmt.exc is None  OR  # bare raise
            stmt.exc.id = handler.name  # explicit re-raise
        )
```

---

## 9. Convergence Score (Data Bottleneck Detection)

**Purpose:** Identifies functions that many other functions depend on.

**Schema output:** `functions[].convergence_score`, `data_flow.bottlenecks` (see [Appendix A.1](#a1-top-level-structure) and [A.3](#a3-functioninfo-schema))

### Formula

```
CONVERGENCE_SCORE(func) = fan_in = |{g : g calls func}|

IS_BOTTLENECK(func) = CONVERGENCE_SCORE(func) >= threshold

Where threshold = 5 (default)
```

### Bottleneck List

```
bottlenecks = SORT_BY(
    {func : CONVERGENCE_SCORE(func) >= 5},
    key = convergence_score,
    order = descending
)[:10]  # Top 10 bottlenecks
```

---

## 10. Type Transformation Detection

**Purpose:** Identifies data type transformation patterns from function signatures.

**Schema output:** `functions[].transforms_types`, `data_flow.type_transformation_chains` (see [Appendix A.1](#a1-top-level-structure) and [A.3](#a3-functioninfo-schema))

### Algorithm

```
EXTRACT_TYPE_TRANSFORMATIONS(signature):
    transformations = []

    return_type = signature.return_annotation
    IF return_type is None: RETURN []

    FOR each param_type in signature.param_annotations:
        IF param_type is None: CONTINUE

        # Pattern matching on type annotations
        IF "dict" in return_type AND "str" in param_type:
            ADD "str -> dict"
        ELIF "str" in return_type AND "dict" in param_type:
            ADD "dict -> str"
        ELIF "list" in return_type AND "dict" in param_type:
            ADD "dict -> list"
        ELIF "dict" in return_type AND "list" in param_type:
            ADD "list -> dict"
        ELIF "str" in return_type AND "list" in param_type:
            ADD "list -> str"

    RETURN transformations
```

---

## 11. Call Graph Construction

**Purpose:** Builds forward and reverse call relationships.

**Schema output:** `call_graph`, `reverse_call_graph` (see [Appendix A.1](#a1-top-level-structure))

### Data Structures

```
call_graph: Dict[caller, Set[callee]]
    call_graph[f] = {g : f calls g}

reverse_call_graph: Dict[callee, Set[caller]]
    reverse_call_graph[g] = {f : f calls g}
```

### Construction

```
BUILD_CALL_GRAPH(functions):
    FOR each (func_name, func_data) in functions:
        FOR each called in func_data.resolved_calls:
            call_graph[func_name].add(called)
            reverse_call_graph[called].add(func_name)
```

---

## 12. Local Variable Collection

**Purpose:** Accurately distinguish local variables from true globals.

**Schema output:** `functions[].reads_globals`, `functions[].writes_globals`, `functions[].reads_nonlocals`, `functions[].writes_nonlocals` (see [Appendix A.3](#a3-functioninfo-schema))

### Algorithm

```
COLLECT_LOCALS(function_node, param_names):
    locals = set(param_names)
    explicit_globals = set()
    explicit_nonlocals = set()

    VISIT all nodes in function:
        IF node is Global:
            ADD names to explicit_globals
            REMOVE from locals
        IF node is Nonlocal:
            ADD names to explicit_nonlocals
            REMOVE from locals
        IF node is Assign/AnnAssign/AugAssign:
            COLLECT target names into locals (if not explicit global/nonlocal)
        IF node is For/AsyncFor:
            COLLECT loop target into locals
        IF node is With/AsyncWith:
            COLLECT as-binding into locals
        IF node is ExceptHandler:
            ADD handler name to locals
        IF node is NamedExpr (:=):
            ADD target to locals
        IF node is ListComp/SetComp/DictComp/GeneratorExp:
            COLLECT comprehension variables into locals

    RETURN (locals, explicit_globals, explicit_nonlocals)
```

---

## 13. Call Source Classification

**Purpose:** Classify calls as stdlib, third-party, or local.

**Schema output:** `functions[].call_sources`, `functions[].external_dependencies` (see [Appendix A.3](#a3-functioninfo-schema))

### Algorithm

```
CLASSIFY_CALL_SOURCE(resolved_name, raw_name, module_name):
    name = resolved_name if resolved_name else raw_name
    IF not name: RETURN "unknown"

    top_module = name.split('.')[0]

    # Check local (same project)
    IF module_name:
        module_root = module_name.split('.')[0]
        IF top_module == module_root: RETURN "local"

    # Check stdlib (lazy-loaded for performance)
    IF top_module in _get_stdlib_modules(): RETURN "stdlib"

    # Check local prefix match
    IF name.startswith(module_name + '.'): RETURN "local"

    RETURN "third_party"
```

---

## 14. Fidelity Metrics

**Purpose:** Track analysis quality for self-auditing.

**Schema output:** `metadata.fidelity_metrics` (see [Appendix A.1](#a1-top-level-structure))

### Tracked Metrics

| Metric | Description |
|--------|-------------|
| `files_attempted` | Total files discovered |
| `files_analyzed` | Successfully parsed files |
| `files_failed` | Parse failures |
| `parse_success_rate` | files_analyzed / files_attempted |
| `syntax_errors` | Count of syntax errors |
| `read_failures` | Count of read failures |
| `total_calls` | Total function calls found |
| `unresolved_calls` | Calls that couldn't be resolved |
| `call_resolution_rate` | (total - unresolved) / total |
| `enhanced_analysis_failures` | CFG/cognitive complexity failures |

### Formula

```
parse_success_rate = files_analyzed / max(1, files_attempted)
call_resolution_rate = (total_calls - unresolved_calls) / max(1, total_calls)
```

---

## 15. Feature Flags System

**Purpose:** Control which analysis features are enabled.

### Command Line Options

```
--features {basic,full}   Global mode selector (default: basic)
--enable FEATURE          Enable specific feature (repeatable)
--no-schema-header        Output valid JSON without schema comments
```

### Feature Gating

```
_is_feature_enabled(feature) =
    features == "full" OR feature in enabled_features
```

### Available Features

| Feature | Description | Enabled By |
|---------|-------------|------------|
| `cfg` | Control flow graph generation | `--features full` or `--enable cfg` |
| `deadcode` | Dead code analysis | `--features full` or `--enable deadcode` |
| `exception_flow` | Exception propagation analysis | `--features full` or `--enable exception_flow` |

---

## 16. Computational Complexity Summary

| Algorithm | Time | Space |
|-----------|------|-------|
| Cyclomatic Complexity | O(N) per function | O(1) |
| Symbol Resolution | O(1) average | O(I) where I = imports |
| IO Detection | O(P) where P = prefixes | O(1) |
| Blast Radius | O(V+E) with cache | O(V) |
| Exception Flow | O(V+E) per exception | O(V) |
| Call Graph Build | O(F*C) | O(F*C) |
| Local Variable Collection | O(N) per function | O(L) where L = locals |
| Source Classification | O(1) per call | O(1) |

Where:
- N = AST nodes in function
- V = number of functions
- E = number of call edges
- F = number of functions
- C = average calls per function
- L = local variables in function

---

# Appendix A: Output Schema Reference

The analyzer produces a JSON fact pack. Use `--no-schema-header` for valid JSON output suitable for programmatic parsing.

## A.1 Top-Level Structure

```json
{
  "metadata": { ... },
  "files": { "<module_name>": <FileInfo> },
  "functions": { "<qualified_name>": <FunctionInfo> },
  "call_graph": { "<caller>": ["<callees>"] },
  "reverse_call_graph": { "<callee>": ["<callers>"] },
  "exception_flow": { ... },
  "data_flow": { ... },
  "dead_code_analysis": { ... }
}
```

### metadata

| Field | Type | Algorithm Reference |
|-------|------|---------------------|
| `version` | string | Schema version |
| `generated_by` | string | Generator identifier |
| `total_files` | int | File count |
| `total_functions` | int | Function count |
| `enhanced_analysis_enabled` | bool | CFG availability |
| `fidelity_metrics` | object | See [Section 14](#14-fidelity-metrics) |

### fidelity_metrics

| Field | Type | Algorithm Reference |
|-------|------|---------------------|
| `files_attempted` | int | [Section 14](#14-fidelity-metrics) |
| `files_analyzed` | int | [Section 14](#14-fidelity-metrics) |
| `files_failed` | int | [Section 14](#14-fidelity-metrics) |
| `parse_success_rate` | float | [Section 14](#14-fidelity-metrics) |
| `syntax_errors` | int | [Section 14](#14-fidelity-metrics) |
| `read_failures` | int | [Section 14](#14-fidelity-metrics) |
| `total_calls` | int | [Section 14](#14-fidelity-metrics) |
| `unresolved_calls` | int | [Section 14](#14-fidelity-metrics) |
| `call_resolution_rate` | float | [Section 14](#14-fidelity-metrics) |
| `enhanced_analysis_failures` | int | [Section 14](#14-fidelity-metrics) |
| `complex_signature_fields` | int | Signature parsing failures |
| `failed_files` | List[string] | Paths of failed files |

### exception_flow

| Field | Type | Algorithm Reference |
|-------|------|---------------------|
| `exception_sinks` | List[string] | [Section 8](#8-exception-flow-analysis) |
| `exception_sources` | List[string] | [Section 8](#8-exception-flow-analysis) |
| `propagation_chains` | Dict[string, List] | [Section 8](#8-exception-flow-analysis) |

### data_flow

| Field | Type | Algorithm Reference |
|-------|------|---------------------|
| `bottlenecks` | List[BottleneckInfo] | [Section 9](#9-convergence-score-data-bottleneck-detection) |
| `type_transformation_chains` | List[ChainInfo] | [Section 10](#10-type-transformation-detection) |

---

## A.2 FileInfo Schema

| Field | Type | Description |
|-------|------|-------------|
| `module` | string | Dotted module name |
| `file_path` | string | Absolute file path |
| `imports` | Dict[str, str] | alias -> real module name |
| `exports` | List[str] | Top-level definitions |
| `classes` | Dict[str, ClassInfo] | Class definitions |

---

## A.3 FunctionInfo Schema

### Basic Information

| Field | Type | Description | Algorithm Reference |
|-------|------|-------------|---------------------|
| `name` | string | Simple function name | - |
| `qualname` | string | Fully qualified name | - |
| `module` | string | Module name | - |
| `class` | string? | Class name if method | - |
| `is_method` | bool | True if class method | - |
| `is_async` | bool | True if async function | - |
| `is_generator` | bool | True if contains yield | [Section 7](#7-data-flow-type-classification) |
| `is_test` | bool | True if test function | - |

### Signature and Location

| Field | Type | Description | Algorithm Reference |
|-------|------|-------------|---------------------|
| `signature` | SignatureInfo | Parameter and return info | - |
| `decorators` | List[str] | Decorator names | - |
| `pytest_marks` | List[str] | pytest mark decorators | - |
| `fixtures_used` | List[str] | Test fixture parameters | - |
| `file_rel_path` | string | Relative file path | - |
| `start_line` | int | Line number | - |

### Complexity Metrics

| Field | Type | Description | Algorithm Reference |
|-------|------|-------------|---------------------|
| `complexity` | int | Cyclomatic complexity | [Section 1](#1-cyclomatic-complexity) |
| `purity_heuristic` | bool | True if appears pure | [Section 6](#6-purity-heuristic) |

### Call Relationships

| Field | Type | Description | Algorithm Reference |
|-------|------|-------------|---------------------|
| `calls` | List[str] | Raw call names | - |
| `resolved_calls` | List[str] | Fully qualified call names | [Section 2](#2-symbol-resolution) |
| `unresolved_calls` | List[str] | Unresolved call names | [Section 2](#2-symbol-resolution) |
| `recursive` | bool | True if self-recursive | - |
| `call_sources` | Dict[str,str] | call_name -> 'stdlib' \| 'third_party' \| 'local' | [Section 13](#13-call-source-classification) |
| `external_dependencies` | List[str] | Third-party calls with boundary flags | [Section 13](#13-call-source-classification) |

### Exception Handling

| Field | Type | Description | Algorithm Reference |
|-------|------|-------------|---------------------|
| `raises` | List[str] | Exception types raised | [Section 8](#8-exception-flow-analysis) |
| `catches_exceptions` | List[str] | Exception types caught | [Section 8](#8-exception-flow-analysis) |
| `swallows_exceptions` | bool | Catches without re-raising | [Section 8](#8-exception-flow-analysis) |
| `exception_handlers` | List[HandlerInfo] | Exception handler details | [Section 8](#8-exception-flow-analysis) |
| `exception_propagation` | List[str] | Bubbling exceptions from callees | [Section 8](#8-exception-flow-analysis) |

### Variable Access

| Field | Type | Description | Algorithm Reference |
|-------|------|-------------|---------------------|
| `reads_globals` | List[str] | Global variables read (excludes locals/builtins) | [Section 12](#12-local-variable-collection) |
| `writes_globals` | List[str] | Global variables written (explicit global only) | [Section 12](#12-local-variable-collection) |
| `reads_nonlocals` | List[str] | Nonlocal variables read | [Section 12](#12-local-variable-collection) |
| `writes_nonlocals` | List[str] | Nonlocal variables written | [Section 12](#12-local-variable-collection) |
| `reads_attrs` | List[str] | Attributes read | - |
| `writes_attrs` | List[str] | Attributes written | - |

### Boundary Detection

| Field | Type | Description | Algorithm Reference |
|-------|------|-------------|---------------------|
| `boundary_flags` | List[str] | IO/net/db/datetime/random flags | [Section 3](#3-io-boundary-detection) |
| `io_label` | bool | True if performs IO | [Section 3](#3-io-boundary-detection) |

### Centrality Metrics

| Field | Type | Description | Algorithm Reference |
|-------|------|-------------|---------------------|
| `fan_in` | int | Number of callers | [Section 11](#11-call-graph-construction) |
| `fan_out` | int | Number of callees | [Section 11](#11-call-graph-construction) |
| `blast_radius` | int | Transitive caller count | [Section 4](#4-blast-radius-calculation) |
| `priority_score` | float | Risk/priority score | [Section 5](#5-priority-score-calculation) |
| `convergence_score` | int | Same as fan_in | [Section 9](#9-convergence-score-data-bottleneck-detection) |

### Data Flow Analysis

| Field | Type | Description | Algorithm Reference |
|-------|------|-------------|---------------------|
| `data_flow_type` | string | transformer/pass-through/generator/aggregator/sink | [Section 7](#7-data-flow-type-classification) |
| `transforms_types` | List[str] | Type transformation patterns | [Section 10](#10-type-transformation-detection) |
| `modifies_parameters` | bool | Modifies mutable params | [Section 7](#7-data-flow-type-classification) |

---

## A.4 Boundary Flags Reference

| Flag | Description |
|------|-------------|
| `io` | File/stream operations (open, read, write) |
| `net` | Network operations (requests, http, socket) |
| `db` | Database operations (sqlite3, sqlalchemy) |
| `datetime` | Time-dependent operations (datetime, time) |
| `random` | Non-deterministic operations (random, uuid) |

---

## A.5 Data Flow Types Reference

| Type | Description |
|------|-------------|
| `transformer` | Modifies and returns input data |
| `pass-through` | Returns input unchanged |
| `generator` | Creates new data (doesn't return input) |
| `aggregator` | Combines multiple inputs into output |
| `sink` | Consumes data without returning (no return statements) |
