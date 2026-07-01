"""PawPal+ logic layer.

Backend classes for the intelligent daily schedule planner:

- Task      : a single pet-care activity (what, how long, how important).
- Pet       : stores a pet's details and the list of tasks tracked for it.
- Owner     : manages multiple pets and provides access to all their tasks.
- Scheduler : the "brain" that organizes tasks across pets into a daily plan.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import date, timedelta


@dataclass
class Task:
    """A single pet-care activity and its scheduling constraints."""

    title: str
    category: str          # e.g. "Walks", "Feeding", "Meds", "Grooming"
    duration_mins: int
    priority: str           # "High" | "Medium" | "Low"
    time: str = ""          # planned start as "HH:MM" (24-hour); "" = no set time
    recurrence: str = "none"    # "none" | "daily" | "weekly"
    due_date: "date | None" = None  # the day this occurrence is due
    is_scheduled: bool = False  # did it make it into today's plan?
    is_complete: bool = False   # has the owner finished doing it?
    # Back-reference to the owning pet, set by Pet.add_task(). Excluded from
    # eq/repr to avoid infinite recursion (Pet holds a list of Tasks). This
    # lets callers read task.owner_pet directly instead of rebuilding the
    # task -> pet link by object id() at display time.
    owner_pet: "Pet | None" = field(default=None, compare=False, repr=False)

    def update_task(
        self,
        title: str,
        category: str,
        duration_mins: int,
        priority: str,
    ) -> None:
        """Edit this task's details (called from the Streamlit UI)."""
        self.title = title
        self.category = category
        self.duration_mins = duration_mins
        self.priority = priority

    # How far ahead the next occurrence of a recurring task is due. Using
    # timedelta means date arithmetic rolls over month/year/leap-year
    # boundaries correctly (e.g. 2026-01-31 + 1 day -> 2026-02-01) instead
    # of us hand-counting days in a month.
    _RECURRENCE_DELTAS = {
        "daily": timedelta(days=1),
        "weekly": timedelta(weeks=1),
    }

    def next_occurrence(self) -> "Task | None":
        """Build the next occurrence of a recurring task (not yet attached).

        The next date is based on this task's ``due_date`` when set (so
        completing late doesn't skip a cycle), falling back to today's date.
        The interval is one day for "daily" and one week for "weekly".

        Returns:
            A fresh, incomplete Task with its ``due_date`` advanced by one
            interval, or None if this task does not recur (recurrence "none"
            or unrecognized).
        """
        delta = self._RECURRENCE_DELTAS.get(str(self.recurrence).strip().lower())
        if delta is None:
            return None
        base_date = self.due_date or date.today()
        return Task(
            title=self.title,
            category=self.category,
            duration_mins=self.duration_mins,
            priority=self.priority,
            time=self.time,
            recurrence=self.recurrence,
            due_date=base_date + delta,
        )

    def mark_complete(self) -> "Task | None":
        """Mark this task done; if it recurs, spawn and attach the next one.

        Sets ``is_complete`` to True. If the task recurs and has an owning pet,
        the next occurrence is created and added to that pet's task list.

        Returns:
            The newly created next occurrence (already attached to the same
            pet), or None for a one-off task.
        """
        self.is_complete = True
        upcoming = self.next_occurrence()
        if upcoming is not None and self.owner_pet is not None:
            self.owner_pet.add_task(upcoming)
        return upcoming


@dataclass
class Pet:
    """The animal receiving care; owns the list of tasks tracked for it."""

    name: str
    species: str
    breed: str
    tasks: list[Task] = field(default_factory=list)

    def get_profile_summary(self) -> str:
        """Return a formatted string for the UI, e.g. 'Biscuit (Golden Retriever)'."""
        return f"{self.name} ({self.breed})"

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet and record the back-reference."""
        task.owner_pet = self
        self.tasks.append(task)


@dataclass
class Owner:
    """The app user: manages one or more pets and exposes all their tasks."""

    name: str
    available_time_mins: int
    pets: list[Pet] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's profile."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Flatten every pet's tasks into a single list for scheduling."""
        all_tasks: list[Task] = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks


