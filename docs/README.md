# Documentation

Project documentation lives here to keep the repo root clean.

| Doc | Description |
|-----|-------------|
| **LOGGING_SYSTEM.md** / **LOGGING_QUICKSTART.md** | Script execution logging and analysis |
| **DATABASE_MIGRATION.md** / **SQLITE_IMPLEMENTATION.md** | DB migration and SQLite setup |
| **OPENAI_INTEGRATION.md** / **SETUP_OPENAI.md** | OpenAI + Gemini AI assistant setup |
| **DUAL_RUNTIME.md** / **QUICKSTART_DUAL_RUNTIME.md** | Docker + Kubernetes runtime |
| **KUBERNETES_MIGRATION.md** | Moving to Kubernetes |
| **IMPLEMENTATION_SUMMARY.md** | Logging system implementation summary |
| **CHANGES_SUMMARY.md** | OpenAI integration summary |
| **VERBOSE_DEBUGGING_WORKFLOW.md** | Debugging workflow |

For deployment and paths (EC2, SSH, Docker Compose), see **CONTEXT.md** in the project root.

**Migration scripts** (e.g. `migrate_to_db.py`, `migrate_images.py`) were moved to `scripts/archive/`. Run from project root:  
`python scripts/archive/migrate_to_db.py`
