# Deviations from the frozen replication protocol

## 1. Window d2-pm rescheduled (recorded 2026-10-02T19:40:08+00:00 UTC)

- **Planned:** Friday 2 October 2026, 16:00-21:00 Europe/Kyiv (+03:00).
- **Now:** Friday 2 October 2026, 23:00, to Saturday 3 October, 04:00 (+03:00); five hours, as planned.
- **Why:** the operator did not start the window during its slot. When the change was made, no d2-pm
  request had been issued (0 issued, 0 received, no events), so the decision could not depend on any
  d2-pm outcome. Windows d1-pm and d2-am were complete; the pilot runs used separate records.
- **What changes:** d2-pm is collected at night instead of in the afternoon, so the six windows no
  longer alternate strictly morning/afternoon. The window keeps its identifier, its 1,920 scheduled
  requests and their randomized order; nothing else in the design, schedule, code or analysis
  changes.
- **Integrity record:** FREEZE.json now holds the amended design hash and, under "amendments", the
  previous hash (ba5254c8a06746c6c11c4146fc6b2b1de3ed8483d8b6f5964d151987eeafa49d), the change and its reason.
- **Reporting:** the manuscript reports this deviation with the replication results.
