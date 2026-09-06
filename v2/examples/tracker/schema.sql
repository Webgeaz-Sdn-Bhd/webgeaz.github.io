-- MySQL 8.4; H2 tests use MODE=MySQL. Install framework auth SQL first.
CREATE TABLE project (
    id INT PRIMARY KEY AUTO_INCREMENT,
    owner_id VARCHAR(32) NOT NULL,
    name VARCHAR(120) NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES soad_auth_user(id)
);
CREATE INDEX project_owner ON project(owner_id, id);
CREATE TABLE task (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'todo',
    assignee_id VARCHAR(32),
    FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE,
    FOREIGN KEY (assignee_id) REFERENCES soad_auth_user(id),
    CHECK (status IN ('todo', 'doing', 'done'))
);
CREATE INDEX task_project_status ON task(project_id, status, id);
CREATE TABLE attachment (
    id INT PRIMARY KEY AUTO_INCREMENT,
    task_id INT NOT NULL UNIQUE,
    filename VARCHAR(120) NOT NULL,
    content LONGBLOB NOT NULL,
    FOREIGN KEY (task_id) REFERENCES task(id) ON DELETE CASCADE
);
