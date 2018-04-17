from . import database as db
from . import task
from . import schedule
from . import weekly_schedule
from . import TIME_FORMAT
from datetime import datetime

class scalable_task(task.task):

    type = task.SCALABLE_TASK

    def __init__(self, id, schedules, wdays, name, start, finish):

        self.id = id
        self.schedules = schedules
        self.wdays = wdays
        self.name = name
        self.start = start
        self.finish = finish

    def __str__(self):

        return self.start + ' - ' + self.finish + ': ' + self.name

    def set_id(self, id):

        t = load(id)

        if t:

            self.__init__(t.id, t.schedules, t.wdays, t.name, t.start, t.finish)

    def set_start(self, start):

        self.start = update_start(self.id, start)

    def set_finish(self, finish):

        self.finish = update_finish(self.id, finish)

    def add_to_schedule(self, date):

        add_task_to_schedule(self.id, date)
        self.schedules = self.get_schedules()

    def remove_from_schedule(self, date):

        remove_task_from_schedule(self.id, date)
        self.schedules = self.get_schedules()

    def add_to_weekly_schedule(self, sid, wdays):

        add_task_to_weekly_schedule(self.id, sid, wdays)
        self.wdays = self.get_weekly_recurrence()

    def remove_from_weekly_schedule(self, sid):

        remove_task_from_weekly_schedule(self.id)
        self.wdays = self.get_weekly_recurrence()

    def get_schedules(self):

        return get_task_schedules(self.id)

    def get_weekly_recurrence(self):

        return get_task_weekly_recurrence(self.id)

    def get_weekly_schedule(self):

        return get_task_weekly_schedule(self.id)

def update_start(id, start):

    # update the start time for a task with id
    # return the new start time if everything goes right
    # return the old start time if cannot update
    # return '00:00' in case this task does not exists

    try:

        db.cursor.execute('SELECT finish FROM scalable_task WHERE id = ?', [id])
        finish = db.cursor.fetchone()[0]

        schedules = get_schedules(id)
        wdays = get_weekly_recurrence(id)

        valid = True

        for s in schedules:

            valid = valid and schedule.is_free_time(s, start, finish)

            if not valid:
                
                break

        for d in wdays:

            if not valid:

                break

            valid = valid and schedule.weekly_is_free_time(d, start, finish)

        if valid:

            db.cursor.execute('UPDATE scalable_task SET start=? WHERE id=?', [start, id])

            return start

        db.cursor.execute('SELECT start from scalable_task where id = ?', [id])
        return db.cursor.fetchone()[0]

    except:

        return '00:00'

def update_finish(id, finish):

    # update the start time for a task with id
    # return the new start time if everything goes right
    # return the old start time if cannot update
    # return '00:00' in case this task does not exists

    try:

        db.cursor.execute('SELECT start FROM scalable_task WHERE id = ?', [id])
        start = db.cursor.fetchone()[0]

        schedules = get_schedules(id)
        wdays = get_weekly_recurrence(id)

        valid = True

        for s in schedules:

            valid = valid and schedule.is_free_time(s, start, finish)

            if not valid:
                
                break

        for d in wdays:

            if not valid:

                break

            valid = valid and schedule.weekly_is_free_time(d, start, finish)

        if valid:

            db.cursor.execute('UPDATE scalable_task SET finish=? WHERE id=?', [finish, id])

            return finish

        db.cursor.execute('SELECT finish from scalable_task where id = ?', [id])
        return db.cursor.fetchone()[0]

    except:

        return '00:00'

def create(schedules, wdays, name, start, finish):

    # create a new task with and id
    # if something goes wrong return None
    # else return the new task

    t = validate(schedules, wdays, name, start, finish)

    if t:

        base = task.create(name, t.type)
        t.id = base.id

        db.cursor.execute('INSERT INTO scalable_task VALUES(?, ?, ?)', [t.id, start, finish])

        for s in schedules:
            id = schedule.create(s).id # load if exists create if not
            db.cursor.execute('INSERT INTO task_schedule VALUES(?,?)', [id, t.id])

        try:

            db.cursor.execute('INSERT INTO task_weekly_schedule VALUES(?, ?)', [wdays[0], t.id])

            for d in wdays[1:]:
                    
                db.cursor.execute('INSERT INTO weekly_recurrence VALUES(?, ?)', [t.id, d])

        except:

            pass

        return t

