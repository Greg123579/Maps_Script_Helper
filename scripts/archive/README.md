# Archived scripts

One-off or dev-only scripts moved here to keep the project root clean. Run from **project root** if needed, e.g.:

```bash
python scripts/archive/migrate_to_db.py
python scripts/archive/test_api.py
```

Some scripts assume they are in the project root (e.g. `backend` on the path); if you get import errors, run from the repo root or adjust `sys.path` in the script.

| Script | Purpose |
|--------|---------|
| `migrate_to_db.py` | One-time migration from JSON to SQLite (see docs/DATABASE_MIGRATION.md) |
| `migrate_images.py` | One-time image migration |
| `create_test_data.py` | Create test users in DB |
| `generate_test_users.py` | Generate test users |
| `test_db.py` | Quick DB verification |
| `test_api.py` | API endpoint tests (TestClient) |
| `example_use_logs.py` | Example usage of script logging (see docs/LOGGING_QUICKSTART.md) |
| `b2212364-*.py`, `c91a7a7c-*.py` | Old example/saved script runs |
