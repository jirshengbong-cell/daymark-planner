from __future__ import annotations

import csv
import io
import os
import sqlite3
import uuid
from collections import Counter
from contextlib import contextmanager
from datetime import date, datetime
from html import escape
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Daymark · Daily Planner",
    page_icon="◌",
    layout="wide",
    initial_sidebar_state="auto",
)


CSS = """
<style>
    :root {
        --ink: #18382b;
        --muted: #65756d;
        --paper: #f4f5ef;
        --card: rgba(255, 255, 255, 0.84);
        --line: #dfe5dc;
        --green: #1d6b4d;
        --lime: #cbe383;
        --coral: #e97855;
    }
    .stApp {
        background:
            radial-gradient(circle at 88% 3%, rgba(203, 227, 131, 0.42), transparent 28rem),
            linear-gradient(135deg, #f8f9f4 0%, #f1f4ec 100%);
        color: var(--ink);
    }
    [data-testid="stSidebar"] {
        background: #173d2e;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    [data-testid="stSidebar"] * {
        color: #f5f8f2;
    }
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea {
        color: #18382b !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] * {
        color: #18382b !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.14);
    }
    .block-container {
        max-width: 1180px;
        padding-top: 2.2rem;
        padding-bottom: 4rem;
    }
    h1, h2, h3 {
        color: var(--ink);
        letter-spacing: -0.035em;
    }
    .brand {
        padding: 0.5rem 0 1.25rem;
    }
    .brand-mark {
        width: 38px;
        height: 38px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        background: var(--lime);
        color: #173d2e;
        font-size: 22px;
        font-weight: 800;
        vertical-align: middle;
        margin-right: 10px;
    }
    .brand-name {
        color: #ffffff;
        font-size: 1.4rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        vertical-align: middle;
    }
    .brand-sub {
        color: rgba(255, 255, 255, 0.65) !important;
        font-size: 0.78rem;
        margin: 0.45rem 0 0 50px;
    }
    .hero {
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(24, 56, 43, 0.08);
        border-radius: 28px;
        padding: 2.1rem 2.35rem;
        background: linear-gradient(120deg, rgba(255, 255, 255, 0.95), rgba(237, 245, 218, 0.91));
        box-shadow: 0 24px 70px rgba(36, 69, 52, 0.08);
        margin-bottom: 1.4rem;
    }
    .hero::after {
        content: "";
        position: absolute;
        width: 240px;
        height: 240px;
        border-radius: 50%;
        right: -60px;
        top: -105px;
        border: 46px solid rgba(29, 107, 77, 0.08);
    }
    .eyebrow {
        color: var(--green);
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        margin-bottom: 0.75rem;
    }
    .hero h1 {
        max-width: 720px;
        font-size: clamp(2.25rem, 5vw, 4.4rem);
        line-height: 0.97;
        margin: 0;
        letter-spacing: -0.065em;
    }
    .hero-copy {
        color: var(--muted);
        font-size: 1rem;
        margin: 1rem 0 0;
        max-width: 620px;
    }
    .date-line {
        display: inline-flex;
        gap: 0.5rem;
        align-items: center;
        color: var(--ink);
        font-weight: 700;
        font-size: 0.86rem;
        background: rgba(255, 255, 255, 0.74);
        border: 1px solid var(--line);
        border-radius: 999px;
        padding: 0.45rem 0.75rem;
        margin-top: 1.25rem;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--card);
        border-color: var(--line) !important;
        border-radius: 18px;
        box-shadow: 0 8px 26px rgba(31, 66, 48, 0.035);
    }
    [data-testid="stMetric"] {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 1rem 1.15rem;
        min-height: 112px;
    }
    [data-testid="stMetricLabel"] {
        color: var(--muted);
    }
    [data-testid="stMetricValue"] {
        color: var(--ink);
        font-weight: 800;
        letter-spacing: -0.04em;
    }
    .section-kicker {
        color: var(--green);
        font-size: 0.7rem;
        letter-spacing: 0.13em;
        text-transform: uppercase;
        font-weight: 800;
        margin: 1.4rem 0 0.25rem;
    }
    .task-title {
        color: var(--ink);
        font-weight: 750;
        font-size: 1rem;
        line-height: 1.35;
        margin: 0 0 0.42rem;
    }
    .task-title.done {
        color: #809087;
        text-decoration: line-through;
    }
    .task-meta {
        color: var(--muted);
        font-size: 0.78rem;
        line-height: 1.5;
    }
    .chip {
        display: inline-block;
        border-radius: 999px;
        padding: 0.17rem 0.5rem;
        margin-right: 0.35rem;
        font-size: 0.68rem;
        font-weight: 750;
        line-height: 1.45;
    }
    .chip-work { background: #e4ecfa; color: #314e83; }
    .chip-personal { background: #f8e7de; color: #8c4b33; }
    .chip-learning { background: #eee4f7; color: #68488c; }
    .chip-health { background: #dff0e6; color: #32694a; }
    .priority-high { background: #fde8e2; color: #a74428; }
    .priority-medium { background: #fff0ca; color: #7a5c16; }
    .priority-low { background: #e8eeeb; color: #52665b; }
    .overdue { color: #b44d31; font-weight: 700; }
    .progress-shell {
        height: 10px;
        border-radius: 999px;
        background: #e5eae2;
        overflow: hidden;
        margin: 1.15rem 0 0.6rem;
    }
    .progress-fill {
        height: 100%;
        border-radius: inherit;
        background: linear-gradient(90deg, #1d6b4d, #8cb955);
    }
    .progress-label {
        display: flex;
        justify-content: space-between;
        color: var(--muted);
        font-size: 0.8rem;
    }
    .empty-note {
        border: 1px dashed #bdc9ba;
        border-radius: 18px;
        padding: 1.35rem;
        color: var(--muted);
        background: rgba(255, 255, 255, 0.44);
        text-align: center;
    }
    .sidebar-note {
        color: rgba(255, 255, 255, 0.58) !important;
        font-size: 0.75rem;
        line-height: 1.65;
    }
    .stButton > button,
    .stDownloadButton > button {
        border-radius: 999px;
        border: 1px solid #cbd6cc;
        font-weight: 700;
        transition: transform 120ms ease, border-color 120ms ease;
    }
    .stButton > button:hover,
    .stDownloadButton > button:hover {
        transform: translateY(-1px);
        border-color: var(--green);
        color: var(--green);
    }
    [data-testid="stSidebar"] .stButton > button {
        background: #f7faf5;
        color: #173d2e !important;
        border-color: #f7faf5;
    }
    [data-testid="stSidebar"] .stButton > button * {
        color: #173d2e !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: var(--lime);
        border-color: var(--lime);
    }
    [data-testid="stSidebar"] .stDownloadButton > button {
        background: transparent;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.28);
    }
    [data-testid="stSidebar"] .stDownloadButton > button * {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] .stDownloadButton > button:hover {
        background: rgba(255, 255, 255, 0.1);
        border-color: var(--lime);
    }
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.72);
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 1rem 1.1rem 0.1rem;
    }
    div[data-testid="stForm"] button[kind="primaryFormSubmit"] {
        background: var(--green);
        color: #fff;
        border-color: var(--green);
    }
    .footnote {
        color: #8b978f;
        font-size: 0.75rem;
        margin-top: 2.5rem;
    }
    .mini-chart {
        background: rgba(255, 255, 255, 0.66);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 1rem 1.1rem 0.75rem;
    }
    .mini-row {
        display: grid;
        grid-template-columns: 82px minmax(80px, 1fr) 64px;
        gap: 0.75rem;
        align-items: center;
        min-height: 36px;
    }
    .mini-label {
        color: var(--ink);
        font-size: 0.78rem;
        font-weight: 700;
    }
    .mini-track {
        height: 9px;
        background: #e7ece5;
        border-radius: 999px;
        overflow: hidden;
    }
    .mini-fill {
        height: 100%;
        min-width: 0;
        border-radius: inherit;
    }
    .mini-value {
        color: var(--muted);
        font-size: 0.74rem;
        text-align: right;
        font-variant-numeric: tabular-nums;
    }
    @media (max-width: 700px) {
        .block-container { padding-top: 1.2rem; }
        .hero { padding: 1.5rem 1.35rem; border-radius: 22px; }
        .hero h1 { font-size: 2.55rem; }
    }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

CATEGORIES = ("Work", "Personal", "Learning", "Health")
PRIORITIES = ("High", "Medium", "Low")
PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}
DB_PATH = Path(
    os.environ.get(
        "DAYMARK_DB_PATH",
        Path(__file__).resolve().with_name("daymark.db"),
    )
)


def init_state() -> None:
    defaults = {
        "page": "Today",
        "query": "",
        "category_filter": "All categories",
        "priority_filter": "Any priority",
        "delete_candidate": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


@contextmanager
def database():
    connection = get_connection()
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with database() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                minutes INTEGER NOT NULL,
                due_date TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
            """
        )


