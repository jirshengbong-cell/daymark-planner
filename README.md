# Daymark

A focused daily planner built with Streamlit. It supports task capture, due-date
and priority filtering, completion tracking, quick-start tasks, progress
insights, and CSV export.

## Run locally

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL Streamlit prints, usually `http://localhost:8501`.

## Test

```powershell
python tests/test_app.py
```

## Notes

- Tasks are saved automatically in the local `daymark.db` SQLite database.
- Data survives browser closes, page reloads, and Streamlit restarts.
- Use **Export plan as CSV** in the sidebar to keep a portable backup.
- All task actions work without a backend or external service.
- Daymark is designed as a single-user local app. A public multi-user
  deployment would need authentication and user-scoped storage.
