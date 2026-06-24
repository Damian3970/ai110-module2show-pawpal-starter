"""PawPal+ logic layer.

Backend classes for the intelligent daily schedule planner:

- Task      : a single pet-care activity (what, how long, how important).
- Pet       : stores a pet's details and the list of tasks tracked for it.
- Owner     : manages multiple pets and provides access to all their tasks.
- Scheduler : the "brain" that organizes tasks across pets into a daily plan.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Task:
    """A single pet-care activity and its scheduling constraints."""

    title: str
    category: str          # e.g. "Walks", "Feeding", "Meds", "Grooming"
    duration_mins: int
    priority: str           # "High" | "Medium" | "Low"
    is_scheduled: bool = False  # did it make it into today's plan?
    is_complete: bool = False   # has the owner finished doing it?

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

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.is_complete = True


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
        """Attach a task to this pet."""
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


class Scheduler:
    """The brain: organizes tasks across pets into a daily plan.

    Greedy strategy — schedule highest-priority tasks first, then drop
    whatever no longer fits the owner's available time. Reasoning from the
    most recent plan is cached so get_reasoning_summary() can explain it.
    """

    # Lower rank == higher priority (scheduled first).
    _PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

    def __init__(self) -> None:
        """Initialize the scheduler with an empty reasoning cache."""
        self._reasoning: str = ""

    def _priority_rank(self, task: Task) -> int:
        """Map a task's priority to a sortable rank; unknown values sort last."""
        return self._PRIORITY_ORDER.get(str(task.priority).strip().lower(), 99)

    def sort_tasks_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered highest -> lowest priority (stable for ties)."""
        return sorted(tasks, key=self._priority_rank)

    def generate_daily_plan(self, owner: Owner) -> list[Task]:
        """Schedule the owner's tasks by priority within their time budget, dropping the rest."""
        ordered = self.sort_tasks_by_priority(owner.get_all_tasks())

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
        lines = [
            f"You had {budget} minutes available today and scheduled "
            f"{len(plan)} task(s)."
        ]
        if not dropped:
            lines.append("Everything fit — no tasks were skipped.")
        else:
            for task in dropped:
                lines.append(
                    f"Skipped '{task.title}' ({task.duration_mins} min, "
                    f"{task.priority} priority) because only {remaining} "
                    f"minute(s) remained."
                )
        return "\n".join(lines)

    def get_reasoning_summary(self) -> str:
        """Explain why certain tasks were omitted from the latest plan."""
        return self._reasoning or "No plan has been generated yet."
