from . import database as db
from . import project
from . import task

class project_task(task.task):

    type = task.PROJECT_TASK

    def __init__(self, id, project_id, name, duration, done):

        self.id = id
        self.project_id = project_id
        self.name = name
        self.duration = duration
        self.done = done

    def __str__(self):

        return str(self.project_id) + ' - ' + self.name + ': ' + str(self.duration) + ' minutes, ' + str(bool(self.done)) + '.'

    def set_id(self, id):

        t = load(id)

        if t:

            self.__init__(t.id, t.project_id, t.name, t.duration, t.done)

    def set_duration(self, duration):

        self.duration = update_duration(self.id, self.project_id, duration)

    def set_done(self, done):

        self.done = update_done(self.id, self.project_id, done)

def update_duration(id, pid, duration):

    # update a task with id from project with id = pid to duration
    # if this task does not exists on database or do not belongs to pid
    # return -1, else if duration is less than zero return the current duration
    # of this task, if everything goes correctly returns the new duration

    try:

        db.cursor.execute('SELECT selected from project where id = ? ', [pid])
        selected = db.cursor.fetchone()[0]

        if (duration >= 0) and not selected:

            db.cursor.execute('UPDATE project_task SET duration=? WHERE id=? and project_id = ?', [duration, id, pid])

            project.update_duration(pid)

            return duration

        db.cursor.execute('SELECT duration from project_task WHERE id = ?', [id])
        return db.cursor.fetchone()[0]

    except:

        return -1

def update_done(id, pid, done):

    # mark a task as done or not done, return the new state of the task
    # if the update could not be done return the old state
    # if something goes wrong, return False

    try:

        if ((done == True) or (done == False)):

            db.cursor.execute('UPDATE project_task SET done=? WHERE id=? and project_id = ?', [done, id, pid])

            project.update_progress(pid)

            return done

        db.cursor.execute('SELECT done from project_task where id = ?', [id])
        return db.cursor.fetchone()[0]

    except:

        return False

def create(pid, name, duration, done=False):

    # create a new task to a project, return the new task with an id
    # if something goes wrong return None

    try:

        db.cursor.execute('SELECT selected from project where id = ? ', [pid])
        selected = db.cursor.fetchone()[0]

        t = validate(pid, name, duration, done)

        if t and not selected:

            base = task.create(name, t.type)
            t.id = base.id

            db.cursor.execute('INSERT INTO project_task VALUES(?,?,?,?)', [t.id, pid, duration, done])

            project.update_duration(pid)

            return t

    except:

        pass

def load(id):

    # load a task with id
    # if it does not exists return None

    try:

        db.cursor.execute('SELECT name FROM task WHERE id=?', [id])
        name = db.cursor.fetchone()[0]

        db.cursor.execute('SELECT * FROM project_task WHERE id=?', [id])
        tdata = db.cursor.fetchone()

        return project_task(tdata[0], tdata[1], name, tdata[2], tdata[3])

    except:

        pass

def remove(id, pid):

    # remove the task with id from project with pid

    try:

        db.cursor.execute('SELECT id from project_task where id = ? and project_id = ?', [id, pid])
        check = db.cursor.fetchone()[0]

        db.cursor.execute('SELECT selected from project where id = ? ', [pid])
        selected = db.cursor.fetchone()[0]

        if not selected:

            task.remove(id)
            project.update_duration(pid)

            return True

        return False

    except:

        return False

def validate(pid, name, duration, done):

    # validate a task for a project
    # return a new task without an id if the informations are valid
    # else return None

    db.cursor.execute('SELECT * from project where id = ?', [pid])
    p = db.cursor.fetchone()

    valid = bool(name.strip()) and bool(p)
    valid = valid and duration >= 0
    valid = valid and ((done == True) or (done == False))

    if valid:

        return project_task(None, pid, name, duration, done)

def load_all(restrictions = lambda x: True):

    # load all project tasks

    db.cursor.execute('''SELECT task.id, project_id, name, duration, done
        from project_task inner join task on project_task.id = task.id''')

    tlist = []

    for t in db.cursor.fetchall():

        tlist.append(project_task(t[0], t[1], t[2], t[3], t[4]))

    return [x for x in filter(restrictions, tlist)]