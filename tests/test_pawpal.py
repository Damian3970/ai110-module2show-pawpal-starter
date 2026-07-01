"""Unit tests for the PawPal+ logic layer."""

from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_changes_status():
    """Task Completion: calling mark_complete() flips the task's status."""
    task = Task("Give medicine", "Meds", 15, "High")

    assert task.is_complete is False  # starts incomplete

    task.mark_complete()

    assert task.is_complete is True


def test_add_task_increases_pet_task_count():
    """Task Addition: adding a task to a Pet increases its task count."""
    pet = Pet("Biscuit", "Dog", "Golden Retriever")

    assert len(pet.tasks) == 0  # no tasks yet

    pet.add_task(Task("Morning walk", "Walks", 30, "Medium"))

    assert len(pet.tasks) == 1


def test_completing_daily_task_spawns_next_day():
    """Recurrence: a Daily task, when completed, creates tomorrow's occurrence."""
    pet = Pet("Biscuit", "Dog", "Golden Retriever")
    task = Task("Meds", "Meds", 10, "High", recurrence="daily", due_date=date(2026, 1, 31))
    pet.add_task(task)

    upcoming = task.mark_complete()

    assert task.is_complete is True
    assert upcoming is not None
    assert upcoming.due_date == date(2026, 2, 1)  # rolls into February correctly
    assert upcoming.is_complete is False          # the new one is fresh
    assert upcoming in pet.tasks                  # attached to the same pet
    assert len(pet.tasks) == 2


def test_completing_weekly_task_spawns_next_week():
    """Recurrence: a Weekly task advances the due date by seven days."""
    pet = Pet("Mittens", "Cat", "Tabby")
    task = Task("Bath", "Grooming", 30, "Low", recurrence="weekly", due_date=date(2026, 1, 1))
    pet.add_task(task)

    upcoming = task.mark_complete()

    assert upcoming.due_date == date(2026, 1, 8)


def test_completing_one_off_task_spawns_nothing():
    """Recurrence: a non-recurring task creates no new occurrence."""
    pet = Pet("Biscuit", "Dog", "Golden Retriever")
    task = Task("Vet visit", "Meds", 60, "High")  # recurrence defaults to "none"
    pet.add_task(task)

    upcoming = task.mark_complete()

    assert upcoming is None
    assert len(pet.tasks) == 1


def test_recurring_task_without_due_date_uses_today():
    """Recurrence: with no due_date set, the next occurrence is based on today."""
    pet = Pet("Biscuit", "Dog", "Golden Retriever")
    task = Task("Walk", "Walks", 20, "Medium", recurrence="daily")
    pet.add_task(task)

    upcoming = task.mark_complete()

    assert upcoming.due_date == date.today() + timedelta(days=1)


def test_add_task_sets_owner_pet_back_reference():
    """Data model: add_task wires each task back to its owning pet."""
    pet = Pet("Biscuit", "Dog", "Golden Retriever")
    task = Task("Morning walk", "Walks", 30, "Medium")

    pet.add_task(task)

    assert task.owner_pet is pet


def _owner_with(*tasks, minutes):
    """Build a single-pet owner holding the given tasks."""
    owner = Owner(name="Test", available_time_mins=minutes)
    pet = Pet("Biscuit", "Dog", "Golden Retriever")
    for task in tasks:
        pet.add_task(task)
    owner.add_pet(pet)
    return owner


def test_high_priority_scheduled_before_low():
    """Scheduling: higher priority is scheduled first when time is tight."""
    high = Task("Meds", "Meds", 30, "High")
    low = Task("Grooming", "Grooming", 30, "Low")
    owner = _owner_with(low, high, minutes=30)  # only room for one

    plan = Scheduler().generate_daily_plan(owner)

    assert plan == [high]


