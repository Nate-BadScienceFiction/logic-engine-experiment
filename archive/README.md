# Archive

Older material from this repository, kept for the record. **It describes the earlier engine as it was in spring 2026, not the current one.** Several architecture details and a few claims in it were wrong, or became wrong. See [HISTORY.md](../docs/HISTORY.md) for what happened and [ENGINE.md](../docs/ENGINE.md) for the current engine.

| File | What it is | Read it for |
|---|---|---|
| `README-2026-05-28.md` | The project page as of May 2026: status notes, article list, charts | The project as it presented itself then |
| `KB_API_AND_DESIGN-2026-04.md` | API and internals of the earlier engine, April 9, 2026 | Its teaching examples (negation, the Event Calculus location example, tabling a cycle), which still run. The architecture sections are superseded |
| `KB_ARCHITECTURE_VS_SWI_PROLOG-2026-04.md` | A comparison with SWI-Prolog, April 9, 2026 | The "why logic programming" section. Its comparisons were not checked against a running SWI, and some are wrong |
| `ANALYZE_CODE_ALGORITHM_DESCRIPTION.md` | How the code-analysis tool that mapped the codebase for the agents worked (v1.3, Dec 2025) | A side experiment in giving agents a map of a large codebase |
| `charts/` | The unit-test chart (May 2026), the code-change chart (Apr 2026), the story-graph ("Spider's Eye") screenshot, and a static image of the function-topology chart | The development record as charted at the time |
| `harriets-world-narrative.pl` | An excerpt of a story model (a memory-plague epidemic), extracted from story prose by an LLM | An example of story-as-facts. It has known gaps: undeclared time points, one undefined name |

Removed from the repository rather than archived:

- the 25 MB code-analysis dump that fed the old charts, which described the superseded engine;
- the 5.6 MB interactive chart built from that dump.
