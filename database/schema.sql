-- SQL-схема информационной системы управления проектами компании

CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    position VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE,
    department VARCHAR(100)
);

CREATE TABLE projects (
    project_id INTEGER PRIMARY KEY,
    project_name VARCHAR(200) NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE,
    status VARCHAR(30) NOT NULL,
    project_manager_id INTEGER,
    FOREIGN KEY (project_manager_id) REFERENCES employees(employee_id)
);

CREATE TABLE tasks (
    task_id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    task_name VARCHAR(200) NOT NULL,
    description TEXT,
    start_date DATE,
    due_date DATE,
    status VARCHAR(30) NOT NULL,
    priority VARCHAR(30),
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE TABLE task_workers (
    task_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    assigned_at DATE,
    PRIMARY KEY (task_id, employee_id),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);