def insert_task(task: dict) -> None:
    with database() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO tasks (
                id, title, category, priority, minutes, due_date,
                completed, created_at, completed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task["id"],
                task["title"],
                task["category"],
                task["priority"],
                int(task["minutes"]),
                task["due"],
                int(bool(task["completed"])),
                task["created_at"],
                task["completed_at"],
            ),
        )


def load_tasks() -> list[dict]:
    with database() as connection:
        rows = connection.execute(
            """
            SELECT id, title, category, priority, minutes, due_date AS due,
                   completed, created_at, completed_at
            FROM tasks
            ORDER BY created_at
            """
        ).fetchall()
    return [
        {
            **dict(row),
            "minutes": int(row["minutes"]),
            "completed": bool(row["completed"]),
        }
        for row in rows
    ]


def migrate_legacy_session_tasks() -> None:
    legacy_tasks = st.session_state.pop("tasks", None)
    if not isinstance(legacy_tasks, list):
        return
    for task in legacy_tasks:
        if not isinstance(task, dict) or not task.get("title"):
            continue
        insert_task(
            {
                "id": task.get("id", uuid.uuid4().hex),
                "title": str(task["title"]),
                "category": task.get("category", "Work"),
                "priority": task.get("priority", "Medium"),
                "minutes": int(task.get("minutes", 30)),
                "due": task.get("due", date.today().isoformat()),
                "completed": bool(task.get("completed", False)),
                "created_at": task.get(
                    "created_at",
                    datetime.now().isoformat(timespec="seconds"),
                ),
                "completed_at": task.get("completed_at"),
            }
        )


