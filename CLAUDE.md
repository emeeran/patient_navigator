# Patient Navigator Platform

AI-assisted patient care coordination ecosystem.

## Tech Stack
- **Frontend:** React + TypeScript + Tailwind CSS (Vite)
- **Backend:** FastAPI + SQLAlchemy + Alembic
- **Database:** PostgreSQL (dev via Docker)
- **AI:** Ollama (Qwen3, Gemma)
- **OCR:** PaddleOCR
- **Vector Search:** ChromaDB (V2)

## Commands
- **Backend dev:** `cd backend && uvicorn app.main:app --reload --port 8000`
- **Frontend dev:** `cd frontend && npm run dev`
- **Tests:** `cd backend && pytest tests/ -v`
- **Lint:** `cd backend && ruff check . --fix`
- **Migrate:** `cd backend && alembic upgrade head`
- **Docker:** `docker compose up -d`

## Architecture
- SDD workflow: specs → validate → scaffold → implement → test
- 8 feature specs (FEAT-001..008), 51 API specs, 12 data schemas
- See `specs/REGISTRY.md` for full traceability matrix
- See `specs/architecture/ARCH-001-master-plan.md` for comprehensive plan

## Conventions
- Conventional commits: `feat:`, `fix:`, `test:`, `spec:`
- Branch naming: `feature/`, `fix/`, `chore/`
- All tests must reference spec IDs via `@spec` annotations
- Minimum 80% test coverage
- Never commit `.env` files or secrets
