#!/bin/sh

echo "Waiting for database..."
python3 wait_for_db.py

# Check the exit code of the wait script
if [ $? -ne 0 ]; then
    echo "Database wait script failed. Exiting."
    exit 1
fi

echo "Running database migrations..."
alembic upgrade head

echo "Starting bot..."
python3 main.py
