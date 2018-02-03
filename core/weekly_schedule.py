from . import database as db
from . import scalable_task
from . import schedule
from . import DATE_FORMAT
from datetime import datetime, timedelta

class weekly_schedule:

	def __init__(self, id, name):

		self.id = id
		self.name = name

	def set_name(self, name):

		self.name = update_name(name)

	def add_task(self, wdays, name, start, finish):

		return scalable_task.create([], [self.id] + wdays, name, start, finish)

	def remove_task(self, tid):

		return scalable_task.remove_task_from_weekly_schedule(tid)

	def get_tasks(self, wday):

		return get_task_list(self.id, wday)

	def enable(self, date_begin, date_end):

		enable_schedule(self.id, date_begin, date_end)

	def disable(self, date_begin, date_end):

		disable_schedule(self.id, date_begin, date_end)


def create(name):

    # create a new schedule with an id

	schedule = validate(name)

	if schedule:

		db.cursor.execute('INSERT INTO weekly_schedule(name) VALUES (?)', [name])
		schedule.id = db.last_id('weekly_schedule')

		return schedule

def load(id):

    # load the schedule with id

	try:

		db.cursor.execute('SELECT * FROM weekly_schedule WHERE id = ?', [id])
		sdata = db.cursor.fetchone()

		return weekly_schedule(sdata[0], sdata[1])

	except:

		pass

def validate(name):

    # validate the given informations, return a new schedule
    # without an id, if something goes wrong return None

	if name.strip():

		return weekly_schedule(None, name)

def remove(id):

    # remove the schedule
    # note: this wont unschedule the tasks related to this

	db.cursor.execute('DELETE FROM weekly_schedule WHERE id = ?', [id])

def update_name(id, name):

    # try to change the name of this schedule
    # return the new name
    # if something goes wrong return the old name

    if name.strip():

        db.cursor.execute('UPDATE weekly_schedule SET name = ? WHERE id = ?', [name, id])

        return name

    try:

        db.cursor.execute('SELECT name FROM weekly_schedule WHERE id = ?', [id])
        return db.cursor.fetchone()[0]

    except:

        return 'Unnamed'

def get_task_list(id, wday):

	# return a list with the tasks of the schedule with id
	# in wday

    db.cursor.execute('''SELECT task_id 
        FROM weekly_recurrence INNER JOIN schedule_id WHERE schedule_id = ? and week_day = ?''', [id, wday])

    tlist = []

    for t in db.cursor.fetchall():

        tlist.append(scalable_task.load(t[0]))

    return tlist

def is_free_time(id, wday, start, finish):

	# check if there is no tasks between start and finish
	# in wday of schedule with id

    db.cursor.execute('''SELECT *
        FROM (scalable_task INNER JOIN weekly_recurrence ON scalable_task.id = task_id)
        INNER JOIN weekly_schedule ON weekly_schedule.id = ?
        WHERE (week_day = ?) AND
        (((start >= ? AND start < ?) OR (finish > ? AND finish <= ?)) OR
        ((? >= start AND ? < finish) OR (? > start AND ? <= finish)))''',
        [id, wday, start, finish, start, finish, start, start, finish, finish])

    return len(db.cursor.fetchall()) == 0

def enable_schedule(id, date_begin, date_end):

	# take the weekly schedule recurrence table
    # and place the tasks to be executed between two dates

    a = datetime.strptime(date_begin, DATE_FORMAT)
    b = datetime.strptime(date_end, DATE_FORMAT)

    db.cursor.execute('''SELECT task_weekly_schedule.task_id, week_day FROM weekly_recurrence
        INNER JOIN task_weekly_schedule ON task_weekly_schedule.task_id = weekly_recurrence.task_id
        WHERE schedule_id = ?''', [id])
    data = db.cursor.fetchall()

    week = [
        [ x[0] for x in filter(lambda x: x[1] == 0, data) ], # 0 monday
        [ x[0] for x in filter(lambda x: x[1] == 1, data) ], # 1 tuesdeay
        [ x[0] for x in filter(lambda x: x[1] == 2, data) ], # 2 wednesday
        [ x[0] for x in filter(lambda x: x[1] == 3, data) ], # 3 thursday
        [ x[0] for x in filter(lambda x: x[1] == 4, data) ], # 4 friday
        [ x[0] for x in filter(lambda x: x[1] == 5, data) ], # 5 saturday
        [ x[0] for x in filter(lambda x: x[1] == 6, data) ]  # 6 sunday
    ]

    while a <= b:

        schedule_id = schedule.create(a.strftime(DATE_FORMAT)).id

        day = a.weekday()

        for t in week[day]:
            
            try:

                db.cursor.execute('INSERT INTO task_schedule VALUES(?, ?)', [schedule_id, t])
            
            except:
                
                pass

        a += timedelta(1)

def disable_schedule(id, date_begin, date_end):

	# remove the tasks of the weekly schedule recurrence table
    # between the given dates

    try:

        db.cursor.execute('SELECT task_id FROM task_weekly_schedule WHERE schedule_id = ?', [id])
        tasks = [x[0] for x in db.cursor.fetchall()]

        db.cursor.execute('SELECT id FROM schedule WHERE date BETWEEN ? and ?', [date_begin, date_end])
        schedules = [x[0] for x in db.cursor.fetchall()]

        for s in schedules:

            for t in tasks:

                db.cursor.execute('DELETE FROM task_schedule WHERE task_id = ? AND schedule_id = ?', [t, s])

        return True

    except:

        return False

def load_all(restrictions = lambda x: True):

    # return all the schedules that respects the
    # given restrictions

    db.cursor.execute('SELECT * FROM weekly_schedule')
    slist = []

    for s in db.cursor.fetchall():

        slist.append(weekly_schedule(s[0], s[1]))

    return [x for x in filter(restrictions, slist)]