def load(id):

    # load a task with this id
    # if something goes wrong return None
    # else return the loaded task

    try:

        db.cursor.execute('SELECT name FROM task WHERE id=?', [id])
        name = db.cursor.fetchone()[0]

        schedules = get_task_schedules(id)
        wdays = get_task_weekly_recurrence(id)

        db.cursor.execute('SELECT * FROM scalable_task WHERE id=?', [id])
        tdata = db.cursor.fetchone()

        return scalable_task(tdata[0], schedules, wdays, name, tdata[1], tdata[2])

    except:

        pass

def get_task_schedules(id):

    # return the date of the schedules that this
    # task is on

    db.cursor.execute('SELECT date FROM task_schedule INNER JOIN schedule ON schedule_id = id WHERE task_id=?', [id])
    schedules = [x[0] for x in db.cursor.fetchall()]

    return schedules

def get_task_weekly_recurrence(id):

    # get the days of the week in wich this task is executed

    db.cursor.execute('SELECT week_day FROM weekly_recurrence WHERE task_id = ?', [id])
    wdays = [x[0] for x in db.cursor.fetchall()]

    return wdays

def get_task_weekly_schedule(id):

    try:

        db.cursor.execute('''SELECT weekly_schedule.id, name 
            FROM weekly_schedule INNER JOIN task_weekly_schedule ON weekly_schedule.id = schedule_id
            WHERE task_id = ?''', [id])

        s = db.cursor.fetchone()

        return weekly_schedule.weekly_schedule(s[0], s[1])

    except:

        pass

def validate(schedules, wdays, name, start, finish):

    # check if the given information are from a valid task
    # if yes return a task without an id
    # else return None

    try:

        a = datetime.strptime(start, TIME_FORMAT)
        b = datetime.strptime(finish, TIME_FORMAT)

        valid = bool(name.strip())
        valid = valid and (a < b)

        for s in schedules:

            if not valid:
                
                break

            valid = valid and schedule.is_free_time(s, start, finish)

        for d in wdays[1:]:

            if not valid:

                break

            valid = valid and weekly_schedule.is_free_time(wdays[0], d, start, finish)

        if valid:

            return scalable_task(None, schedules, wdays, name, start, finish)

    except:

        pass

def add_task_to_schedule(id, date):

    try:

        db.cursor.execute('SELECT start, finish FROM scalable_task WHERE id = ?', [id])
        start, finish = db.cursor.fetchone()

        if schedule.is_free_time(date, start, finish):

            sid = schedule.create(date).id

            db.cursor.execute('INSERT INTO task_schedule VALUES (?, ?)', [sid, id])

            return True

        return False

    except:

        return False

def add_task_to_weekly_schedule(id, sid, wdays):

    try:

        db.cursor.execute('SELECT start, finish FROM scalable_task WHERE id = ?', [id])
        start, finish = db.cursor.fetchone()

        ok = True

        for d in wdays:

            ok = ok and weekly_schedule.is_free_time(sid, d, start, finish)

        if ok:

            db.cursor.execute('INSERT INTO task_weekly_schedule VALUES(?, ?)', [sid, id])

            for d in wdays:

                db.cursor.execute('INSERT INTO weekly_recurrence VALUES (?, ?)', [id, d])

            return True

        return False

    except:

        return False

def remove_task_from_schedule(id, date):

    try:

        db.cursor.execute('SELECT id FROM schedule WHERE date = ?', [date])
        sid = db.cursor.fetchone()[0]

        db.cursor.execute('DELETE FROM task_schedule WHERE task_id = ? AND schedule_id = ?', [id, sid])

        return True

    except:

        return False

def remove_task_from_weekly_schedule(id):

    db.cursor.execute('DELETE FROM task_weekly_schedule WHERE task_id = ?', [id])
    db.cursor.execute('DELETE FROM weekly_recurrence WHERE task_id = ?', [id])

def load_all(restrictions = lambda x: True):

    # load all tasks that respects the given restrictions

    db.cursor.execute('''SELECT task.id, name, duration, done
        from scalable_task inner join task on scalable_task.id = task.id''')

    tlist = []

    for t in db.cursor.fetchall():

        schedules = get_schedules(t[0])
        wschedule = get_weekly_schedule(t[0]).id
        wdays = get_weekly_recurrence(t[0])

        if wschedule:

            wdays = [wschedule] + wdays

        tlist.append(scalable_task(t[0], schedules, wdays, t[1], t[2], t[3]))

    return [x for x in filter(restrictions, tlist)]
