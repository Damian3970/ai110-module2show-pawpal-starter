# PawPal+ Scheduler — Test Plan

Test plan for the pet scheduler logic in `pawpal_system.py`, focused on
**sorting**, **conflict detection**, **recurring tasks**, and
**daily plan generation** under a time budget.

Legend: 🟢 = happy path, 🟠 = edge case.

---

## 1. Priority sorting — `sort_tasks_by_priority()`

| # | Type | Scenario | Expected |
|---|------|----------|----------|
| 1.1 | 🟢 | Mix of High/Medium/Low | Order High → Medium → Low |
| 1.2 | 🟢 | Same priority, different durations | Shorter task comes first (density tiebreak) |
| 1.3 | 🟠 | **Empty list** | Returns `[]`, no error |
| 1.4 | 🟠 | Single task | Returns that one task |
| 1.5 | 🟠 | Two tasks, identical priority **and** duration | Both present; stable order preserved |
| 1.6 | 🟠 | Unknown priority string (`"Urgent"`, `""`, `"HIGH "`) | Ranks last (99); trimmed/case-insensitive `"HIGH "` still ranks High |
| 1.7 | 🟠 | Input list must not be mutated | Original list unchanged (new list returned) |

## 2. Time sorting — `sort_by_time()`

| # | Type | Scenario | Expected |
|---|------|----------|----------|
| 2.1 | 🟢 | Distinct times `08:30`, `12:00`, `18:45` | Earliest → latest |
| 2.2 | 🟠 | Non-padded time `9:00` vs `10:00` | `9:00` sorts **before** `10:00` (numeric, not lexicographic) |
| 2.3 | 🟠 | **Two tasks at the exact same time** | Both retained; no crash; order stable |
| 2.4 | 🟠 | Task with no time (`""`) | Sorts **last** (treated as 24:00) |
| 2.5 | 🟠 | Malformed time (`"9"`, `"24:99"`, `"noon"`) | Sorts last; never raises |
| 2.6 | 🟠 | Midnight boundary `00:00` and `23:59` | `00:00` first, `23:59` last |

## 3. Conflict detection — `find_conflicts()` / `check_conflicts()`

