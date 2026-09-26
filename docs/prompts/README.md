# The three prompts behind the rewrite

In September 2026 I wrote three prompts, about 540 lines in all, and had AI agents build and then audit a new engine from them. They are reproduced here as I wrote them. [HISTORY.md](../HISTORY.md#5-starting-over-september-2026) tells what happened next.

| # | Date | Prompt | What it asks for | Words |
|---|---|---|---|---:|
| 1 | Sep 13 | [Design brief](1-design-brief-2026-09-13.md) | Build a ground-up successor to the earlier engine: goals and non-goals, an adversarial architecture review, then a runnable, tested first slice | 1,983 |
| 2 | Sep 14 | [Test-migration audit](2-test-migration-audit-2026-09-14.md) | Give every one of the old engine's tests a disposition, check each for relevance and strength, and fill gaps from the new code outward | 1,638 |
| 3 | Sep 15 | [Two-way audit of code and tests](3-two-way-audit-2026-09-15.md) | Trace every test to the behavior it claims to check and every component to the tests that should protect it; review the fix plan adversarially; show that critical tests catch plausible bugs | 1,630 |

**Where they come from.** `prompt.md` in the rewrite's repository, AkiyaBlocks-CyclopsStorm (private for now), grew by one prompt a day: commits `f575672` (Sep 13), `467dbb8` (Sep 14) and `beb6179` (Sep 15). The copies here change only formatting, and replace local folder paths with repository names.
