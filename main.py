"""PawPal+ command-line demo.

Builds a sample owner with pets and tasks, runs the Scheduler, and prints
today's schedule to the terminal. Also demonstrates the sort_by_time and
filter_tasks helpers so we can confirm they work.
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def print_tasks(tasks: list[Task]) -> None:
    """Print a numbered task list, or a placeholder when empty."""
    if not tasks:
        print("  (none)")
        return
    for i, task in enumerate(tasks, start=1):
        pet_name = task.owner_pet.name if task.owner_pet else "?"
        clock = task.time or "--:--"
        status = "done" if task.is_complete else "todo"
        print(
            f"  {i}. {clock} [{pet_name}] {task.title} "
            f"({task.category}, {task.priority}, {task.duration_mins} min) [{status}]"
        )


def main() -> None:
    # 1. Create an owner with a daily care-time budget.
    owner = Owner(name="Alice", available_time_mins=90)

    # 2. Create at least two pets and add them to the owner.
    biscuit = Pet(name="Biscuit", species="Dog", breed="Golden Retriever")
    mittens = Pet(name="Mittens", species="Cat", breed="Tabby")
    owner.add_pet(biscuit)
    owner.add_pet(mittens)

    # 3. Add tasks deliberately OUT OF TIME ORDER (and not zero-padded) so the
    #    sort has real work to do. One task is pre-marked complete to exercise
    #    the completion filter.
    biscuit.add_task(Task("Morning walk", "Walks", 45, "Medium", time="7:30"))
    biscuit.add_task(Task("Give medicine", "Meds", 15, "High", time="20:00"))
    mittens.add_task(Task("Grooming", "Grooming", 40, "Low", time="9:15"))

    # Deliberately schedule Mittens's breakfast at the SAME time (07:30) as
    # Biscuit's morning walk to create a conflict the Scheduler should catch.
    mittens.add_task(Task("Feed Mittens", "Feeding", 10, "High", time="7:30"))

    fed = Task("Evening feed", "Feeding", 10, "High", time="18:00")
    fed.mark_complete()  # already done today
    mittens.add_task(fed)

    scheduler = Scheduler()
    all_tasks = owner.get_all_tasks()

    # --- Demonstrate SORTING by time -------------------------------------
    print("=" * 52)
    print("All tasks, as ADDED (unsorted)")
    print("=" * 52)
    print_tasks(all_tasks)

    print()
    print("=" * 52)
    print("All tasks, SORTED BY TIME (sort_by_time)")
    print("=" * 52)
    print_tasks(scheduler.sort_by_time(all_tasks))

    # --- Demonstrate CONFLICT DETECTION ----------------------------------
    print()
    print("=" * 52)
    print("CONFLICT CHECK (check_conflicts)")
    print("=" * 52)
    warning = scheduler.check_conflicts(all_tasks)
    print(warning if warning else "No scheduling conflicts.")

    # --- Demonstrate FILTERING -------------------------------------------
    print()
    print("=" * 52)
    print("FILTER: incomplete tasks only (is_complete=False)")
    print("=" * 52)
    print_tasks(scheduler.filter_tasks(all_tasks, is_complete=False))

    print()
    print("=" * 52)
    print("FILTER: Mittens's tasks only (pet_name='Mittens')")
    print("=" * 52)
    print_tasks(scheduler.filter_tasks(all_tasks, pet_name="Mittens"))

    print()
    print("=" * 52)
    print("FILTER + SORT: Mittens's incomplete tasks, by time")
    print("=" * 52)
    mittens_todo = scheduler.filter_tasks(
        all_tasks, is_complete=False, pet_name="Mittens"
    )
    print_tasks(scheduler.sort_by_time(mittens_todo))

    print()
    print("=" * 52)
    print("FILTER + SORT: Biscuit's incomplete tasks, by time")
    print("=" * 52)
    biscuit_todo = scheduler.filter_tasks(
        all_tasks, is_complete=False, pet_name="Biscuit"
    )
    print_tasks(scheduler.sort_by_time(biscuit_todo))

    # --- The actual daily plan -------------------------------------------
    plan = scheduler.generate_daily_plan(owner)

    print()
    print("=" * 52)
    print("Today's Schedule")
    print("=" * 52)
    print(f"Owner: {owner.name}  |  Time budget: {owner.available_time_mins} min")
    print(f"Pets:  {', '.join(p.get_profile_summary() for p in owner.pets)}")
    print("-" * 52)

    if plan:
        for i, task in enumerate(plan, start=1):
            pet_name = task.owner_pet.name if task.owner_pet else "?"
            print(
                f"{i}. [{pet_name}] {task.title} ({task.category}, "
                f"{task.priority}) - {task.duration_mins} min"
            )
    else:
        print("No tasks could be scheduled today.")

    print("-" * 52)
    print("Why this plan:")
    print(scheduler.get_reasoning_summary())
    print("=" * 52)


if __name__ == "__main__":
    main()
