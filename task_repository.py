"""
Task repository — the only place that talks to the database.

Routes in main.py call these functions and never touch SQL directly.
This keeps storage an implementation detail: swapping SQLite for
PostgreSQL later will not change the routes.
"""

from database import get_connection, row_to_task


def get_all_tasks(done=None, search=None):
    """Return all tasks, optionally filtered by done status and/or title search."""
    connection = get_connection()

    query = "SELECT id, title, done FROM tasks"
    conditions = []
    parameters = []

    if done is not None:
        conditions.append("done = %s")
        parameters.append(bool(done))

    if search:
        conditions.append("LOWER(title) LIKE LOWER(%s)")
        parameters.append(f"%{search}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY id"

    rows = connection.execute(query, parameters).fetchall()

    connection.close()

    return [row_to_task(row) for row in rows]


def get_task(task_id):
    """Return a single task by id, or None if it does not exist."""
    connection = get_connection()

    row = connection.execute(
        """
        SELECT id, title, done
        FROM tasks
        WHERE id = %s
        """,
        (task_id,),
    ).fetchone()

    connection.close()

    return row_to_task(row)


def create_task(title):
    """Insert a new task and return it."""
    connection = get_connection()

    row = connection.execute(
        """
        INSERT INTO tasks (title, done)
        VALUES (%s, %s)
        RETURNING id, title, done
        """,
        (title, False),
    ).fetchone()

    connection.commit()

    connection.close()

    return row_to_task(row)


def update_task(task_id, title=None, done=None):
    """
    Update a task's title and/or done status.

    Returns the updated task, or None if the task does not exist.
    """
    connection = get_connection()

    existing = connection.execute(
        """
        SELECT id, title, done
        FROM tasks
        WHERE id = %s
        """,
        (task_id,),
    ).fetchone()

    if existing is None:
        connection.close()
        return None

    # Build the UPDATE dynamically, but only from known column names.
    fields = []
    parameters = []

    if title is not None:
        fields.append("title = %s")
        parameters.append(title)

    if done is not None:
        fields.append("done = %s")
        parameters.append(bool(done))

    # If the request contains no fields, return the existing task.
    if fields:
        parameters.append(task_id)

        query = f"""
            UPDATE tasks
            SET {", ".join(fields)}
            WHERE id = %s
        """

        connection.execute(query, parameters)
        connection.commit()

    row = connection.execute(
        """
        SELECT id, title, done
        FROM tasks
        WHERE id = %s
        """,
        (task_id,),
    ).fetchone()

    connection.close()

    return row_to_task(row)


def delete_task(task_id):
    """Delete a task by id. Returns True if a row was deleted, False otherwise."""
    connection = get_connection()

    cursor = connection.execute(
        """
        DELETE FROM tasks
        WHERE id = %s
        """,
        (task_id,),
    )

    connection.commit()

    deleted = cursor.rowcount

    connection.close()

    return deleted > 0


def get_stats():
    """Return task statistics (total, done, open)."""
    connection = get_connection()

    row = connection.execute(
        """
        SELECT
            COUNT(*) AS total,
            COALESCE(SUM(CASE WHEN done = TRUE THEN 1 ELSE 0 END), 0) AS done
        FROM tasks
        """
    ).fetchone()

    connection.close()

    total = row["total"]
    done = row["done"]

    return {
        "total": total,
        "done": done,
        "open": total - done,
    }


def reset_tasks():
    """Delete all tasks and re-insert the three example tasks."""
    connection = get_connection()

    connection.execute("DELETE FROM tasks")

    connection.executemany(
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