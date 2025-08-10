# FastAPI Infra Kit
Bunch of tools to quickly bootstrap a FastAPI project with observability stack and database migrations.

## Directory Structure

```
├── app/
│    ├── alembic/             # Database migrations
│    ├── api/                 # API routes
│    ├── core/                # Core app logic (config, db, logging, etc.)
│    ├── envs/                # Environment configs
│    ├── exceptions/          # Custom exception handlers
│    ├── models/              # SQLAlchemy models
│    ├── schemas/             # Pydantic schemas
│    ├── services/            # Business logic
│    └── tests/               # Unit & integration tests
├── scripts/                  # Helper scripts (lint, test, migrate)
├── static/                   # Static files (favicon, etc.)
├── visualization/
│    ├── grafana/             # Grafana configs
│    ├── loki/                # Loki configs
│    ├── prometheus/          # Prometheus configs
│    └── promtail/            # Promtail configs
├── docker-compose.yml        # Docker Compose setup - contains image from ghcr
├── build.docker-compose.yml  # Docker Compose setup - contains build context with Dockerfile
├── sample.docker-compose.env # Docker Compose environment variables for fastapi app, same as the ones from envs. Dummy data.
├── Dockerfile                # App Dockerfile
├── requirements.txt          # Python dependencies
├── pyproject.toml            # Project metadata
└── run_now.sh                # Random script to run the whole app for initial setup.
```

## Features

- FastAPI backend
- SQLAlchemy + Alembic for DB migrations (automatically created)
- Redis integration
- Observability stack: Loki, Prometheus, Grafana, Promtail & Loguru.
- Services are dockerized for easy deployment. You can hot reload the app with proper volume mounts.
- Scripts for linting, testing, and migrations

## Observability Inspiration

Big thanks
to [dimasyotama](https://github.com/dimasyotama/fastapi-observability-dashboard/)
for the Loki/Grafana/Prometheus setup inspiration!

---

Feel free to fork, break, or improve.