def test_shorter_task_wins_the_density_tiebreak():
    """Scheduling: within a priority, shorter tasks are scheduled first."""
    long_task = Task("Long walk", "Walks", 45, "High")
    short_task = Task("Feed", "Feeding", 10, "High")
    owner = _owner_with(long_task, short_task, minutes=10)

    plan = Scheduler().generate_daily_plan(owner)

    assert plan == [short_task]


def test_completed_tasks_are_skipped():
    """Scheduling: already-complete tasks don't consume the budget."""
    done = Task("Feed", "Feeding", 10, "High")
    done.mark_complete()
    todo = Task("Walk", "Walks", 10, "Medium")
    owner = _owner_with(done, todo, minutes=10)

    plan = Scheduler().generate_daily_plan(owner)

    assert plan == [todo]


def test_duplicate_tasks_are_collapsed():
    """Scheduling: duplicate (pet, category, title) tasks schedule once."""
    owner = _owner_with(
        Task("Feed", "Feeding", 10, "High"),
        Task("Feed", "Feeding", 10, "High"),
        minutes=100,
    )

    plan = Scheduler().generate_daily_plan(owner)

    assert len(plan) == 1


def test_smaller_task_fills_leftover_time():
    """Scheduling: the loop keeps scanning past a task that doesn't fit."""
    big = Task("Big walk", "Walks", 40, "Medium")
    small = Task("Quick feed", "Feeding", 5, "Low")
    owner = _owner_with(big, small, minutes=30)  # big won't fit, small will

    plan = Scheduler().generate_daily_plan(owner)

    assert plan == [small]


def test_reasoning_flags_dropped_high_priority_task():
    """Reasoning: dropping a High-priority task raises a visible warning."""
    owner = _owner_with(Task("Meds", "Meds", 60, "High"), minutes=30)

    scheduler = Scheduler()
    scheduler.generate_daily_plan(owner)

    assert "HIGH-priority" in scheduler.get_reasoning_summary()


def test_sort_by_time_orders_earliest_first():
    """Sorting: sort_by_time returns tasks in ascending start-time order."""
    noon = Task("Lunch feed", "Feeding", 10, "High", time="12:00")
    morning = Task("Breakfast", "Feeding", 10, "High", time="07:30")
    evening = Task("Dinner", "Feeding", 10, "High", time="18:15")

    ordered = Scheduler().sort_by_time([noon, evening, morning])

    assert ordered == [morning, noon, evening]


def test_sort_by_time_handles_unpadded_hours():
    """Sorting: '9:00' sorts before '10:00' (numeric, not string, compare)."""
    ten = Task("Ten", "Walks", 10, "Low", time="10:00")
    nine = Task("Nine", "Walks", 10, "Low", time="9:00")  # not zero-padded

    ordered = Scheduler().sort_by_time([ten, nine])

    assert ordered == [nine, ten]  # a raw string sort would get this wrong


def test_sort_by_time_pushes_blank_times_last():
    """Sorting: tasks with no set time sort to the end of the day."""
    timed = Task("Timed", "Meds", 10, "High", time="08:00")
    untimed = Task("Whenever", "Grooming", 10, "Low")  # time defaults to ""

    ordered = Scheduler().sort_by_time([untimed, timed])

    assert ordered == [timed, untimed]


def test_filter_tasks_by_completion_status():
    """Filtering: is_complete keeps only matching tasks."""
    owner = Owner(name="Test", available_time_mins=100)
    pet = Pet("Biscuit", "Dog", "Golden Retriever")
    done = Task("Feed", "Feeding", 10, "High")
    done.mark_complete()
    todo = Task("Walk", "Walks", 10, "Medium")
    pet.add_task(done)
    pet.add_task(todo)
    owner.add_pet(pet)

    scheduler = Scheduler()
    tasks = owner.get_all_tasks()

    assert scheduler.filter_tasks(tasks, is_complete=False) == [todo]
    assert scheduler.filter_tasks(tasks, is_complete=True) == [done]


