from . import database as db
from . import schedule
from . import task
from . import project_task
from . import scalable_task
from . import DATETIME_FORMAT
from datetime import datetime

STARS_MIN = 1
STARS_MAX = 10

class project:

    def __init__(self, id, name, deadline, duration, progress, stars, selected):

        self.id = id
        self.name = name
        self.deadline = deadline
        self.duration = duration
        self.progress = progress
        self.stars = stars
        self.selected = selected

    def __str__(self):

        return self.name + ': ' + self.deadline + ', ' + str(self.progress) + '% complete. ' + '*' * self.stars

    def set_id(self, id):

        p = load(id)

        if p:

            self.__init__(p.id, p.name, p.deadline, p.duration, p.progress, p.stars, p.selected)

    def set_name(self, name):

        self.name = update_name(self.id, name)

    def set_deadline(self, deadline):

        self.deadline = update_deadline(self.id, deadline)

    def set_stars(self, stars):

        self.stars = update_stars(self.id, stars)

    def set_selected(self, selected):

        self.selected = update_selected(self.id, selected)

    def get_tasks(self):

        return get_task_list(self.id)

    def schedule(self, contexts):

        schedule_project(self.id, contexts)

    def unschedule(self):

        if unschedule_project(self.id):
            self.set_selected(False)

    def add_task(self, name, duration, done=False):

        task = project_task.create(self.id, name, duration, done)

        if task:

            self.duration += duration

        return task

    def remove_task(self, tid):

        project_task.remove(tid, self.id)

def update_name(id, name):

    # change the name of a project
    # return the new name,
    # if something goes wrong return 'Unnamed'

    if name.strip():

        db.cursor.execute('UPDATE project SET name=? WHERE id=? and selected = 0', [name, id])

        return name

    try:

        db.cursor.execute('SELECT name FROM project WHERE id = ?', [id])

        return db.cursor.fetchone()[0]

    except:

        return 'Unnamed'

def update_deadline(id, deadline):

    # change the deadline of a project
    # return the new deadline

    try:

        datetime.strptime(deadline, DATETIME_FORMAT)
        db.cursor.execute('UPDATE project set deadline=? WHERE id=? and selected = 0', [deadline, id])

        return deadline

    except:

        try: # deadline is not a valid deadline

            db.cursor.execute('SELECT deadline FROM project WHERE id = ?', [id])

            return db.cursor.fetchone()[0]

        except:

            # project does not exists

            pass

def update_duration(id):

    # update the project duration
    # return the duration updated
        
    db.cursor.execute('SELECT sum(duration) FROM project_task WHERE project_id=?', [id])
    duration = db.cursor.fetchone()[0]

    if duration == None:
        duration = 0

    db.cursor.execute('SELECT sum(duration) FROM project_task WHERE project_id=? and done=1', [id])
    done = db.cursor.fetchone()[0]

    if not done:
        done = 0

    progress = 0

    if (duration > 0) and (done > 0):
        progress = done / duration * 100

    db.cursor.execute('UPDATE project SET duration=?, progress=? WHERE id=?', [duration, progress, id])

    return duration

def update_progress(id):

    # update the project progress
    # return the updated progress

    db.cursor.execute('SELECT sum(duration) FROM project WHERE id=?', [id])
    duration = db.cursor.fetchone()[0]

    if not duration:
        duration = 0

    db.cursor.execute('SELECT sum(duration) FROM project_task WHERE project_id=? and done=1', [id])
    done = db.cursor.fetchone()[0]

    if not done:
        done = 0

    progress = 0

    if (duration > 0) and (done > 0):
        progress = done / duration * 100

    db.cursor.execute('UPDATE project SET progress=? WHERE id=?', [progress, id])

    return progress

def update_stars(id, stars):

    # update the number of stars of a project
    # return the new number of stars

    if (stars >= STARS_MIN) and (stars <= STARS_MAX):

        db.cursor.execute('UPDATE project set stars=? WHERE id=? and selected == 0', [stars, id])

        return stars

    try:
    
        db.cursor.execute('SELECT stars FROM project WHERE id = ?', [id])

        return db.cursor.fetchone()[0]

    except:

        return 0