def add_task(
    title: str,
    category: str,
    priority: str,
    minutes: int,
    due_date: date,
) -> None:
    clean_title = title.strip()
    if not clean_title:
        return
    insert_task(
        {
            "id": uuid.uuid4().hex,
            "title": clean_title,
            "category": category,
            "priority": priority,
            "minutes": int(minutes),
            "due": due_date.isoformat(),
            "completed": False,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "completed_at": None,
        }
    )


def remove_task(task_id: str) -> None:
    with database() as connection:
        connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))


def set_task_completion(task_id: str, completed: bool) -> None:
    with database() as connection:
        connection.execute(
            "UPDATE tasks SET completed = ?, completed_at = ? WHERE id = ?",
            (
                int(completed),
                datetime.now().isoformat(timespec="seconds") if completed else None,
                task_id,
            ),
        )


def remove_completed_tasks() -> None:
    with database() as connection:
        connection.execute("DELETE FROM tasks WHERE completed = 1")


def reset_filters() -> None:
    st.session_state.query = ""
    st.session_state.category_filter = "All categories"
    st.session_state.priority_filter = "Any priority"


def completed_tasks(tasks: list[dict]) -> list[dict]:
    return [task for task in tasks if task["completed"]]


def task_search_blob(task: dict) -> str:
    return " ".join(
        str(task.get(field, ""))
        for field in ("title", "category", "priority", "due")
    ).casefold()


def filtered_tasks(tasks: list[dict]) -> list[dict]:
    query = st.session_state.query.strip().casefold()
    category = st.session_state.category_filter
    priority = st.session_state.priority_filter
    result = []

    for task in tasks:
        if query and query not in task_search_blob(task):
            continue
        if category != "All categories" and task["category"] != category:
            continue
        if priority != "Any priority" and task["priority"] != priority:
            continue
        result.append(task)

    return sorted(
        result,
        key=lambda task: (
            task["completed"],
            task["due"],
            PRIORITY_ORDER.get(task["priority"], 9),
            task["created_at"],
        ),
    )


