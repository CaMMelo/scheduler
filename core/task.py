from . import database as db

PROJECT_TASK = 0
SCALABLE_TASK = 1

class task:

    def __init__(self, id, name, type):

        self.id = id
        self.name = name
        self.type = type

    def set_name(self, name):

        self.name = update_name(self.id, name)

    def set_id(self, id):

        t = load(id)

        if t:

            self.__init__(t.id, t.name, t.type)

def update_name(id, name):

    # try to update a task name
    # if success return the new name
    # return the old name if something goes wrong

    if name.strip():

        db.cursor.execute('UPDATE task SET name=? WHERE id=?', [name, id])

        return name

    try:

        db.cursor.execute('SELECT name from task where id = ?', [id])
        return db.cursor.fetchone()[0]

    except:

        return 'Unnamed'

def create(name, type):

    # create a new task with an id

    t = validate(name, type)

    if t:

        db.cursor.execute('INSERT INTO task (name, type) VALUES(?,?)', [name, type])
        t.id = db.last_id('task')

        return t

def load(id):

    # load the task related to id

    try:

        db.cursor.execute('SELECT * FROM task WHERE id=?', [id])
        data = db.cursor.fetchone()

        return task(data[0], data[1], data[2])

    except:

        pass

def remove(id):

    # remove the task related to id
    # note: this will remove the task from all schedules, weekly schedules, projects, etc...

    db.cursor.execute('DELETE FROM task WHERE id=?', [id])

def validate(name, type):

    # validate the given information
    # if everything is ok return a new task without an id
    # else return None

    valid = bool(name.strip())
    valid = valid and ((type == PROJECT_TASK) or (type == SCALABLE_TASK))

    if valid:

        return task(None, name, type)

def load_all(restrictions = lambda x: True):

    # load all the tasks that respects restrictions
    
    db.cursor.execute('SELECT * FROM task')
    tlist = []

    for t in db.cursor.fetchall():

        tlist.append(task(t[0], t[1], t[2]))

    return [x for x in filter(restrictions, tlist)]