import os
import socket
import time

host = os.environ.get("DB_HOST", "db")
port = int(os.environ.get("DB_PORT", 3306))
timeout = 2

print(f"Waiting for database at {host}:{port}...")

for _ in range(30):  # Try for 60 seconds
    try:
        with socket.create_connection((host, port), timeout=timeout):
            print("Database is ready!")
            exit(0)
    except (socket.timeout, ConnectionRefusedError, OSError):
        print("Database is not ready yet, waiting...")
        time.sleep(2)

print("Could not connect to the database after 60 seconds. Exiting.")
exit(1)
