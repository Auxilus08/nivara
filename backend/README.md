# Nivara backend

Install the package and test dependencies from this directory:

```bash
python -m pip install -e '.[test]'
uvicorn app.main:app --reload
pytest
```

The API exposes health at `/health` and `/api/v1/health`. Database sessions are
available through `app.db.session.get_db_session`; feature modules should keep
the API → service → repository → database boundary.
