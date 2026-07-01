# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

My sample output: 

------------------

========================================
Today's Schedule
========================================
Owner: Alice  |  Time budget: 90 min
Pets:  Biscuit (Golden Retriever), Mittens (Tabby)
----------------------------------------
1. [Biscuit] Give medicine (Meds, High) - 15 min
2. [Mittens] Feed Mittens (Feeding, High) - 10 min
3. [Biscuit] Morning walk (Walks, Medium) - 45 min
----------------------------------------
Why this plan:
You had 90 minutes available today and scheduled 3 task(s).
Skipped 'Grooming' (40 min, Low priority) because only 20 minute(s) remained.
========================================

------------------

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

The tests cover sorting correctness, recurrence logic, conflict detection, scheduling, and filtering. 

```
# Paste your pytest output here
```
================================================================= test session starts ==================================================================
platform win32 -- Python 3.13.5, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\adami\OneDrive\Desktop\AI-110\ai110-module2show-pawpal-starter
plugins: anyio-4.13.0
collected 31 items                                                                                                                                      

tests\test_pawpal.py ...............................                                                                                              [100%]

================================================================== 31 passed in 0.09s ==================================================================


Confidence Level: 5/5 Stars

## ✨ Features

The algorithms implemented in [`pawpal_system.py`](pawpal_system.py):

- **Priority sorting** — orders tasks High → Medium → Low, then *shortest-first*
  within a tier (a value-density heuristic so more care fits the budget).
- **Sorting by time** — orders tasks by `"HH:MM"` start time, converted to
  minutes since midnight so unpadded times like `9:00` sort correctly before
  `10:00` (a plain string sort would not).
- **Conflict warnings** — detects overlapping tasks by comparing their
  `[start, start + duration)` windows, catching exact same-time clashes and
  partial overlaps, **across different pets too**; surfaces a plain-language
  warning that names the clashing tasks and never crashes on bad data.
- **Daily & weekly recurrence** — completing a recurring task auto-spawns its
  next occurrence (`+1 day` / `+7 days` via `timedelta`, so month/leap-year
  boundaries roll over correctly) and attaches it to the same pet.
- **Greedy daily planning** — fills the owner's time budget by keeping tasks
  while they fit, and keeps scanning so a smaller lower-priority task can still
  use leftover time.
- **Fair sharing across pets** — an optional round-robin mode interleaves tasks
  so one pet doesn't consume the entire budget.
- **Task filtering** — filter by completion status and/or pet name
  (case-insensitive), combined with AND, in a single pass.
- **De-duplication** — collapses duplicate `(pet, category, title)` tasks so the
  same chore added twice doesn't consume the budget twice.
- **Plan reasoning** — explains what was scheduled and why, flags dropped
  High-priority (welfare-critical) tasks, and gives a "what-if" tip for the
  smallest extra time that would fit the next task.

## 📐 Smarter Scheduling

Beyond a basic plan, PawPal+ adds several "smarter" behaviors. Each is
implemented in [`pawpal_system.py`](pawpal_system.py) and covered by tests in
[`tests/test_pawpal.py`](tests/test_pawpal.py).

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sort by priority | `Scheduler.sort_tasks_by_priority()` | High → Medium → Low, then **shortest first** within a tier so more care fits the budget. |
| Sort by time | `Scheduler.sort_by_time()` | Orders tasks by their `"HH:MM"` start time. |
| Filter tasks | `Scheduler.filter_tasks()` | Filter by completion status and/or pet name; both criteria combine (AND). |
| Conflict detection | `Scheduler.find_conflicts()` | Finds every pair of tasks whose time windows overlap. |
| Lightweight conflict check | `Scheduler.check_conflicts()` | Returns a printable warning string (never raises). |
| Recurring tasks | `Task.mark_complete()` / `Task.next_occurrence()` | Completing a daily/weekly task auto-creates its next occurrence. |
| Plan generation | `Scheduler.generate_daily_plan()` | Greedy fill within the time budget; `fair=True` shares time across pets. |
| Plan reasoning | `Scheduler.get_reasoning_summary()` | Explains what was kept/dropped and why. |

SORTING BEHAVIOR 

- **`Scheduler.sort_by_time(tasks)`** sorts tasks by their `"HH:MM"` start time
  using `sorted()` with a lambda `key` that converts each time to minutes since
  midnight (`_time_to_minutes`). Comparing numbers rather than raw strings means
  an unpadded `"9:00"` correctly sorts *before* `"10:00"` (a plain string sort
  would get this wrong because `'9' > '1'`).
- **`Scheduler.sort_tasks_by_priority(tasks)`** sorts by `(priority, duration)`,
  so higher-priority tasks come first and, within the same priority, shorter
  tasks come first to pack more into the day.

FILTERING BEHAVIOR

- **`Scheduler.filter_tasks(tasks, *, is_complete=None, pet_name=None)`** returns
  the subset matching the given criteria. Filter by **completion status**
  (`is_complete=True/False`), by **pet name** (case-insensitive), or both — the
  two criteria combine with AND. Passing neither returns a copy of the full
  list. It runs in a single pass over the tasks.