def update_selected(id, selected):

    # update the selected state of a project
    # return the new state

    if selected == True:

        db.cursor.execute('UPDATE project set selected = 1 WHERE id = ? and selected = 0', [id])

        return selected

    try:

        db.cursor.execute('SELECT selected from project WHERE id = ?', [id])
        selected = db.cursor.fetchone()[0]

        if selected == 2:

            unschedule_project(id)

        db.cursor.execute('UPDATE project set selected = 0 WHERE id = ?', [id])

        return selected
    
    except:

        return False

def create(name, deadline, stars, selected=False):

    # create and save a new project
    # return the projected created with a new id

    proj = validate(name, deadline, stars, selected)

    if proj:

        db.cursor.execute('''INSERT INTO project (name, deadline, progress, duration, stars, selected)
            VALUES(?,?,?,?,?,?)''', [ name, deadline, 0, 0, stars, selected ])

        proj.id = db.last_id('project')

        return proj

def load(id):

    # return the project related to id
    # return none if this id is not registered

    try:

        db.cursor.execute('SELECT * FROM project WHERE id=?', [id])
        data = db.cursor.fetchone()

        proj = project(data[0], data[1], data[2], data[3], data[4], data[5], data[6])

        return proj

    except:

        pass

def remove(id):

    # remove a project and all the related tasks

    tlist = get_task_list(id)

    for task in tlist:
        db.cursor.execute('DELETE FROM task WHERE id=?', [task.id])

    unschedule_project(id)

    db.cursor.execute('DELETE FROM project WHERE id=?', [id])

def validate(name, deadline, stars, selected):

    # check if those parameters corresponds to a valid
    # project, if yes return a new project without a id
    # if no, return None

    try:

        datetime.strptime(deadline, DATETIME_FORMAT)

        valid = True
        valid = valid and bool(name.strip())
        valid = valid and (stars >= STARS_MIN) and (stars <= STARS_MAX)
        valid = valid and (selected >= 0) and (selected <= 2)

        if valid:

            return project(None, name, deadline, 0, 0, stars, selected)
    
    except:

        pass

def get_task_list(id):

    # load the tasks related to the project with id
    # if this project does not exists or have no tasks, a empty list is returned
    # else the tasks are loaded into a list

    db.cursor.execute('''SELECT task.id, name, duration, done
        from (project_task inner join task on task.id = project_task.id) where project_id = ?''', [id])

    tlist = []

    for t in db.cursor.fetchall():

        tlist.append(project_task.project_task(t[0], id, t[1], t[2], t[3]))

    return tlist

def schedule_project(id, contexts = {}):

    try:

        db.cursor.execute('SELECT selected, name from project where id = ?', [id])
        v, name = db.cursor.fetchone()

        if v == 1:

            db.cursor.execute('BEGIN')

            for date, conts in contexts.items():

                for t in conts:

                    if schedule.is_free_time(date, t[0], t[1]):

                        tid = scalable_task.create([date], [], name, t[0], t[1]).id
                        db.cursor.execute('INSERT INTO scalable_task_project VALUES(?, ?)', [tid, id])

                    else:

                        db.cursor.execute('ROLLBACK')
                        return

            db.cursor.execute('UPDATE project set selected = 2 where id = ?', [id])
            db.cursor.execute('COMMIT')

        else:

            pass

    except:

        pass

def unschedule_project(id):

    # remove this project from all the schedules

    try:

        db.cursor.execute('SELECT selected from project where id = ?', [id])
        v = db.cursor.fetchone()[0]

        if v == 2:

            db.cursor.execute('UPDATE project set selected = 0 where id = ?', [id])
            db.cursor.execute('SELECT task_id from scalable_task_project where project_id = ?', [id])

            tasks = [x[0] for x in db.cursor.fetchall()]

            for t in tasks:

                task.remove(t)

        return True

    except:

        return False

def load_all(restrictions = lambda x: True):

    # load all projects
    
    db.cursor.execute('SELECT * from project')

    plist = []

    for p in db.cursor.fetchall():

        plist.append(project(p[0], p[1], p[2], p[3], p[4], p[5], p[6]))

    return [x for x in filter(restrictions, plist)]