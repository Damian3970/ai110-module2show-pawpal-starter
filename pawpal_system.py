"""PawPal+ logic layer.

Backend classes for the intelligent daily schedule planner.
Skeleton generated from diagrams/uml.mmd — method bodies are stubs to be
filled in during the Code & Test step.
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
    is_scheduled: bool = False

    def update_task(
        self,
        title: str,
        category: str,
        duration_mins: int,
        priority: str,
    ) -> None:
        """Edit this task's details (called from the Streamlit UI)."""
        raise NotImplementedError


@dataclass
class Pet:
    """The animal receiving care; owns the list of tasks tracked for it."""

    name: str
    species: str
    breed: str
    tasks: list[Task] = field(default_factory=list)

    def get_profile_summary(self) -> str:
        """Return a formatted string for the UI, e.g. 'Biscuit (Golden Retriever)'."""
        raise NotImplementedError

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet."""
        raise NotImplementedError


@dataclass
class Owner:
    """The app user: holds profile info and manages one or more pets."""

    name: str
    available_time_mins: int
    pets: list[Pet] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's profile."""
        raise NotImplementedError


class Scheduler:
    """Core engine: sorts/filters tasks and produces a daily plan.

    Stateless w.r.t. input data — tasks and the time budget are passed in.
    Reasoning from the most recent plan is cached so get_reasoning_summary()
    can explain why tasks were dropped.
    """

    def __init__(self) -> None:
        self._reasoning: str = ""

    def sort_tasks_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered highest -> lowest priority."""
        raise NotImplementedError

    def generate_daily_plan(self, pet: Pet, total_time_limit: int) -> list[Task]:
        """Build the daily plan: add tasks while they fit the time budget,
        marking each scheduled task is_scheduled = True. Drops what doesn't fit
        and records the reasoning for get_reasoning_summary()."""
        raise NotImplementedError

    def get_reasoning_summary(self) -> str:
        """Explain why certain tasks were omitted from the latest plan."""
        raise NotImplementedError
