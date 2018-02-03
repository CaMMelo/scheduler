CREATE TABLE IF NOT EXISTS  project (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  deadline DATETIME NOT NULL,
  duration INT NOT NULL,
  progress FLOAT NOT NULL,
  stars INT NOT NULL,
  selected BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS  task(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  type INT NOT NULL
);

CREATE TABLE IF NOT EXISTS  project_task (
  id INT NOT NULL,
  project_id INT NOT NULL,
  duration INT NOT NULL,
  done BOOLEAN NOT NULL,
  FOREIGN KEY(id) REFERENCES task(id) ON DELETE CASCADE,
  FOREIGN KEY(project_id) REFERENCES project(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS  schedule (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  'date' DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS  scalable_task(
  id INT NOT NULL,
  start DATETIME NOT NULL,
  finish DATETIME NOT NULL,
  FOREIGN KEY(id) REFERENCES task(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS task_schedule(
  schedule_id INT NOT NULL,
  task_id INT NOT NULL,
  PRIMARY KEY(schedule_id, task_id),
  FOREIGN KEY(schedule_id) REFERENCES schedule(id) ON DELETE CASCADE,
  FOREIGN KEY(task_id) REFERENCES task(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS weekly_schedule (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS task_weekly_schedule(
  schedule_id INT NOT NULL,
  task_id INT NOT NULL,
  CONSTRAINT task_unique UNIQUE(task_id),
  FOREIGN KEY(schedule_id) REFERENCES weekly_schedule(id) ON DELETE CASCADE,
  FOREIGN KEY(task_id) REFERENCES task(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS weekly_recurrence (
  task_id INT NOT NULL,
  week_day INT NOT NULL, /* 0-6 | monday-sunday */
  PRIMARY KEY (task_id, week_day),
  FOREIGN KEY(task_id) REFERENCES task(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scalable_task_project (
  task_id INT NOT NULL,
  project_id INT NOT NULL,
  PRIMARY KEY(task_id, project_id),
  FOREIGN KEY(task_id) REFERENCES task(id) ON DELETE CASCADE,
  FOREIGN KEY(project_id) REFERENCES project(id) ON DELETE CASCADE
);