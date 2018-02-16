from . import database as db
from . import scalable_task
from . import DATE_FORMAT, TIME_FORMAT, DATETIME_FORMAT
from datetime import datetime, timedelta, date
from math import ceil

class schedule:

    def __init__(self, id, date):

        self.id = id
        self.date = date

    def add_task(self, name, start, finish):

        return scalable_task.create([self.date], [], name, start, finish)

    def remove_task(self, tid):

        return scalable_task.remove_task_from_schedule(tid, self.date)

    def get_tasks(self):
        
        return get_task_list(self.date)

    def set_date(self, date):

        s = load(date)

        if s:

            self.id = s.id
            self.date = date

    def is_free_time(self, start, finish):

        return is_free_time(self.date, start, finish)

def create(date):

    # try to create a schedule,
    # if a schedule in this date already exists, load it
    # else create the new schedule and put an id to it

    sch = load(date)

    if sch:
        return sch

    sch = validate(date)

    if sch:

        db.cursor.execute('INSERT INTO schedule (date) VALUES (?)', [sch.date])
        sch.id = db.last_id('schedule')

        return sch

def load(date):

    # load the schedule to date
    # if there is no schedule return None

    try:

        db.cursor.execute('SELECT * FROM schedule WHERE date=?', [date])
        data = db.cursor.fetchone()

        sch = schedule(data[0], data[1])

        return sch

    except:

        pass

def validate(date):

    # check if date is valid, if yes:
    # return a new schedule with no id
    # else return None

    try:

        datetime.strptime(date, DATE_FORMAT)

        return schedule(None, date)

    except:

        pass

def remove(date):

    # empty a date

    db.cursor.execute('DELETE FROM schedule WHERE date=?', [date])

def get_task_list(date):

    # return all the tasks marked to date

    db.cursor.execute('''SELECT task.id
        FROM ((task_schedule INNER JOIN scalable_task ON task_id = task.id) 
        INNER JOIN task ON scalable_task.id = task.id)
        INNER JOIN schedule on schedule.id = schedule_id
        WHERE date = ? ORDER BY start''', [date])
    
    tlist = []

    for t in db.cursor.fetchall():

        tlist.append(scalable_task.load(t[0]))

    return tlist

def is_free_time(date, start, finish):

    # check if there is no tasks between start and finish
    # in the given date

    db.cursor.execute(''' SELECT schedule_id, start, finish
        FROM ((scalable_task INNER JOIN task_schedule ON scalable_task.id = task_id)
        INNER JOIN schedule ON schedule.id = schedule_id)
        WHERE (date = ?) AND
        (((start >= ? AND start < ?) OR (finish > ? AND finish <= ?)) OR
        ((? >= start AND ? < finish) OR (? > start AND ? <= finish))) ''',
        [date, start, finish, start, finish, start, start, finish, finish])

    return len(db.cursor.fetchall()) == 0

def get_tasks_until(work_begin, work_end, date_begin, date_end):

    # get the tasks between two datetimes and between
    # the times: work_begin and work_end

    # return a dict, the keys are the dates
    # the values are a list of tuples with the starting and finishing time of each task

    db.cursor.execute('''SELECT date, start, finish from
        (scalable_task inner join task_schedule on scalable_task.id = task_schedule.task_id)
        inner join schedule on schedule.id = task_schedule.schedule_id
        where ((datetime(date, start) between ? and ?) or
        (datetime(date, finish) between ? and ?)) and
        ((start between ? and ?) or (finish between ? and ?))
        order by schedule_id, start''',
        [date_begin, date_end, date_begin, date_end, work_begin, work_end, work_begin, work_end])

    query = db.cursor.fetchall()
    tasks = {}

    for q in query:

        dt = datetime.strptime(q[0], DATE_FORMAT).date()

        if dt not in tasks:

            tasks[dt] = []

        tasks[dt].append(
            (datetime.combine(date.min, datetime.strptime(q[1], TIME_FORMAT).time()),
            (datetime.combine(date.min, datetime.strptime(q[2], TIME_FORMAT).time()))))

    return tasks

