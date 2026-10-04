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

## 2. Window d2-pm: end extended instead (recorded 2026-10-02T19:44:09+00:00 UTC; supersedes entry 1)

- **Now:** Friday 2 October 2026, 16:00-23:00 (+03:00): the planned afternoon slot with its end moved
  from 21:00 to 23:00. The 23:00-04:00 schedule of entry 1 was never used.
- **Why:** to keep d2-pm an afternoon/evening window, as planned. Still no d2-pm request had been
  issued when this was decided.
- **Consequence:** collection starts after 22:40, so the window is shorter in practice; requests not
  issued by 23:00 are recorded as not collected, as the frozen rules require.

## 3. Window d2-pm: end moved to midnight (recorded 2026-10-02T19:45:22+00:00 UTC; supersedes entry 2)

- **Now:** Friday 2 October 2026, 16:00, to Saturday 3 October, 00:00 (+03:00).
- **Why:** an end at 23:00 left about fifteen minutes, too little for the two slowest models to
  complete the window. When this was decided, 169 d2-pm requests had been issued.

## Correction to the commit message of 67da9c1

That message says no d2-pm request had been issued. In fact the window was already running: 169
d2-pm requests had been issued when the end was moved to midnight, as entry 3 and FREEZE.json record.
The run in progress had loaded the 23:00 end, so it is restarted before 23:00 to load the midnight end;
requests in flight at the restart are recorded as interrupted and are not sent again.

## 4. Window d4-am: start moved to 09:00 (recorded 2026-10-04T06:28:41+00:00 UTC)

- **Planned:** Sunday 4 October 2026, 10:00-15:00 Europe/Kyiv (+03:00).
- **Now:** Sunday 4 October 2026, 09:00-15:00 (+03:00): the start is one hour earlier; the end is unchanged.
- **Why:** at the operator's request, so that the last window could start before 10:00. When this was
  decided (09:28 Kyiv), no d4-am request had been issued, so the decision could not depend on any d4-am
  outcome. The d4-am record file existed but was empty: a start attempt at about 09:26 was refused
  because the window had not opened (the runner creates the file before it checks the time). Windows
  d1-pm, d2-am, d2-pm, d3-am and d3-pm were closed.
- **What changes:** d4-am may begin an hour earlier than the other morning windows; it remains a morning
  window and keeps its identifier, its 1,920 scheduled requests and their randomized order. Nothing else
  in the design, schedule, code or analysis changes.
- **Integrity record:** FREEZE.json now holds the amended design hash and, under "amendments", the
  previous hash (01fc061b0c7fa12d6b4ec3319abd3035c7b7554d67d53dc551e9497e866aacc3), the change and its reason.
