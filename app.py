from flask import Flask, render_template, request, redirect, url_for, flash
from database import get_connection, init_db

app = Flask(__name__)
app.secret_key = "project-management-secret-key-2026"

# Главная страница системы
@app.route("/")
def index():
    init_db()

    connection = get_connection()

    projects_count = connection.execute(
        "SELECT COUNT(*) FROM projects"
    ).fetchone()[0]

    tasks_count = connection.execute(
        "SELECT COUNT(*) FROM tasks"
    ).fetchone()[0]

    employees_count = connection.execute(
        "SELECT COUNT(*) FROM employees"
    ).fetchone()[0]

    active_tasks = connection.execute(
        "SELECT COUNT(*) FROM tasks WHERE status = 'В работе'"
    ).fetchone()[0]

    connection.close()

    return render_template(
        "index.html",
        projects_count=projects_count,
        tasks_count=tasks_count,
        employees_count=employees_count,
        active_tasks=active_tasks
    )

# Просмотр и добавление сотрудников
@app.route("/employees", methods=["GET", "POST"])
def employees():
    connection = get_connection()

    if request.method == "POST":
        full_name = request.form["full_name"]
        position = request.form["position"]
        email = request.form["email"]

        try:
            connection.execute(
                """
                INSERT INTO employees (full_name, position, email)
                VALUES (?, ?, ?)
                """,
                (full_name, position, email or None)
            )
            connection.commit()
            flash("Сотрудник успешно добавлен!")
        except Exception:
            flash("Ошибка: проверьте данные сотрудника.")

        connection.close()
        return redirect(url_for("employees"))

    employees_list = connection.execute(
        "SELECT * FROM employees ORDER BY id DESC"
    ).fetchall()

    connection.close()

    return render_template(
        "employees.html",
        employees=employees_list
    )

