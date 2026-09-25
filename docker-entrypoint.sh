#!/bin/bash
set -e

echo "Waiting for PostgreSQL database to become accessible..."
python -c "
import time, sys
from sqlalchemy import create_engine, text
url = '${DATABASE_URL}'
for i in range(30):
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('PostgreSQL connection established successfully.')
        sys.exit(0)
    except Exception as e:
        print(f'Waiting for DB ({i+1}/30)... {e}')
        time.sleep(1)
sys.exit(1)
"

echo "Applying Alembic database migrations..."
alembic upgrade head

echo "Seeding initial models, accounts, and demo vitals..."
python scripts/init_db.py || true

echo "Starting Intelligent Diabetes Risk Predictor server on port 8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