@dataclass
class Conflict:
    """Two tasks whose scheduled time windows overlap."""

    task_a: Task
    task_b: Task

    @property
    def same_pet(self) -> bool:
        """True when both tasks belong to the same pet."""
        return (
            self.task_a.owner_pet is not None
            and self.task_a.owner_pet is self.task_b.owner_pet
        )

    def describe(self) -> str:
        """Human-readable one-line summary, e.g. for the terminal."""
        def label(task: Task) -> str:
            pet = task.owner_pet.name if task.owner_pet else "?"
            return f"'{task.title}' [{pet}] {task.time}-{_add_mins(task.time, task.duration_mins)}"

        scope = "same pet" if self.same_pet else "different pets"
        return f"[!] Time clash ({scope}): {label(self.task_a)} overlaps {label(self.task_b)}"


def _add_mins(time_str: str, minutes: int) -> str:
    """Add minutes to an 'HH:MM' time, for showing a task's end time.

    Args:
        time_str: The start time as "HH:MM" (padding optional).
        minutes: Minutes to add (negative values are clamped to 0).

    Returns:
        The resulting time as a zero-padded "HH:MM" string, wrapping past
        midnight (e.g. "23:30" + 45 -> "00:15").
    """
    total = Scheduler._time_to_minutes(time_str) + max(minutes, 0)
    return f"{(total // 60) % 24:02d}:{total % 60:02d}"


