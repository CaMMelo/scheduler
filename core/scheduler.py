from . import database as db
from . import schedule as sch
from . import scalable_task
from . import DATE_FORMAT, TIME_FORMAT, DATETIME_FORMAT
from datetime import datetime
from math import exp, ceil
from random import uniform, choice as choose

alpha = 0.9
max_it = 100
t_initial = 400
t_final = 50

def retrieve(context_duration, work_begin, work_end, date_begin, date_end, time_gap = 15, weekends=True, avoid=[]):

    # get all the selected projects to be schedules
    # this will get only the projects that can be performed between
    # date_begin and date_end

    db.cursor.execute('SELECT * FROM project WHERE selected == 1 ORDER BY deadline')
    projects = [list(x) for x in db.cursor.fetchall()]

    i = 0
    while i < len(projects):

        deadline = min(datetime.strptime(projects[i][2], DATETIME_FORMAT), datetime.strptime(date_end, DATETIME_FORMAT))
        free = sch.free_time_until(context_duration, work_begin, work_end, date_begin, deadline.strftime(DATETIME_FORMAT), time_gap, weekends, avoid)
        projects[i][2] = datetime.strptime(projects[i][2], '%Y-%m-%d  %H:%M')
        projects[i][3] = ceil((projects[i][3] - projects[i][3] * projects[i][4]) / context_duration)

        if not (free > projects[i][3]):

            del projects[i]
            i -= 1

        i += 1

    return projects

def f_objective(solution, context, projects):

    # IDEA: adjust the benefit and penality with machine-learning algorithms

    objective = 0

    for i in range(1, len(solution)):

        if solution[i] != solution[i-1]:
            objective += 2
        else:
            objective -= 1

    return objective

def f_neighboor(solution, context, projects):

    # swap one context of each project

    s_neigh = solution[:]

    i = 0
    while i < len(projects):

        try:

            # choose someone to be swaped randomly

            a = choose([x for x in filter(lambda x: solution[x] == i, range(len(solution)))])
            p = s_neigh[a]

            # look for everybody that a can be in its place
            # and everyone who can be in place of a
            b = filter(lambda x: s_neigh[x] != s_neigh[a], range(len(s_neigh)))
            b = filter(lambda x: projects[p][2] >= context[x][1], b)
            b = filter(lambda x: (s_neigh[x] == None) or (projects[s_neigh[x]][2] >= context[a][1]), b)

            # choose someone randomly from that set
            b = choose([x for x in b])

            s_neigh[a], s_neigh[b] = s_neigh[b], s_neigh[a]

        except:

            pass

        # swap someone of next project
        i += 1

    return s_neigh

def save_solution(solution, projects, contexts):

    # save a given solution to the database
    
    print(solution)

    schedules = {}

    for c in contexts:

        date = c[0].strftime(DATE_FORMAT)

        if date not in schedules:
            schedules[date] = sch.create(date).id
    
    esc = []

    i = 0
    for s in solution:

        if s == None:
            i += 1
            continue

        sch_ = contexts[i][0].strftime(DATE_FORMAT)
        start = contexts[i][0].strftime(TIME_FORMAT)
        finish = contexts[i][1].strftime(TIME_FORMAT)
        name = projects[s][1]

        id = scalable_task.create([sch_,], [], name, start, finish).id

        db.cursor.execute('INSERT INTO scalable_task_project VALUES(?, ?)', [id, projects[s][0]])

        if projects[s][0] not in esc:
            esc.append(projects[s][0])

        i += 1

    for e in esc:
        db.cursor.execute('UPDATE project SET selected = 2 WHERE id = ?', [e])


def schedule(context_duration, work_begin, work_end, date_begin, date_end, time_gap = 15, weekends=True, avoid=[]):

    # execute the simulated annealing algorithm to find more approppriated
    # times to executed the tasks of each selected project

    # get the necessary informations
    projects = retrieve(context_duration, work_begin, work_end, date_begin, date_end)
    contexts = sch.free_contexts_until(context_duration, work_begin, work_end, date_begin, date_end, time_gap, weekends, avoid)

    # NOTE: check if there is no conflicts with the selected projects
    # if there is some abort the scheduling

    # mount the initial solution
    s_best = []

    i = 0
    for p in projects:
        s_best += [i] * p[3]
        i += 1

    # fill the solution with blank
    s_best += [None] * (len(contexts) - len(s_best))
    o_best = f_objective(s_best, contexts, projects)

    s_local = s_best[:]
    o_local = o_best

    temp = t_initial

    # S.A main loop

    while temp > t_final:

        i = 0

        while i < max_it:

            s_neigh = f_neighboor(s_local, contexts, projects)
            o_neigh = f_objective(s_local, contexts, projects)

            delta = o_local - o_neigh

            if delta < 0:

                s_local = s_neigh
                o_local = o_neigh

                if o_best < o_neigh:

                    s_best = s_neigh
                    o_best = o_neigh

            else:

                if uniform(0, 1) < exp(-delta / temp):

                    s_local = s_neigh
                    o_local = o_neigh

            i += 1
            temp *= alpha

    save_solution(s_best, projects, contexts)

    # return the solution
    return s_best
