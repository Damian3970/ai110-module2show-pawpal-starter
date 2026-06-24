"""Unit tests for the PawPal+ logic layer."""

from pawpal_system import Pet, Task


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