| # | Type | Scenario | Expected |
|---|------|----------|----------|
| 3.1 | 🟢 | Non-overlapping tasks back-to-back (`08:00+30`, `08:30+30`) | **No conflict** (end == next start is allowed) |
| 3.2 | 🟠 | **Two tasks at the exact same time** | Reported as a conflict |
| 3.3 | 🟠 | Partial overlap (`08:00+60` vs `08:30+15`) | Reported as a conflict |
| 3.4 | 🟠 | Fully nested (`08:00+60` contains `08:15+10`) | Reported as a conflict |
| 3.5 | 🟢 | Overlap across **different pets** | Still a conflict (one owner can't be in two places) |
| 3.6 | 🟠 | Overlap within the **same pet** | Conflict flagged; `Conflict.same_pet` is `True` |
| 3.7 | 🟠 | Tasks with no time set | Ignored (not compared) |
| 3.8 | 🟠 | Three tasks all overlapping | All pairwise conflicts reported (3 pairs) |
| 3.9 | 🟠 | `check_conflicts()` with corrupt data | Returns soft warning string, **never raises** |
| 3.10 | 🟢 | No conflicts | `check_conflicts()` returns `""` (falsy) |
| 3.11 | 🟠 | Midnight wrap end time (`23:30 + 45`) in `describe()` | End shows `00:15` |

## 4. Recurring tasks — `next_occurrence()` / `mark_complete()`

| # | Type | Scenario | Expected |
|---|------|----------|----------|
| 4.1 | 🟢 | Daily task with `due_date` | Next occurrence due `+1 day` |
| 4.2 | 🟢 | Weekly task with `due_date` | Next occurrence due `+7 days` |
| 4.3 | 🟠 | Recurrence `"none"` | `next_occurrence()` returns `None` |
| 4.4 | 🟠 | Unknown recurrence (`"monthly"`, `"DAILY "`, casing) | `"monthly"` → `None`; `"DAILY "` still resolves to daily |
| 4.5 | 🟠 | No `due_date` set | Falls back to `date.today()` as base |
| 4.6 | 🟠 | **Month / year / leap-year rollover** (`2026-01-31 +1d → 2026-02-01`; `2024-02-28 +1d → 2024-02-29`) | Date arithmetic rolls over correctly |
| 4.7 | 🟢 | `mark_complete()` on recurring task attached to a pet | Original marked complete; **new occurrence added to same pet** |
| 4.8 | 🟠 | `mark_complete()` on recurring task with **no owner pet** | Marked complete; occurrence returned but **not** attached anywhere |
| 4.9 | 🟠 | `mark_complete()` on one-off task | Marked complete; returns `None`; pet's task count unchanged |
| 4.10 | 🟠 | New occurrence starts incomplete/unscheduled | `is_complete=False`, `is_scheduled=False` |
| 4.11 | 🟠 | Completed late (due_date in the past) | Next date advances from `due_date`, not today — no skipped cycle |

## 5. Daily plan generation — `generate_daily_plan()`

| # | Type | Scenario | Expected |
|---|------|----------|----------|
| 5.1 | 🟢 | Total task time < budget | All tasks scheduled; reasoning says "Everything fit" |
| 5.2 | 🟢 | Tasks exceed budget | High-priority kept first; low-priority dropped |
| 5.3 | 🟠 | **Pet with no tasks** | Contributes nothing; no crash |
| 5.4 | 🟠 | **Owner with no pets** | Empty plan; reasoning generated safely |
| 5.5 | 🟠 | Budget = 0 | Nothing scheduled; all tasks dropped |
| 5.6 | 🟠 | Single task exactly equal to budget | Task fits (`<=` boundary), 0 min left |
| 5.7 | 🟠 | Task longer than entire budget | Dropped; if High-priority → surfaced in reasoning with warning |
| 5.8 | 🟠 | Big task dropped but a later small task still fits | Loop keeps scanning; small task fills leftover time |
| 5.9 | 🟠 | **Duplicate tasks** (same pet/category/title) | Collapsed to one; budget not consumed twice |
| 5.10 | 🟠 | Already-complete tasks in the list | Excluded from eligibility |
| 5.11 | 🟢 | `fair=True` with multiple pets | Round-robin: no single pet monopolizes budget |
| 5.12 | 🟠 | `fair=True` with one pet | Behaves like normal ordering |
| 5.13 | 🟠 | Negative / zero duration task | Duration clamped to 0 in windows; scheduled without breaking budget |
| 5.14 | 🟠 | `is_scheduled` flag correctness | Kept tasks `True`, dropped tasks `False` |

## 6. Reasoning summary — `get_reasoning_summary()`

| # | Type | Scenario | Expected |
|---|------|----------|----------|
| 6.1 | 🟠 | Called before any plan generated | Returns "No plan has been generated yet." |
| 6.2 | 🟢 | After a plan with drops | Lists dropped tasks; High-priority drops flagged with `[!]` first |
| 6.3 | 🟠 | "Tip: add N more minutes" | `N` = smallest dropped task's duration − remaining; shown only when positive |

## 7. Filtering — `filter_tasks()`

| # | Type | Scenario | Expected |
|---|------|----------|----------|
| 7.1 | 🟢 | Filter by `is_complete=True/False` | Correct subset |
| 7.2 | 🟢 | Filter by `pet_name` (case-insensitive, trimmed) | Only that pet's tasks |
| 7.3 | 🟢 | Both filters combined | AND logic |
| 7.4 | 🟠 | Neither filter supplied | Returns copy of full list |
| 7.5 | 🟠 | `pet_name` for pet with no tasks / no match | Returns `[]` |
| 7.6 | 🟠 | Task with `owner_pet=None` + pet filter | Excluded (no crash) |

---

## Priority focus (most important edge cases)

1. **Two tasks at the exact same time** → conflict detected (3.2) and stable sort (2.3).
2. **Pet with no tasks / owner with no pets** → empty plan, no crash (5.3, 5.4).
3. **Budget boundary** → task exactly equal to budget fits; budget=0 schedules nothing (5.5, 5.6).
4. **Recurrence date rollover** across month/leap-year (4.6).
5. **Duplicate & completed tasks** excluded from the plan (5.9, 5.10).
6. **Malformed / unpadded / empty times** sort last and never raise (2.2, 2.4, 2.5).
7. **Dropped High-priority welfare tasks** surfaced in reasoning (5.7, 6.2).
