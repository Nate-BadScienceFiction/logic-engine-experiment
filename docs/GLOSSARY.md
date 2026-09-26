# Glossary

Plain-language definitions of the terms used in these pages.

**Atom.** A constant name in Prolog: `alice`, `light_on`, `'Hello'`. Distinct from numbers: `'1'` is an atom, `1` is an integer.

**Backtracking.** When a line of reasoning fails, the engine goes back to the most recent choice it made and tries the next option. This is how Prolog finds every answer.

**Built-in.** A predicate the engine provides rather than one you define: `member/2`, `findall/3`, `is/2`.

**Clause.** A fact or a rule.

**Cut (`!`).** "Commit to the choices made so far." Once a cut runs, Prolog won't try this predicate's remaining clauses, or other answers for the goals before the cut in this clause. Useful, and notoriously easy to get subtly wrong.

**Event Calculus.** A way of reasoning about time, introduced by Kowalski and Sergot in 1986. This engine uses a simplified form from the 1990s. Events *happen* at time points and *initiate* or *terminate* fluents. A fluent keeps holding until something terminates it; that persistence is called *inertia*.

**Fact.** A statement taken as true: `parent(alice, bob).`

**Fluent.** A fact that can change over time: `light_on`, `device_mode(vend_01, offline)`.

**Left recursion.** A rule whose first goal calls the rule itself, as in `path(X,Y) :- path(X,Z), edge(Z,Y).` Plain Prolog loops forever on it; tabling fixes that.

**Mutation testing.** Deliberately breaking the code in small ways to check that some test notices. A test that never goes red can't be protecting anything.

**Negation as failure (`\+`).** `\+ G` succeeds when `G` can't be proven. "Not provable" isn't quite "false," which is why it needs care.

**Oracle.** In testing, the source of truth for expected answers. Here, usually SWI-Prolog.

**Predicate.** A named relation with a number of arguments, written `name/arity`: `parent/2`.

**Prolog.** A logic programming language from 1972. You describe facts and rules, then ask questions; the system searches for answers.

**Provenance.** Where a fact came from. Here, the sentence in the source story that supports it.

**Result status.** In this engine, a label on every result: *complete* (the search finished) or *exhausted* (a budget ran out, so the truth is unknown). A complete result with no answers means "false." It can also mean "no such predicate": by default, unknown predicates quietly fail.

**Rule.** A conditional fact: `ancestor(X, Z) :- parent(X, Y), ancestor(Y, Z).` reads "X is an ancestor of Z if X is a parent of some Y and Y is an ancestor of Z."

**SLD resolution.** The standard way Prolog executes: take the first goal, find a matching clause, replace the goal with that clause's body, and repeat, backtracking on failure.

**Stratification.** A check that no predicate depends on its own negation, directly or indirectly. A program that passes has a single intended model, meaning one agreed set of true facts. This engine refuses programs that don't pass.

**SWI-Prolog.** A widely used, mature, free Prolog system. It's used here as the referee.

**Tabling.** Remembering the answers to a subgoal and reusing them. Recursive rules that would otherwise loop forever then finish with every answer, as long as there are finitely many different calls and answers.

**Unification.** Making two terms equal by binding variables: `parent(X, bob)` unifies with `parent(alice, bob)` by setting `X = alice`.

**Variable.** A placeholder, written with a capital letter or underscore: `X`, `Who`, `_`.