def test_filter_tasks_by_pet_name_is_case_insensitive():
    """Filtering: pet_name keeps only that pet's tasks, ignoring case."""
    owner = Owner(name="Test", available_time_mins=100)
    dog = Pet("Biscuit", "Dog", "Golden Retriever")
    cat = Pet("Mittens", "Cat", "Tabby")
    walk = Task("Walk", "Walks", 10, "Medium")
    feed = Task("Feed", "Feeding", 10, "High")
    dog.add_task(walk)
    cat.add_task(feed)
    owner.add_pet(dog)
    owner.add_pet(cat)

    result = Scheduler().filter_tasks(owner.get_all_tasks(), pet_name="mittens")

    assert result == [feed]


def test_filter_tasks_combines_criteria():
    """Filtering: completion and pet_name filters combine with AND."""
    owner = Owner(name="Test", available_time_mins=100)
    cat = Pet("Mittens", "Cat", "Tabby")
    done = Task("Feed", "Feeding", 10, "High")
    done.mark_complete()
    todo = Task("Groom", "Grooming", 10, "Low")
    cat.add_task(done)
    cat.add_task(todo)
    owner.add_pet(cat)

    result = Scheduler().filter_tasks(
        owner.get_all_tasks(), is_complete=False, pet_name="Mittens"
    )

    assert result == [todo]


def test_find_conflicts_detects_overlap_same_pet():
    """Conflicts: two overlapping tasks for one pet are flagged as same-pet."""
    pet = Pet("Biscuit", "Dog", "Golden Retriever")
    walk = Task("Walk", "Walks", 30, "Medium", time="08:00")   # 08:00-08:30
    meds = Task("Meds", "Meds", 15, "High", time="08:15")      # 08:15-08:30
    pet.add_task(walk)
    pet.add_task(meds)

    conflicts = Scheduler().find_conflicts(pet.tasks)

    assert len(conflicts) == 1
    assert conflicts[0].same_pet is True


def test_find_conflicts_detects_overlap_across_pets():
    """Conflicts: overlapping tasks on different pets are flagged too."""
    owner = Owner(name="Test", available_time_mins=100)
    dog = Pet("Biscuit", "Dog", "Golden Retriever")
    cat = Pet("Mittens", "Cat", "Tabby")
    dog.add_task(Task("Walk", "Walks", 30, "Medium", time="09:00"))  # 09:00-09:30
    cat.add_task(Task("Feed", "Feeding", 10, "High", time="09:20"))  # 09:20-09:30
    owner.add_pet(dog)
    owner.add_pet(cat)

    conflicts = Scheduler().find_conflicts(owner.get_all_tasks())

    assert len(conflicts) == 1
    assert conflicts[0].same_pet is False


def test_no_conflict_when_windows_touch_but_dont_overlap():
    """Conflicts: back-to-back tasks (one ends as the next starts) don't clash."""
    pet = Pet("Biscuit", "Dog", "Golden Retriever")
    pet.add_task(Task("Walk", "Walks", 30, "Medium", time="08:00"))  # 08:00-08:30
    pet.add_task(Task("Feed", "Feeding", 10, "High", time="08:30"))  # 08:30-08:40

    assert Scheduler().find_conflicts(pet.tasks) == []


def test_untimed_tasks_are_ignored_for_conflicts():
    """Conflicts: tasks without a set time are not considered."""
    pet = Pet("Biscuit", "Dog", "Golden Retriever")
    pet.add_task(Task("Walk", "Walks", 30, "Medium"))  # no time
    pet.add_task(Task("Feed", "Feeding", 10, "High"))  # no time

    assert Scheduler().find_conflicts(pet.tasks) == []


def test_check_conflicts_returns_empty_string_when_none():
    """Lightweight check: no clashes -> falsy empty string."""
    pet = Pet("Biscuit", "Dog", "Golden Retriever")
    pet.add_task(Task("Walk", "Walks", 30, "Medium", time="08:00"))
    pet.add_task(Task("Feed", "Feeding", 10, "High", time="09:00"))

    assert Scheduler().check_conflicts(pet.tasks) == ""


