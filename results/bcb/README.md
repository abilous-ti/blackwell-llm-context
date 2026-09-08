# BigCodeBench pilot: does the partial order show up on natural tasks?

A pilot, not a headline result. It asks whether the paper's structure survives when
the two sources are documentation of **real library APIs** on **real benchmark tasks**
with **the benchmark's own executable tests**, instead of two hand-built notes.

## The obstacle, and two ways round it

BigCodeBench tests check the behaviour of `task_func`, not which API produced it, so
renaming a library alone makes no convention decisive: a solution can ignore the doc,
import the real library and still pass. Two designs fix that:

- **sandbox**  the solution may not import the real library (enforced statically; a
  `meta_path` blocker is not enough because a function-body import evades it). The
  renamed shim `qx7` is the only route. The task's own test runs unchanged.
- **contract** task and test untouched; the solution must additionally register a
  private token through `qx7`, checked by one appended assertion.

## Screening

The first round failed for a reason worth recording: base solve rates were 20-50%,
so nothing had room to collapse. Screening 82 tasks with no context at n=3 showed a
bimodal distribution (0.0 or 1.0), and the 22 tasks at 100% became the pilot set.

## Result (DeepSeek-V4-Pro, 22 tasks, 4 arms)

| design | side | none | W_PD | W_SC | both |
|---|---|---|---|---|---|
| sandbox | pandas | 0/12 | 6/12 | 0/12 | 2/12 |
| sandbox | scipy | 0/10 | 0/10 | 2/10 | 3/10 |
| contract | pandas | 0/12 | 3/12 | 0/12 | 0/12 |
| contract | scipy | 0/10 | 0/10 | 5/10 | 3/10 |

Both designs show the double crossover and a superset collapse, with `none` at zero
on tasks the model otherwise solves 100% of the time. The two designs make the
convention decisive by different mechanisms (blocked access vs private token), so the
structure is not an artifact of either.

Magnitudes are far below the hand-built cells: writing correct code through an
unfamiliar renamed API costs accuracy, and 62 of 88 contract failures are the task
itself failing rather than the convention. Treat this as evidence the construction
transfers, not as a measurement of how strong the effect is in the wild.
