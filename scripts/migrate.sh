#!/bin/bash
PYTHONPATH=. .venv/bin/alembic -c app/alembic/alembic.ini "$@"