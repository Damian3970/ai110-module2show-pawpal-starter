"""PawPal+ command-line demo.

Builds a sample owner with pets and tasks, runs the Scheduler, and prints
today's schedule to the terminal.
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def main() -> None:
    # 1. Create an owner with a daily care-time budget.
    owner = Owner(name="Alice", available_time_mins=90)

    # 2. Create at least two pets and add them to the owner.
    biscuit = Pet(name="Biscuit", species="Dog", breed="Golden Retriever")
    mittens = Pet(name="Mittens", species="Cat", breed="Tabby")
    owner.add_pet(biscuit)
    owner.add_pet(mittens)

    # 3. Add at least three tasks (with different durations) to those pets.
    biscuit.add_task(Task("Give medicine", "Meds", 15, "High"))
    biscuit.add_task(Task("Morning walk", "Walks", 45, "Medium"))
    mittens.add_task(Task("Feed Mittens", "Feeding", 10, "High"))
    mittens.add_task(Task("Grooming", "Grooming", 40, "Low"))

    # 4. Run the scheduler and print "Today's Schedule" to the terminal.
    scheduler = Scheduler()
    plan = scheduler.generate_daily_plan(owner)

    print("=" * 40)
    print("Today's Schedule")
    print("=" * 40)
    print(f"Owner: {owner.name}  |  Time budget: {owner.available_time_mins} min")
    print(f"Pets:  {', '.join(p.get_profile_summary() for p in owner.pets)}")
    print("-" * 40)

    # Map each task back to its pet (the scheduler works on a flat list, so we
    # rebuild the task -> pet link here for display). Task is an unhashable
    # dataclass, so key the lookup by object id.
    task_to_pet = {
        id(task): pet for pet in owner.pets for task in pet.tasks
    }

    if plan:
        for i, task in enumerate(plan, start=1):
            pet = task_to_pet[id(task)]
            print(
                f"{i}. [{pet.name}] {task.title} ({task.category}, "
                f"{task.priority}) - {task.duration_mins} min"
            )
    else:
        print("No tasks could be scheduled today.")

    print("-" * 40)
    print("Why this plan:")
    print(scheduler.get_reasoning_summary())
    print("=" * 40)


if __name__ == "__main__":
    main()
