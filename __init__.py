from core import database as db
from core import weekly_schedule
from core import schedule

context_size = 120 # 2 hours
work_begin = '08:00'
work_end = '22:40'

dt_begin = '2018-03-05 00:00'
dt_end = '2018-07-13 00:00'

# db.create_database('CaMMelo.sqlite')
db.open_connection('CaMMelo.sqlite')

# schedule = weekly_schedule.create('IFMG 2018.1')
#
# schedule.add_task([2,4], 'Probabilidade e Estatistica', '20:40', '22:40')
# schedule.add_task([3,4], 'Engenharia de Software I', '08:00', '10:20')
# schedule.add_task([1,2], 'Inteligencia Artificial', '08:00', '10:20')
# schedule.add_task([0], 'Laboratório de Sistema Digitais', '07:00', '09:00')
# schedule.add_task([0], 'Redes I', '10:20', '12:20')
# schedule.add_task([1], 'Redes I', '13:30', '15:30')
# schedule.add_task([2,4], 'Seminários', '13:30', '15:30')
# schedule.add_task([2,4], 'Teoria da Computação', '10:20', '12:20')
# schedule.add_task([1,3], 'Desenvolvimento Rápido em Linux', '15:50', '17:50')
# schedule.add_task([2,3], 'Programação em Assembly', '18:30', '20:30')

# schedule.enable('2018-03-05', '2018-07-13')

time = schedule.free_contexts_until(context_size, work_begin, work_end, dt_begin, dt_end)

for t in time:

    print(t)

print(len(time))

db.close_connection()