def test_check_conflicts_returns_warning_message_when_clashing():
    """Lightweight check: overlapping tasks -> human-readable warning text."""
    pet = Pet("Biscuit", "Dog", "Golden Retriever")
    pet.add_task(Task("Walk", "Walks", 30, "Medium", time="08:00"))
    pet.add_task(Task("Meds", "Meds", 15, "High", time="08:15"))

    warning = Scheduler().check_conflicts(pet.tasks)

    assert warning.startswith("[!]")
    assert "1 schedule conflict" in warning
    assert "Walk" in warning and "Meds" in warning


def test_check_conflicts_does_not_crash_on_bad_input():
    """Lightweight check: malformed input returns a warning, never raises."""
    warning = Scheduler().check_conflicts([42, "not a task"])  # type: ignore[list-item]

    assert isinstance(warning, str)
    assert warning.startswith("[!]")


# ---------------------------------------------------------------------------
# Rubric coverage: duplicate (identical) times
# ---------------------------------------------------------------------------

def test_find_conflicts_flags_duplicate_times():
    """Conflict Detection: two tasks at the EXACT same time are flagged."""
    pet = Pet("Biscuit", "Dog", "Golden Retriever")
    feed = Task("Feed", "Feeding", 15, "High", time="08:00")   # 08:00-08:15
    walk = Task("Walk", "Walks", 30, "Medium", time="08:00")   # 08:00-08:30
    pet.add_task(feed)
    pet.add_task(walk)

    conflicts = Scheduler().find_conflicts(pet.tasks)

    assert len(conflicts) == 1  # the identical start time is a clash


def test_check_conflicts_reports_duplicate_times():
    """Conflict Detection: the Scheduler surfaces duplicate-time clashes as text."""
    pet = Pet("Biscuit", "Dog", "Golden Retriever")
    pet.add_task(Task("Feed", "Feeding", 15, "High", time="12:00"))
    pet.add_task(Task("Meds", "Meds", 10, "High", time="12:00"))  # same time

    warning = Scheduler().check_conflicts(pet.tasks)

    assert "1 schedule conflict" in warning
    assert "Feed" in warning and "Meds" in warning


def test_three_tasks_same_time_flag_all_pairs():
    """Conflict Detection: N tasks sharing a time yield every pairwise clash."""
    pet = Pet("Biscuit", "Dog", "Golden Retriever")
    for title in ("Feed", "Meds", "Walk"):
        pet.add_task(Task(title, "Care", 10, "High", time="09:00"))

    conflicts = Scheduler().find_conflicts(pet.tasks)

    assert len(conflicts) == 3  # 3 tasks -> C(3,2) = 3 overlapping pairs


def test_sort_by_time_keeps_both_when_times_tie():
    """Sorting Correctness: duplicate times don't drop or lose a task."""
    first = Task("Feed", "Feeding", 10, "High", time="08:00")
    second = Task("Meds", "Meds", 10, "High", time="08:00")  # identical time

    ordered = Scheduler().sort_by_time([first, second])

    assert ordered == [first, second]  # both kept, stable order


def test_fair_mode_interleaves_across_pets():
    """Fairness: fair=True gives each pet attention instead of one hogging time."""
    owner = Owner(name="Test", available_time_mins=20)
    dog = Pet("Biscuit", "Dog", "Golden Retriever")
    cat = Pet("Mittens", "Cat", "Tabby")
    dog.add_task(Task("Walk", "Walks", 10, "Medium"))
    dog.add_task(Task("Play", "Play", 10, "Medium"))
    cat.add_task(Task("Feed", "Feeding", 10, "Medium"))
    owner.add_pet(dog)
    owner.add_pet(cat)

    plan = Scheduler().generate_daily_plan(owner, fair=True)

    scheduled_pets = {task.owner_pet.name for task in plan}
    assert scheduled_pets == {"Biscuit", "Mittens"}
