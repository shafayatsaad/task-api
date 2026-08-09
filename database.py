import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / "tasks.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        )
        """
    )

    connection.commit()

    count = connection.execute(
        "SELECT COUNT(*) FROM tasks"
    ).fetchone()[0]

    if count == 0:
        connection.executemany(
            """
            INSERT INTO tasks (title, done)
            VALUES (?, ?)
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
    """Convert a SQLite row into a normal Python dictionary."""
    if row is None:
        return None

    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
    }