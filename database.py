import sqlite3

DATABASE = "company.db"


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    connection = get_connection()

    connection.executescript("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            position TEXT NOT NULL,
            email TEXT UNIQUE
        );

        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            start_date TEXT,
            end_date TEXT,
            status TEXT NOT NULL DEFAULT 'Планируется',
            manager_id INTEGER,
            FOREIGN KEY (manager_id)
                REFERENCES employees(id)
                ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            deadline TEXT,
            priority TEXT NOT NULL DEFAULT 'Средний',
            status TEXT NOT NULL DEFAULT 'Новая',
            FOREIGN KEY (project_id)
                REFERENCES projects(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS task_workers (
            task_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            PRIMARY KEY (task_id, employee_id),
            FOREIGN KEY (task_id)
                REFERENCES tasks(id)
                ON DELETE CASCADE,
            FOREIGN KEY (employee_id)
                REFERENCES employees(id)
                ON DELETE CASCADE
        );
    """)

    connection.commit()
    connection.close()


if __name__ == "__main__":
    init_db()
    print("База данных успешно создана!")