def export_csv(tasks: list[dict]) -> bytes:
    output = io.StringIO()
    fieldnames = [
        "title",
        "category",
        "priority",
        "estimated_minutes",
        "due_date",
        "completed",
        "completed_at",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for task in tasks:
        writer.writerow(
            {
                "title": task["title"],
                "category": task["category"],
                "priority": task["priority"],
                "estimated_minutes": task["minutes"],
                "due_date": task["due"],
                "completed": "yes" if task["completed"] else "no",
                "completed_at": task["completed_at"] or "",
            }
        )
    return output.getvalue().encode("utf-8-sig")


def render_header(today: date, mode: str) -> None:
    subtitles = {
        "Today": "A focused place for what deserves your attention right now.",
        "Planner": "Your full plan, filtered and ready to reshape.",
        "Insights": "See the shape of your work and make the next day lighter.",
    }
    st.markdown(
        f"""
        <div class="hero">
            <div class="eyebrow">Daymark · {escape(mode)}</div>
            <h1>Make room for<br>what matters.</h1>
            <p class="hero-copy">{escape(subtitles[mode])}</p>
            <div class="date-line">
                <span>◌</span>
                {escape(f"{today:%A}, {today:%B} {today.day}, {today.year}")}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_progress(tasks: list[dict]) -> None:
    completed = sum(1 for task in tasks if task["completed"])
    total = len(tasks)
    percentage = round((completed / total) * 100) if total else 0
    st.markdown(
        f"""
        <div class="progress-shell">
            <div class="progress-fill" style="width: {percentage}%"></div>
        </div>
        <div class="progress-label">
            <span>{completed} of {total} complete</span>
            <span>{percentage}%</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_task(task: dict, today: date) -> None:
    due = date.fromisoformat(task["due"])
    overdue = due < today and not task["completed"]
    date_label = due.strftime("%b %d")
    if due == today:
        date_label = "Today"
    elif overdue:
        date_label = f"Overdue · {date_label}"

    with st.container(border=True):
        check_col, body_col, delete_col = st.columns([0.07, 0.82, 0.11])

        with check_col:
            is_done = st.checkbox(
                f"Mark {task['title']} complete",
                value=task["completed"],
                key=f"done_{task['id']}",
                label_visibility="collapsed",
            )
            if is_done != task["completed"]:
                set_task_completion(task["id"], is_done)
                st.rerun()

        with body_col:
            title_class = "task-title done" if task["completed"] else "task-title"
            category_class = f"chip chip-{task['category'].casefold()}"
            priority_class = f"chip priority-{task['priority'].casefold()}"
            due_class = "overdue" if overdue else ""
            st.markdown(
                f"""
                <div class="{title_class}">{escape(task["title"])}</div>
                <div class="task-meta">
                    <span class="{category_class}">{escape(task["category"])}</span>
                    <span class="{priority_class}">{escape(task["priority"])}</span>
                    &nbsp; {task["minutes"]} min &nbsp;·&nbsp;
                    <span class="{due_class}">{escape(date_label)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with delete_col:
            if st.button(
                "×",
                key=f"delete_{task['id']}",
                help="Delete this task",
                width="stretch",
            ):
                st.session_state.delete_candidate = task["id"]
                st.rerun()


def render_delete_confirmation(tasks: list[dict]) -> None:
    candidate = st.session_state.delete_candidate
    if candidate is None:
        return

    if candidate == "_completed_":
        completed = completed_tasks(tasks)
        if not completed:
            st.session_state.delete_candidate = None
            return
        message = f"Delete all {len(completed)} completed tasks? This cannot be undone."
    else:
        task = next(
            (item for item in tasks if item["id"] == candidate),
            None,
        )
        if task is None:
            st.session_state.delete_candidate = None
            return
        message = f"Delete “{task['title']}”? This cannot be undone."

    st.warning(message)
    confirm_col, cancel_col, _ = st.columns([0.2, 0.2, 0.6])
    if confirm_col.button("Delete", type="primary", key="confirm_delete"):
        if candidate == "_completed_":
            remove_completed_tasks()
        else:
            remove_task(candidate)
        st.session_state.delete_candidate = None
        st.rerun()
    if cancel_col.button("Keep", key="cancel_delete"):
        st.session_state.delete_candidate = None
        st.rerun()


def render_quick_add(today: date) -> None:
    st.markdown('<div class="section-kicker">Quick add</div>', unsafe_allow_html=True)
    starter_tasks = (
        ("Set today’s three priorities", 10, "Work"),
        ("Clear the inbox", 25, "Work"),
        ("Take a 15 minute walk", 15, "Health"),
    )
    cols = st.columns(3)
    for column, (title, minutes, category) in zip(cols, starter_tasks):
        if column.button(
            title,
            key=f"starter_{category}_{minutes}",
            width="stretch",
        ):
            add_task(title, category, "Medium", minutes, today)
            st.rerun()


def render_today(today: date, all_visible: list[dict]) -> None:
    todays_tasks = [
        task for task in all_visible if date.fromisoformat(task["due"]) <= today
    ]
    completed = sum(1 for task in todays_tasks if task["completed"])
    remaining_minutes = sum(
        task["minutes"] for task in todays_tasks if not task["completed"]
    )
    high_priority = sum(
        1
        for task in todays_tasks
        if not task["completed"] and task["priority"] == "High"
    )

    metric_cols = st.columns(4)
    metric_cols[0].metric("Open tasks", len(todays_tasks) - completed)
    metric_cols[1].metric("Focus time", f"{remaining_minutes} min")
    metric_cols[2].metric("High priority", high_priority)
    metric_cols[3].metric(
        "Completion",
        f"{round(completed / len(todays_tasks) * 100) if todays_tasks else 0}%",
    )

    render_progress(todays_tasks)

    if not todays_tasks:
        st.markdown(
            '<div class="empty-note">Your day is open. Add a task below or use a quick start.</div>',
            unsafe_allow_html=True,
        )
        render_quick_add(today)
        return

    st.markdown(
        '<div class="section-kicker">Today’s queue</div>', unsafe_allow_html=True
    )
    for task in todays_tasks:
        render_task(task, today)

    open_count = sum(1 for task in todays_tasks if not task["completed"])
    if open_count == 0:
        st.success("Everything due today is complete. Leave some space for yourself.")

    st.markdown('<div class="section-kicker">Make space</div>', unsafe_allow_html=True)
    render_quick_add(today)


def render_planner(
    today: date,
    all_visible: list[dict],
    all_tasks: list[dict],
) -> None:
    st.markdown(
        """
        <div class="section-kicker">Create a task</div>
        <p style="color:#65756d;margin-top:0">
            Capture the next concrete action. Small, clear steps are easier to start.
        </p>
        """,
        unsafe_allow_html=True,
    )
    with st.form("new_task_form", clear_on_submit=True):
        title = st.text_input(
            "Task",
            placeholder="What needs your attention?",
            max_chars=140,
        )
        row1, row2, row3 = st.columns(3)
        category = row1.selectbox("Category", CATEGORIES)
        priority = row2.selectbox("Priority", ("Medium", "High", "Low"))
        minutes = row3.slider(
            "Estimate",
            min_value=5,
            max_value=180,
            value=30,
            step=5,
            format="%d min",
        )
        due = st.date_input("Due date", value=today)
        submitted = st.form_submit_button(
            "Add to plan", type="primary", width="stretch"
        )

    if submitted:
        if not title.strip():
            st.error("Give the task a short, clear name.")
        else:
            add_task(title, category, priority, minutes, due)
            st.rerun()

    st.markdown(
        f'<div class="section-kicker">All tasks · {len(all_visible)}</div>',
        unsafe_allow_html=True,
    )
    if not all_visible:
        st.markdown(
            '<div class="empty-note">Nothing matches yet. Add a task above or reset the filters.</div>',
            unsafe_allow_html=True,
        )
        return

    for task in all_visible:
        render_task(task, today)

    completed = completed_tasks(all_tasks)
    if completed:  # noqa: SIM102
        if st.button(f"Clear {len(completed)} completed task(s)", key="clear_completed"):
            st.session_state.delete_candidate = "_completed_"
            st.rerun()


def render_distribution_bar(
    counts: Counter,
    labels: tuple[str, ...],
    unit: str,
    color: str,
) -> None:
    maximum = max((counts.get(label, 0) for label in labels), default=0)
    rows = []
    for label in labels:
        value = counts.get(label, 0)
        percentage = round(value / maximum * 100) if maximum else 0
        rows.append(
            f'<div class="mini-row">'
            f'<span class="mini-label">{escape(label)}</span>'
            f'<div class="mini-track" aria-hidden="true">'
            f'<div class="mini-fill" style="width:{percentage}%;background:{color}"></div>'
            f"</div>"
            f'<span class="mini-value">{value} {escape(unit)}</span>'
            f"</div>"
        )
    st.markdown(
        f'<div class="mini-chart">{"".join(rows)}</div>',
        unsafe_allow_html=True,
    )


def render_insights(today: date, all_visible: list[dict]) -> None:
    if not all_visible:
        st.info("Add a few tasks and your progress patterns will appear here.")
        return

    completed = [task for task in all_visible if task["completed"]]
    open_tasks = [task for task in all_visible if not task["completed"]]
    minutes_done = sum(task["minutes"] for task in completed)
    minutes_open = sum(task["minutes"] for task in open_tasks)
    overdue = sum(
        1
        for task in open_tasks
        if date.fromisoformat(task["due"]) < today
    )

    cols = st.columns(4)
    cols[0].metric("Tasks completed", len(completed))
    cols[1].metric("Time completed", f"{minutes_done} min")
    cols[2].metric("Work still open", f"{minutes_open} min")
    cols[3].metric("Overdue", overdue)

    left, right = st.columns(2)
    with left:
        st.subheader("Completion by category")
        category_counts = Counter(task["category"] for task in completed)
        render_distribution_bar(
            category_counts,
            CATEGORIES,
            "done",
            "linear-gradient(90deg, #1d6b4d, #9fc565)",
        )

    with right:
        st.subheader("Focus mix")
        minutes_by_category = Counter()
        for task in all_visible:
            minutes_by_category[task["category"]] += task["minutes"]
        render_distribution_bar(
            minutes_by_category,
            CATEGORIES,
            "min",
            "linear-gradient(90deg, #5e8847, #cbdc85)",
        )

    st.subheader("Priority balance")
    priority_counts = Counter(task["priority"] for task in open_tasks)
    render_distribution_bar(
        priority_counts,
        PRIORITIES,
        "open",
        "linear-gradient(90deg, #d68a4f, #f0c383)",
    )

    total = len(all_visible)
    if total:
        completion_rate = round(len(completed) / total * 100)
        st.caption(
            f"{completion_rate}% of the current filtered plan is complete. "
            "Insights update as you check off tasks."
        )


init_state()
try:
    initialize_database()
    migrate_legacy_session_tasks()
    all_tasks = load_tasks()
except sqlite3.Error:
    st.error(
        "Daymark could not open its local task database. "
        "Check that the app folder is writable, then reload the page."
    )
    st.stop()

now = date.today()
visible_tasks = filtered_tasks(all_tasks)

with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <span class="brand-mark">◌</span>
            <span class="brand-name">Daymark</span>
            <div class="brand-sub">A quieter way to plan</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    page = st.radio(
        "Workspace",
        ("Today", "Planner", "Insights"),
        key="page",
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("VIEW · Filter your plan")
    st.text_input("Search tasks", key="query", placeholder="Search by title…")
    st.selectbox(
        "Category",
        ("All categories",) + CATEGORIES,
        key="category_filter",
    )
    st.selectbox(
        "Priority",
        ("Any priority",) + PRIORITIES,
        key="priority_filter",
    )

    st.button(
        "Reset filters",
        key="reset_filters",
        on_click=reset_filters,
        width="stretch",
    )

    st.divider()
    st.download_button(
        "Export plan as CSV",
        data=export_csv(all_tasks),
        file_name=f"daymark-{now.isoformat()}.csv",
        mime="text/csv",
        disabled=not all_tasks,
        width="stretch",
    )
    st.markdown(
        '<p class="sidebar-note">Your plan is saved automatically in the local '
        "daymark.db database. Export a CSV whenever you want a portable backup.</p>",
        unsafe_allow_html=True,
    )

render_header(now, page)
render_delete_confirmation(all_tasks)

if page == "Today":
    render_today(now, visible_tasks)
elif page == "Planner":
    render_planner(now, visible_tasks, all_tasks)
else:
    render_insights(now, visible_tasks)

st.markdown(
    '<div class="footnote">Daymark keeps the interface simple so the next action stays obvious.</div>',
    unsafe_allow_html=True,
)
