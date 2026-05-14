# Trinetra Backend (`liteRT`)

FastAPI backend with:
- Local LiteRT Gemma model inference (`gemma-4-E2B-it.litertlm`)
- Sentence-transformer embeddings (`all-MiniLM-L6-v2`)
- PostgreSQL + `pgvector`

## Prerequisites

- Docker Desktop (or Docker Engine + Compose)
- Internet access on first run (to download models)

## One-Command Setup

From project root:

```bash
docker compose up --build
```

This command will:
- Build the app image
- Start PostgreSQL (`pgvector/pgvector:pg16`)
- Download required models into `./models` (only if missing)
- Start the FastAPI app on `http://localhost:8000`

## Services

- `app`: FastAPI server (`uvicorn app.main:app`)
- `postgres`: local DB with persistent volume
- `model-init`: one-shot model downloader

## Environment Variables

Compose loads `.env` and also sets a Docker-safe DB URL for the app:

- `DATABASE_URL=postgresql+asyncpg://trinetra:trinetra@postgres:5432/trinetra`

If you want to use your external/cloud Postgres instead, remove the `DATABASE_URL` override from `docker-compose.yml`.

## API Check

- Health endpoint: `GET http://localhost:8000/health`
- Swagger docs: `http://localhost:8000/docs`

## Model Download Notes

`model-init` downloads into `./models`:
- `gemma-4-E2B-it.litertlm`
- `all-MiniLM-L6-v2/`

If files already exist, download is skipped.

## Useful Commands

Start in background:

```bash
docker compose up -d --build
```

View logs:

```bash
docker compose logs -f app
```

Stop services:

```bash
docker compose down
```

Stop and remove DB volume (full reset):

```bash
docker compose down -v
```
