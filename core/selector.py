from . import database as db
from . import project
from . import schedule
from . import DATETIME_FORMAT
from math import ceil
from random import choice as choose
from datetime import datetime, timedelta

alpha = 0.2
max_it = 10

def retrieve(context_size, work_begin, work_end, date_begin, date_end, time_gap = 15, weekends=True, avoid=[]):

    # get all the projects that can be performed until date_end
    # only the projects with a later deadline than date_begin will be selected

    db.cursor.execute('SELECT * FROM project WHERE deadline >= ?', [date_begin])
    db_state = [list(x) for x in db.cursor.fetchall()]

    # remove the projects that the working time is greater than
    # the time between date_begin and the earlier between date_end or its own deadline

    i = 0
    while i < len(db_state):

        max_date = min(datetime.strptime(date_end, DATETIME_FORMAT),
                       datetime.strptime(db_state[i][2], DATETIME_FORMAT)).strftime(DATETIME_FORMAT)

        db_state[i][2] = schedule.free_time_until(context_size, work_begin, work_end, date_begin, max_date, time_gap, weekends, avoid)
        db_state[i][3] = ceil((db_state[i][3] - db_state[i][3] * db_state[i][4]) / context_size)
        db_state[i][6] = bool(db_state[i][6])

        if not (db_state[i][2] > db_state[i][3]):
            del db_state[i]
            i -= 1

        i += 1

    return db_state

def f_objective(solution, db_state):

    # its just the sum of the number of stars
    # of the selected projects in solution

    o = 0
    i = 0

    for s in solution:
        if s:
            o += db_state[i][5]
        i += 1

    return o

def feasible(solution, pack_size, db_state):

    # return if a given solution is feasible

    selected = [db_state[x] for x in filter(lambda x: solution[x], range(len(solution)))]

    duration = sum([x[3] for x in selected])

    fact = duration < pack_size

    i = 1
    for p in selected:

        if not fact:
            break

        for j in selected[i:]:
            fact = fact and (p[3] + j[3]) < max(p[2], j[2])

        i += 1

    return fact

def gen_candidates(solution, pack_size, db_state):

    # given a solution, return all the projects
    # that can be yet selected

    C = [[x, 0] for x in filter(lambda x: (not db_state[x][6]) and (not solution[x]), range(len(solution)))]

    for c in C:
        c[1] = db_state[c[0]][3] / (db_state[c[0]][2] * db_state[c[0]][5])

    selected = [x for x in filter(lambda x: solution[x], range(len(solution)))]

    duration = sum([db_state[x][3] for x in selected])

    i = 0
    while i < len(C):

        c = C[i][0]

        for p in selected:

            if (db_state[c][3] + db_state[p][3]) >= max(db_state[c][2], db_state[p][2]) or (duration + db_state[c][3] >= pack_size):
                del C[i]
                i -= 1
                break

        i += 1

    return C

def greedy_randomized_construction(alpha, pack_size, db_state):

    solution = [x[6] for x in db_state] # copy the original db_state

    C = gen_candidates(solution, pack_size, db_state)

    while len(C) > 0:

        c_max = max([x[1] for x in C])
        c_min = min([x[1] for x in C])

        rcl = [x for x in filter( lambda x: C[x][1] <= c_min + alpha * (c_max - c_min), range(len(C)) )]

        i = choose(rcl)

        solution[C[i][0]] = True

        del C[i]

        # atualizar a lista de candidatos e os pesos
        C = gen_candidates(solution, pack_size, db_state)

    return solution

def local_search(s_initial, pack_size, db_state, max_it):

    # make random constructions max_it times
    # and return the best of them

    s_best = s_initial
    o_best = f_objective(s_best, db_state)

    i = 0
    while i < max_it:

        s_local = greedy_randomized_construction(1, pack_size, db_state)
        o_local = f_objective(s_local, db_state)

        if o_local > o_best:
            s_best = s_local
            o_best = o_local

        i += 1

    return s_best

def save_solution(db_state, s_optimal):

    # save the solution in the database

    for p, selected in zip(db_state, s_optimal):
        project.update_selected(p[0], selected)
        p[6] = selected

def select(context_size, work_begin, work_end, date_begin, date_end, time_gap = 15, weekends=True, avoid=[]):

    # perform the GRASP algorithm to make a good selection of projects

    # this is done as an adaptation of the knapspack problem
    # the only aditional restriction to the problem is that there cant be
    # any project that is overlaped with some other project, i.e., given two
    # distincts projects there must be enough time to solve them both until
    # the later deadline

    # the pack capacity is the amount of free contexts from date_begin til date_end
    # respecting the working time, defined with work_begin, work_end

    # a context is the amount of time (in minutes) to work on each project

    # NOTE: this will respect the given handly selected projects, i.e., if the user
    # already have selected some to be performed, it will be performed anyway
    # if the users selection is invalid, no aditional selection will be done

    # return True if the selection is valid, otherwise return False

    # get the informations
    db_state = retrieve(context_size, work_begin, work_end, date_begin, date_end)
    pack_size = schedule.free_time_until(context_size, work_begin, work_end, date_begin, date_end, time_gap, weekends, avoid)

    s_optimal = []
    o_optimal = 0

    i = 0

    while i < max_it:

        s_local = greedy_randomized_construction(alpha, pack_size, db_state)
        s_local = local_search(s_local, pack_size, db_state, 10)
        o_local = f_objective(s_local, db_state)

        if o_local > o_optimal:

            s_optimal = s_local
            o_optimal = o_local

        i += 1

    save_solution(db_state, s_optimal)

    return feasible(s_optimal, pack_size, db_state)