# Просмотр и создание проектов
@app.route("/projects", methods=["GET", "POST"])
def projects():
    connection = get_connection()

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]
        status = request.form["status"]
        manager_id = request.form.get("manager_id") or None

        connection.execute(
            """
            INSERT INTO projects
            (name, description, start_date, end_date, status, manager_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, description, start_date, end_date, status, manager_id)
        )
        connection.commit()
        connection.close()

        flash("Проект успешно создан!")
        return redirect(url_for("projects"))

    projects_list = connection.execute("""
        SELECT projects.*, employees.full_name AS manager_name
        FROM projects
        LEFT JOIN employees ON projects.manager_id = employees.id
        ORDER BY projects.id DESC
    """).fetchall()

    employees_list = connection.execute(
        "SELECT * FROM employees ORDER BY full_name"
    ).fetchall()

    connection.close()

    return render_template(
        "projects.html",
        projects=projects_list,
        employees=employees_list
    )

# Просмотр и создание задач
@app.route("/tasks", methods=["GET", "POST"])
def tasks():
    connection = get_connection()

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        project_id = request.form["project_id"]
        deadline = request.form["deadline"]
        priority = request.form["priority"]
        status = request.form["status"]

        cursor = connection.execute(
            """
            INSERT INTO tasks
            (project_id, title, description, deadline, priority, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (project_id, title, description, deadline, priority, status)
        )

        task_id = cursor.lastrowid

        employee_ids = request.form.getlist("employee_ids")

        for employee_id in employee_ids:
            connection.execute(
                """
                INSERT INTO task_workers (task_id, employee_id)
                VALUES (?, ?)
                """,
                (task_id, employee_id)
            )

        connection.commit()
        connection.close()

        flash("Задача успешно создана!")
        return redirect(url_for("tasks"))

    tasks_list = connection.execute("""
        SELECT
            tasks.*,
            projects.name AS project_name,
            GROUP_CONCAT(employees.full_name, ', ') AS workers
        FROM tasks
        JOIN projects ON tasks.project_id = projects.id
        LEFT JOIN task_workers ON tasks.id = task_workers.task_id
        LEFT JOIN employees ON task_workers.employee_id = employees.id
        GROUP BY tasks.id
        ORDER BY tasks.id DESC
    """).fetchall()

    projects_list = connection.execute(
        "SELECT * FROM projects ORDER BY name"
    ).fetchall()

    employees_list = connection.execute(
        "SELECT * FROM employees ORDER BY full_name"
    ).fetchall()

    connection.close()

    return render_template(
        "tasks.html",
        tasks=tasks_list,
        projects=projects_list,
        employees=employees_list
    )

@app.route("/tasks/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    connection = get_connection()

    task = connection.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    ).fetchone()

    if task is None:
        connection.close()
        flash("Задача не найдена.")
        return redirect(url_for("tasks"))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        project_id = request.form["project_id"]
        deadline = request.form["deadline"]
        priority = request.form["priority"]
        status = request.form["status"]

        connection.execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, project_id = ?,
                deadline = ?, priority = ?, status = ?
            WHERE id = ?
            """,
            (
                title, description, project_id,
                deadline, priority, status, task_id
            )
        )

        connection.execute(
            "DELETE FROM task_workers WHERE task_id = ?",
            (task_id,)
        )

        employee_ids = request.form.getlist("employee_ids")

        for employee_id in employee_ids:
            connection.execute(
                """
                INSERT INTO task_workers (task_id, employee_id)
                VALUES (?, ?)
                """,
                (task_id, employee_id)
            )

        connection.commit()
        connection.close()

        flash("Задача успешно обновлена!")
        return redirect(url_for("tasks"))

    projects_list = connection.execute(
        "SELECT * FROM projects ORDER BY name"
    ).fetchall()

    employees_list = connection.execute(
        "SELECT * FROM employees ORDER BY full_name"
    ).fetchall()

    assigned_employees = connection.execute(
        "SELECT employee_id FROM task_workers WHERE task_id = ?",
        (task_id,)
    ).fetchall()

    assigned_ids = [row["employee_id"] for row in assigned_employees]

    connection.close()

    return render_template(
        "edit_task.html",
        task=task,
        projects=projects_list,
        employees=employees_list,
        assigned_ids=assigned_ids
    )

@app.route("/tasks/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    connection = get_connection()

    connection.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )

    connection.commit()
    connection.close()

    flash("Задача успешно удалена!")
    return redirect(url_for("tasks"))

@app.route("/employees/edit/<int:employee_id>", methods=["GET", "POST"])
def edit_employee(employee_id):
    connection = get_connection()

    employee = connection.execute(
        "SELECT * FROM employees WHERE id = ?",
        (employee_id,)
    ).fetchone()

    if employee is None:
        connection.close()
        flash("Сотрудник не найден.")
        return redirect(url_for("employees"))

    if request.method == "POST":
        full_name = request.form["full_name"]
        position = request.form["position"]
        email = request.form["email"]

        try:
            connection.execute(
                """
                UPDATE employees
                SET full_name = ?, position = ?, email = ?
                WHERE id = ?
                """,
                (full_name, position, email or None, employee_id)
            )

            connection.commit()
            flash("Данные сотрудника успешно обновлены!")

        except Exception:
            connection.rollback()
            flash("Ошибка: возможно, такой email уже используется.")

        connection.close()
        return redirect(url_for("employees"))

    connection.close()

    return render_template(
        "edit_employee.html",
        employee=employee
    )

@app.route("/employees/delete/<int:employee_id>", methods=["POST"])
def delete_employee(employee_id):
    connection = get_connection()

    employee = connection.execute(
        "SELECT * FROM employees WHERE id = ?",
        (employee_id,)
    ).fetchone()

    if employee is None:
        connection.close()
        flash("Сотрудник не найден.")
        return redirect(url_for("employees"))

    connection.execute(
        "DELETE FROM employees WHERE id = ?",
        (employee_id,)
    )

    connection.commit()
    connection.close()

    flash("Сотрудник успешно удалён!")
    return redirect(url_for("employees"))

@app.route("/projects/edit/<int:project_id>", methods=["GET", "POST"])
def edit_project(project_id):
    connection = get_connection()

    project = connection.execute(
        "SELECT * FROM projects WHERE id = ?",
        (project_id,)
    ).fetchone()

    if project is None:
        connection.close()
        flash("Проект не найден.")
        return redirect(url_for("projects"))

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]
        status = request.form["status"]
        manager_id = request.form.get("manager_id") or None

        connection.execute(
            """
            UPDATE projects
            SET name = ?, description = ?, start_date = ?,
                end_date = ?, status = ?, manager_id = ?
            WHERE id = ?
            """,
            (
                name, description, start_date,
                end_date, status, manager_id, project_id
            )
        )

        connection.commit()
        connection.close()

        flash("Проект успешно обновлён!")
        return redirect(url_for("projects"))

    employees_list = connection.execute(
        "SELECT * FROM employees ORDER BY full_name"
    ).fetchall()

    connection.close()

    return render_template(
        "edit_project.html",
        project=project,
        employees=employees_list
    )

@app.route("/projects/delete/<int:project_id>", methods=["POST"])
def delete_project(project_id):
    connection = get_connection()

    project = connection.execute(
        "SELECT * FROM projects WHERE id = ?",
        (project_id,)
    ).fetchone()

    if project is None:
        connection.close()
        flash("Проект не найден.")
        return redirect(url_for("projects"))

    connection.execute(
        "DELETE FROM projects WHERE id = ?",
        (project_id,)
    )

    connection.commit()
    connection.close()

    flash("Проект и связанные с ним задачи успешно удалены!")
    return redirect(url_for("projects"))

if __name__ == "__main__":
    app.run(debug=True)