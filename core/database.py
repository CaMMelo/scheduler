    import sqlite3 as sql

conn = None
cursor = None
connection_name = None

def open_connection(filename):
    
    global conn
    global cursor
    global connection_name

    connection_name = filename
    
    conn = sql.connect(filename)

    temp_str = ''

    for line in conn.iterdump():

        temp_str += line

    conn = sql.connect(':memory:')

    cursor = conn.cursor()

    cursor.executescript(temp_str)

    cursor.execute('PRAGMA foreign_keys = ON')
    conn.isolation_level = None

def close_connection():

    global conn

    temp = ''

    for line in conn.iterdump():

        temp += line

    open(connection_name, 'w').close()

    conn = sql.connect(connection_name)

    conn.cursor().executescript(temp)

    conn.commit()
    conn.close()

def create_database(filename):
    
    open(filename, 'w+').close()
    c = sql.connect(filename).cursor()

    with open('scheme.sql') as script:

        c.executescript(script.read())

def last_id(table):

    try:

        cursor.execute('SELECT seq FROM sqlite_sequence WHERE name=?', [table])
        return cursor.fetchone()[0]

    except:

        return 0

def save_changes():
    
    global conn

    temp = ''

    for line in conn.iterdump():

        temp += line

    open(connection_name, 'w').close()

    con = sql.connect(connection_name)

    con.cursor().executescript(temp)

    con.commit()

    con.close()