class Scheduler:
    """The brain: organizes tasks across pets into a daily plan.

    Greedy strategy — schedule highest-priority tasks first (shortest first
    within a priority so more care fits the budget), then drop whatever no
    longer fits the owner's available time. Before scheduling, completed and
    duplicate tasks are filtered out. Reasoning from the most recent plan is
    cached so get_reasoning_summary() can explain it.
    """

    # Lower rank == higher priority (scheduled first).
    _PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

    def __init__(self) -> None:
        """Initialize the scheduler with an empty reasoning cache."""
        self._reasoning: str = ""

    def _priority_rank(self, task: Task) -> int:
        """Map a task's priority to a sortable rank; unknown values sort last.

        Args:
            task: The task whose priority string is ranked.

        Returns:
            0 for High, 1 for Medium, 2 for Low, 99 for anything unrecognized.
        """
        return self._PRIORITY_ORDER.get(str(task.priority).strip().lower(), 99)

    def _is_high(self, task: Task) -> bool:
        """Report whether a task is High priority (welfare-critical: meds, feeding).

        Args:
            task: The task to check.

        Returns:
            True if the task's priority ranks as High, else False.
        """
        return self._priority_rank(task) == 0

    def sort_tasks_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Order tasks highest -> lowest priority, shortest first within a tie.

        The duration tiebreak is a value-density heuristic: given equal
        priority, doing the shorter task first lets more tasks fit the budget.

        Args:
            tasks: The tasks to order (not modified in place).

        Returns:
            A new list sorted by (priority rank, duration); the input list is
            left unchanged.
        """
        return sorted(tasks, key=lambda t: (self._priority_rank(t), t.duration_mins))

    @staticmethod
    def _time_to_minutes(time_str: str) -> int:
        """Convert an 'HH:MM' 24-hour string to minutes since midnight.

        Why not just sort the raw strings? Lexicographic (character-by-
        character) string comparison only orders 'HH:MM' correctly when every
        value is zero-padded — '9:00' would wrongly sort *after* '10:00'
        because '9' > '1'. Converting to a number sidesteps that entirely.

        Args:
            time_str: A time like "08:30" or "9:00" (padding optional).

        Returns:
            Minutes since midnight (e.g. "09:15" -> 555). Blank or malformed
            values return 24*60 so they sort last (treated as end of day).
        """
        try:
            hours, minutes = time_str.split(":")
            return int(hours) * 60 + int(minutes)
        except (ValueError, AttributeError):
            return 24 * 60  # push unscheduled / bad values to the end

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered earliest -> latest start time.

        Uses sorted() with a lambda key that maps each task's 'HH:MM' time
        to minutes since midnight, so the comparison is numeric rather than
        an error-prone string comparison.

        Args:
            tasks: The tasks to order (not modified in place).

        Returns:
            A new list sorted by start time; tasks with no set time sort last.
        """
        return sorted(tasks, key=lambda t: self._time_to_minutes(t.time))

    def _time_window(self, task: Task) -> tuple[int, int]:
        """Compute the minutes-since-midnight interval a task occupies.

        Args:
            task: The task whose start time and duration define the window.

        Returns:
            A (start, end) tuple in minutes since midnight, where
            end = start + duration (negative durations are clamped to 0).
        """
        start = self._time_to_minutes(task.time)
        return start, start + max(task.duration_mins, 0)

    def find_conflicts(self, tasks: list[Task]) -> list[Conflict]:
        """Return every pair of tasks whose scheduled time windows overlap.

        Two tasks conflict when their [start, start + duration) windows overlap
        — this covers exact same-start collisions and partial overlaps alike.
        Conflicts are reported across different pets too, since one owner can't
        perform two overlapping tasks at once.

        Args:
            tasks: The tasks to inspect. Tasks with no set 'time' are ignored.

        Returns:
            A list of Conflict objects, one per overlapping pair (empty if none).
        """
        timed = [t for t in tasks if t.time]
        # Sort by start time so we can stop comparing once a later task starts
        # after the current one ends.
        ordered = sorted(timed, key=lambda t: self._time_to_minutes(t.time))

        conflicts: list[Conflict] = []
        for i, first in enumerate(ordered):
            _, first_end = self._time_window(first)
            for second in ordered[i + 1:]:
                second_start, _ = self._time_window(second)
                if second_start >= first_end:
                    break  # sorted by start: nothing later can overlap `first`
                conflicts.append(Conflict(first, second))
        return conflicts

    def check_conflicts(self, tasks: list[Task]) -> str:
        """Lightweight conflict check: return a warning string, never raise.

        Any unexpected error while scanning is swallowed and reported as a soft
        warning instead of crashing the caller — schedule display should
        degrade gracefully.

        Args:
            tasks: The tasks to check for time-window overlaps.

        Returns:
            A multi-line warning string describing the clashes, or "" when
            there are none. The empty string is falsy, so callers can write
            ``if scheduler.check_conflicts(tasks): ...``.
        """
        try:
            conflicts = self.find_conflicts(tasks)
        except Exception as exc:  # defensive: bad data shouldn't take down the app
            return f"[!] Could not check for schedule conflicts ({exc})."

        if not conflicts:
            return ""

        header = (
            f"[!] Found {len(conflicts)} schedule conflict(s) - "
            f"these tasks overlap in time:"
        )
        lines = [header] + [f"  - {c.describe()}" for c in conflicts]
        return "\n".join(lines)

    def filter_tasks(
        self,
        tasks: list[Task],
        *,
        is_complete: bool | None = None,
        pet_name: str | None = None,
    ) -> list[Task]:
        """Return the subset of tasks matching the given criteria.

        Both filters combine with AND when supplied; passing neither returns a
        copy of the full list. Runs in a single pass over the tasks.

        Args:
            tasks: The tasks to filter (not modified in place).
            is_complete: If given, keep only complete (True) or incomplete
                (False) tasks. None means "don't filter on completion".
            pet_name: If given, keep only tasks belonging to the named pet
                (matched case-insensitively). None means "don't filter by pet".

        Returns:
            A new list containing the matching tasks.
        """
        # Normalize the pet name once, not per task. `None` means "filter off",
        # so each clause short-circuits to True when its filter wasn't requested
        # — letting us keep everything in a single pass over the tasks.
        wanted_pet = pet_name.strip().lower() if pet_name is not None else None
        return [
            task for task in tasks
            if (is_complete is None or task.is_complete == is_complete)
            and (wanted_pet is None or (
                task.owner_pet is not None
                and task.owner_pet.name.lower() == wanted_pet
            ))
        ]

    def _eligible_tasks(self, owner: Owner) -> list[Task]:
        """Return schedulable tasks: not already complete, and de-duplicated.

        Duplicates are collapsed by (pet, category, title) so the same chore
        added twice doesn't consume the budget twice.

        Args:
            owner: The owner whose pets' tasks are gathered and filtered.

        Returns:
            The incomplete, de-duplicated tasks, in the order first seen.
        """
        seen: set[tuple[str, str, str]] = set()
        eligible: list[Task] = []
        for task in owner.get_all_tasks():
            if task.is_complete:
                continue
            pet_name = task.owner_pet.name if task.owner_pet else ""
            key = (pet_name, task.category.strip().lower(), task.title.strip().lower())
            if key in seen:
                continue
            seen.add(key)
            eligible.append(task)
        return eligible

    def _interleave_by_pet(self, ordered: list[Task]) -> list[Task]:
        """Round-robin tasks across pets so no single pet monopolizes the budget.

        Args:
            ordered: Tasks already sorted by priority. Their relative order is
                preserved within each pet's queue.

        Returns:
            A new list with one task taken from each pet in turn, repeating
            until every pet's queue is empty.
        """
        buckets: "OrderedDict[str, list[Task]]" = OrderedDict()
        for task in ordered:
            pet_name = task.owner_pet.name if task.owner_pet else ""
            buckets.setdefault(pet_name, []).append(task)

        queues = list(buckets.values())
        interleaved: list[Task] = []
        while any(queues):
            for queue in queues:
                if queue:
                    interleaved.append(queue.pop(0))
        return interleaved

    def generate_daily_plan(self, owner: Owner, fair: bool = False) -> list[Task]:
        """Schedule the owner's tasks within their time budget, dropping the rest.

        Tasks are ordered by priority (shortest first within a priority), then
        greedily kept while they fit the remaining time. The loop keeps scanning
        after a task doesn't fit, so a smaller lower-priority task can still fill
        leftover time. Side effects: sets each task's ``is_scheduled`` flag and
        caches reasoning for ``get_reasoning_summary()``.

        Args:
            owner: The owner whose tasks are scheduled; ``available_time_mins``
                is the budget.
            fair: When True, interleave tasks across pets (round-robin) so each
                animal gets attention instead of one pet consuming the budget.

        Returns:
            The scheduled tasks, in the order they were placed into the plan.
        """
        ordered = self.sort_tasks_by_priority(self._eligible_tasks(owner))
        if fair:
            ordered = self._interleave_by_pet(ordered)

        plan: list[Task] = []
        dropped: list[Task] = []
        remaining = owner.available_time_mins

        for task in ordered:
            if task.duration_mins <= remaining:
                task.is_scheduled = True
                remaining -= task.duration_mins
                plan.append(task)
            else:
                task.is_scheduled = False
                dropped.append(task)

        self._reasoning = self._build_reasoning(owner, plan, dropped, remaining)
        return plan

    def _build_reasoning(
        self,
        owner: Owner,
        plan: list[Task],
        dropped: list[Task],
        remaining: int,
    ) -> str:
        """Compose the explanation of why tasks were kept or dropped."""
        budget = owner.available_time_mins
        used = budget - remaining
        lines = [
            f"You had {budget} minutes available today and scheduled "
            f"{len(plan)} task(s), using {used} min ({remaining} min left)."
        ]

        if not dropped:
            lines.append("Everything fit — no tasks were skipped.")
            return "\n".join(lines)

        # Surface dropped High-priority tasks first — these are welfare-critical
        # (medicine, feeding) and shouldn't be silently omitted.
        for task in dropped:
            if self._is_high(task):
                lines.append(
                    f"[!] Skipped HIGH-priority '{task.title}' "
                    f"({task.duration_mins} min) — consider adding time or "
                    f"splitting it into smaller sessions."
                )
        for task in dropped:
            if not self._is_high(task):
                lines.append(
                    f"Skipped '{task.title}' ({task.duration_mins} min, "
                    f"{task.priority} priority)."
                )

        # "What-if" tip: the smallest amount of extra time that would let the
        # next-closest dropped task fit.
        closest = min(dropped, key=lambda t: t.duration_mins)
        extra_needed = closest.duration_mins - remaining
        if extra_needed > 0:
            lines.append(
                f"Tip: add {extra_needed} more minute(s) to also fit "
                f"'{closest.title}'."
            )
        return "\n".join(lines)

    def get_reasoning_summary(self) -> str:
        """Explain why certain tasks were omitted from the latest plan."""
        return self._reasoning or "No plan has been generated yet."