CONFLICT DETECTION LOGIC 

- **`Scheduler.find_conflicts(tasks)`** returns the list of overlapping task
  pairs. Each task occupies the window `[start, start + duration_mins)`; two
  tasks conflict when those windows overlap. This catches exact same-start
  collisions *and* partial overlaps, and it flags conflicts **across different
  pets** too, since one owner can't be in two places at once.
- **`Scheduler.check_conflicts(tasks)`** is the lightweight wrapper: it returns
  a ready-to-print warning string (or `""` when there are no clashes) and never
  raises, so a bad time value degrades to a soft warning instead of a crash.

RECURRING TASK LOGIC

- A `Task` has a `recurrence` field (`"none"`, `"daily"`, or `"weekly"`) and a
  `due_date`. When **`Task.mark_complete()`** is called on a recurring task, it
  marks the task done and automatically spawns the next occurrence via
  **`Task.next_occurrence()`**, attaching it to the same pet.
- The next due date is computed with `datetime.timedelta` (`+1 day` for daily,
  `+7 days` for weekly), so month/year/leap-year boundaries roll over correctly
  (e.g. `2026-01-31` → `2026-02-01`).

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. Enter owner information (name and time available)
2. Enter pet information (name, species, breed)
3. Enter task(s) (title, duration, pet, category of task, priority, repeats?)
4. (Optional) - distribute time fairly amongst pets. 
5. Create a schedule

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

CLI Output from running "main.py":

--------------------------------------------------------------------------
====================================================
All tasks, as ADDED (unsorted)
====================================================
  1. 7:30 [Biscuit] Morning walk (Walks, Medium, 45 min) [todo]
  2. 20:00 [Biscuit] Give medicine (Meds, High, 15 min) [todo]
  3. 9:15 [Mittens] Grooming (Grooming, Low, 40 min) [todo]
  4. 7:30 [Mittens] Feed Mittens (Feeding, High, 10 min) [todo]
  5. 18:00 [Mittens] Evening feed (Feeding, High, 10 min) [done]

====================================================
All tasks, SORTED BY TIME (sort_by_time)
====================================================
  1. 7:30 [Biscuit] Morning walk (Walks, Medium, 45 min) [todo]
  2. 7:30 [Mittens] Feed Mittens (Feeding, High, 10 min) [todo]
  3. 9:15 [Mittens] Grooming (Grooming, Low, 40 min) [todo]
  4. 18:00 [Mittens] Evening feed (Feeding, High, 10 min) [done]
  5. 20:00 [Biscuit] Give medicine (Meds, High, 15 min) [todo]

====================================================
CONFLICT CHECK (check_conflicts)
====================================================
[!] Found 1 schedule conflict(s) - these tasks overlap in time:
  - [!] Time clash (different pets): 'Morning walk' [Biscuit] 7:30-08:15 overlaps 'Feed Mittens' [Mittens] 7:30-07:40

====================================================
FILTER: incomplete tasks only (is_complete=False)
====================================================
  1. 7:30 [Biscuit] Morning walk (Walks, Medium, 45 min) [todo]
  2. 20:00 [Biscuit] Give medicine (Meds, High, 15 min) [todo]
  3. 9:15 [Mittens] Grooming (Grooming, Low, 40 min) [todo]
  4. 7:30 [Mittens] Feed Mittens (Feeding, High, 10 min) [todo]

====================================================
FILTER: Mittens's tasks only (pet_name='Mittens')
====================================================
  1. 9:15 [Mittens] Grooming (Grooming, Low, 40 min) [todo]
  2. 7:30 [Mittens] Feed Mittens (Feeding, High, 10 min) [todo]
  3. 18:00 [Mittens] Evening feed (Feeding, High, 10 min) [done]

====================================================
FILTER + SORT: Mittens's incomplete tasks, by time
====================================================
  1. 7:30 [Mittens] Feed Mittens (Feeding, High, 10 min) [todo]
  2. 9:15 [Mittens] Grooming (Grooming, Low, 40 min) [todo]

====================================================
FILTER + SORT: Biscuit's incomplete tasks, by time
====================================================
  1. 7:30 [Biscuit] Morning walk (Walks, Medium, 45 min) [todo]
  2. 20:00 [Biscuit] Give medicine (Meds, High, 15 min) [todo]

====================================================
Today's Schedule
====================================================
Owner: Alice  |  Time budget: 90 min
Pets:  Biscuit (Golden Retriever), Mittens (Tabby)
----------------------------------------------------
1. [Mittens] Feed Mittens (Feeding, High) - 10 min
2. [Biscuit] Give medicine (Meds, High) - 15 min
3. [Biscuit] Morning walk (Walks, Medium) - 45 min
----------------------------------------------------
Why this plan:
You had 90 minutes available today and scheduled 3 task(s), using 70 min (20 min left).
Skipped 'Grooming' (40 min, Low priority).
Tip: add 20 more minute(s) to also fit 'Grooming'.
====================================================