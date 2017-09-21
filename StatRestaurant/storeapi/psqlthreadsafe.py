import pgdb as dbapi2
# import psycopg2 as dbapi2
# from datetime import datetime
from dateutil import tz

utc_timezone = tz.gettz('UTC')
fr_timezone = tz.gettz('Europe/Paris')

db = dbapi2.connect(database='statsrestaurant',
                    host='localhost:5432',
                    user='statsrestaurant',
                    password='statsrestaurant')


cur = db.cursor()
cur.execute("SELECT * FROM stats")
rows = cur.fetchall()
for i, row in enumerate(rows):
    print "Row", i, "value = ", row

try:
    cur = db.cursor()
    cur.execute("SELECT * FROM stats")
except dbapi2.ProgrammingError:
    print "Create Table"
    db.rollback()
    cur.execute("""CREATE TABLE stats (timestamp TIMESTAMP PRIMARY KEY,value NUMERIC(5,2))""")
    db.commit()
    # self.connection.query("truncate stats")