"""
Database connection module for PostgreSQL.

Connection is configured via the DATABASE_URL environment variable.
"""

import os

from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

load_dotenv()

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:dev@localhost:5432/tasks",
)


def get_connection():
    """Return a new PostgreSQL connection."""
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def initialize_database():
    """
    Create the tasks table if it does not exist.

    The three example tasks are inserted only when
    the table is completely empty.
    """
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT FALSE
        )
        """
    )

    connection.commit()

    count = connection.execute(
        "SELECT COUNT(*) FROM tasks"
    ).fetchone()[0]

    if count == 0:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO tasks (title, done)
                VALUES (%s, %s)
                """,
                [
                    ("Buy milk", False),
                    ("Walk the dog", True),
                    ("Finish CRUD assignment", False),
                ],
            )

        connection.commit()

    connection.close()


def row_to_task(row):
    """Convert a PostgreSQL row into a normal Python dictionary."""
    if row is None:
        return None

    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
    }