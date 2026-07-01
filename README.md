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

```
# Paste your pytest output here
```

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

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
