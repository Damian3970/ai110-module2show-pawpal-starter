import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# Create the Owner once and keep it in session state so pets and tasks
# persist as the user interacts with the app (Streamlit reruns on every click).
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_time_mins=120)

owner = st.session_state.owner

st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)
owner.available_time_mins = st.number_input(
    "Available care time today (minutes)",
    min_value=1,
    max_value=1440,
    value=owner.available_time_mins,
)

st.divider()

st.subheader("Add a Pet")
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col_p2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col_p3:
    breed = st.text_input("Breed", value="Mixed")

if st.button("Add pet"):
    owner.add_pet(Pet(name=pet_name, species=species, breed=breed))
    st.success(f"Added {pet_name} to {owner.name}'s pets.")

if owner.pets:
    st.write("Current pets:")
    for pet in owner.pets:
        st.write(f"- {pet.get_profile_summary()} — {len(pet.tasks)} task(s)")
else:
    st.info("No pets yet. Add one above.")

st.divider()

st.subheader("Add a Task")
if owner.pets:
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
        category = st.selectbox("Category", ["Walks", "Feeding", "Meds", "Grooming"])
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col3:
        target_pet_name = st.selectbox("For pet", [p.name for p in owner.pets])
        recurrence = st.selectbox("Repeats", ["none", "daily", "weekly"])

    # Optional start time. Leaving the box unchecked stores "" (no set time),
    # which the Scheduler sorts to the end of the day and skips for conflicts.
    set_time = st.checkbox("Give this task a start time")
    start_time = ""
    if set_time:
        picked = st.time_input("Start time")
        start_time = picked.strftime("%H:%M")

    if st.button("Add task"):
        target_pet = next(p for p in owner.pets if p.name == target_pet_name)
        target_pet.add_task(
            Task(
                title=task_title,
                category=category,
                duration_mins=int(duration),
                priority=priority,
                time=start_time,
                recurrence=recurrence,
            )
        )
        st.success(f"Added '{task_title}' for {target_pet_name}.")
else:
    st.info("Add a pet before adding tasks.")

st.divider()

st.subheader("Build Schedule")
fair = st.checkbox(
    "Share time fairly across pets",
    help="Round-robin tasks so one pet doesn't use up the whole time budget.",
)
if st.button("Generate schedule"):
    scheduler = Scheduler()
    plan = scheduler.generate_daily_plan(owner, fair=fair)

    # --- Conflict warning (most helpful placement: up top, before the plan) ---
    # A pet owner needs to SEE a clash before they read the schedule, so it's
    # surfaced first as a prominent warning that names the tasks and times.
    # check_conflicts() returns "" when there are none and never raises.
    conflict_msg = scheduler.check_conflicts(plan)
    if conflict_msg:
        st.warning(conflict_msg, icon="⚠️")
    else:
        st.success("No time conflicts — nothing overlaps. ✅")

    st.markdown("### Today's Schedule")
    if plan:
        # Show the plan in chronological order using the Scheduler's time sort,
        # rendered as a clean table instead of a plain bulleted list.
        ordered = scheduler.sort_by_time(plan)
        rows = [
            {
                "Time": task.time or "Anytime",
                "Pet": task.owner_pet.name if task.owner_pet else "?",
                "Task": task.title,
                "Category": task.category,
                "Priority": task.priority.capitalize(),
                "Minutes": task.duration_mins,
            }
            for task in ordered
        ]
        st.table(rows)
        st.success(
            f"Scheduled {len(plan)} task(s) for {owner.name}."
        )
    else:
        st.warning("No tasks could be scheduled today.")

    st.markdown("### Why this plan")
    st.info(scheduler.get_reasoning_summary())