def free_time_until(context_duration, work_begin, work_end, date_begin, date_end, time_gap = 20, weekends=True, avoid=[]):

    # get the number of contexts between two datetimes
    # and in each day between work_begin and work_end

    tasks = get_tasks_until(work_begin, work_end, date_begin, date_end)

    date_begin = datetime.strptime(date_begin, DATETIME_FORMAT)
    date_end = datetime.strptime(date_end, DATETIME_FORMAT)
    work_begin = datetime.combine(date.min, datetime.strptime(work_begin, TIME_FORMAT).time())
    work_end = datetime.combine(date.min, datetime.strptime(work_end, TIME_FORMAT).time())

    daydelta = timedelta(1)
    deltatime = timedelta(0, 60 * context_duration)
    time_gap = timedelta(0, 60 * time_gap)

    currentdate = date_begin

    total = 0
    while currentdate <= date_end:

        dt = currentdate.date()

        if ((not weekends) and (dt.weekday() > 4)) or (dt.strftime(DATE_FORMAT) in avoid):
            
            currentdate += daydelta
            continue

        init = datetime.combine(date.min, work_begin.time())
        end = datetime.combine(date.min, work_end.time())

        if dt == date_begin.date():

            currenttime = datetime.combine(date.min, date_begin.time())
            init = max(currenttime, init)

        if dt == date_end.date():

            currenttime = datetime.combine(date.min, date_end.time())
            end = min(currenttime, end)

        if dt in tasks:

            t = tasks[dt]

            finish = init + deltatime

            i = 0
            while (init <= end) and (finish <= end):

                if (i < len(t)) and ((finish + time_gap > t[i][0])) and ((init > t[i][0]) or (init < t[i][1])):

                    init = t[i][1] + time_gap
                    i += 1

                else:

                    init = finish + time_gap
                    total += 1

                finish = init + deltatime
        else:
            
            total += int((end - init).seconds / (60 * (context_duration + time_gap.seconds / 60)) )

        currentdate += daydelta

    return total


def free_contexts_until(context_duration, work_begin, work_end, date_begin, date_end, time_gap = 20, weekends=True, avoid=[]):
    
    # get the contexts between two datetimes
    # and in each day between work_begin and work_end

    # return a list of tuples with the datetime start and finish of each context

    tasks = get_tasks_until(work_begin, work_end, date_begin, date_end)

    date_begin = datetime.strptime(date_begin, DATETIME_FORMAT)
    date_end = datetime.strptime(date_end, DATETIME_FORMAT)
    work_begin = datetime.strptime(work_begin, TIME_FORMAT)
    work_end = datetime.strptime(work_end, TIME_FORMAT)

    daydelta = timedelta(1)
    deltatime = timedelta(0, 60 * context_duration)
    time_gap = timedelta(0, 60 * time_gap)

    currentdate = date_begin

    total = []
    
    while currentdate <= date_end:

        dt = currentdate.date()

        if ((not weekends) and (dt.weekday() > 4)) or (dt.strftime(DATE_FORMAT) in avoid):
            
            currentdate += daydelta
            continue

        init = datetime.combine(date.min, work_begin.time())
        end = datetime.combine(date.min, work_end.time())

        if dt == date_begin.date():

            currenttime = datetime.combine(date.min, date_begin.time())
            init = max(currenttime, init)

        if dt == date_end.date():

            currenttime = datetime.combine(date.min, date_end.time())
            end = min(currenttime, end)

        if dt in tasks:

            t = tasks[dt]

            finish = init + deltatime

            i = 0
            while (init <= end) and (finish <= end):

                if (i < len(t)) and ((finish + time_gap > t[i][0])) and ((init > t[i][0]) or (init < t[i][1])):
                    init = t[i][1] + time_gap
                    i += 1
                else:
                    total.append((datetime.combine(currentdate, init.time()), datetime.combine(currentdate, finish.time())))
                    init = finish + time_gap

                finish = init + deltatime
        else:

            finish = init + deltatime

            while (finish <= end) and (init <= end):

                total.append((datetime.combine(currentdate, init.time()), datetime.combine(currentdate, finish.time())))
                init = finish + time_gap
                finish = init + deltatime

        currentdate += daydelta

    return total

def load_all(restrictions = lambda x: True):

    # return a list of schedules that respects the given restrictions

    db.cursor.execute('SELECT * from schedule')

    slist = []

    for s in db.cursor.fetchall():

        slist.append(schedule(s[0], s[1]))

    return [x for x in filter(restrictions, slist)]
