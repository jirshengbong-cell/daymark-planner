import os
import sqlite3
import tempfile
from pathlib import Path

from streamlit.testing.v1 import AppTest

TEST_DIRECTORY = tempfile.TemporaryDirectory()
TEST_DATABASE = Path(TEST_DIRECTORY.name) / "daymark-test.db"
os.environ["DAYMARK_DB_PATH"] = str(TEST_DATABASE)


def reset_database() -> None:
    for suffix in ("", "-wal", "-shm"):
        Path(f"{TEST_DATABASE}{suffix}").unlink(missing_ok=True)


def make_app(reset: bool = True) -> AppTest:
    if reset:
        reset_database()
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=15)
    app.run()
    return app


def task_rows() -> list[sqlite3.Row]:
    connection = sqlite3.connect(TEST_DATABASE)
    try:
        connection.row_factory = sqlite3.Row
        return connection.execute("SELECT * FROM tasks").fetchall()
    finally:
        connection.close()


def test_app_renders_initial_today_view() -> None:
    app = make_app()

    assert not app.exception
    assert app.radio[0].value == "Today"
    assert any("Make room for" in block.value for block in app.markdown)


def test_task_can_be_added_and_completed() -> None:
    app = make_app()
    app.radio[0].set_value("Planner").run()

    next(widget for widget in app.text_input if widget.label == "Task").set_value(
        "Verify the planner"
    )
    next(button for button in app.button if button.label == "Add to plan").click().run()

    assert not app.exception
    rows = task_rows()
    assert len(rows) == 1
    assert rows[0]["title"] == "Verify the planner"
    assert rows[0]["completed"] == 0

    app.checkbox[0].set_value(True).run()

    assert not app.exception
    rows = task_rows()
    assert rows[0]["completed"] == 1
    assert rows[0]["completed_at"] is not None


def test_tasks_survive_a_new_app_instance() -> None:
    app = make_app()
    app.radio[0].set_value("Planner").run()
    next(widget for widget in app.text_input if widget.label == "Task").set_value(
        "Keep this after closing"
    )
    next(button for button in app.button if button.label == "Add to plan").click().run()

    reopened_app = make_app(reset=False)

    assert not reopened_app.exception
    assert any(
        "Keep this after closing" in block.value
        for block in reopened_app.markdown
    )


def test_insights_view_handles_a_populated_plan() -> None:
    app = make_app()
    app.radio[0].set_value("Planner").run()
    next(widget for widget in app.text_input if widget.label == "Task").set_value(
        "Plan the week"
    )
    next(button for button in app.button if button.label == "Add to plan").click().run()
    app.radio[0].set_value("Insights").run()

    assert not app.exception
    assert any("Focus mix" in item.value for item in app.subheader)


if __name__ == "__main__":
    checks = (
        test_app_renders_initial_today_view,
        test_task_can_be_added_and_completed,
        test_tasks_survive_a_new_app_instance,
        test_insights_view_handles_a_populated_plan,
    )
    for check in checks:
        check()
        print(f"PASS: {check.__name__}")
