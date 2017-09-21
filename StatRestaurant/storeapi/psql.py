from pg import DB, ProgrammingError
from datetime import datetime
from dateutil import tz
from os import environ
utc_timezone = tz.gettz('UTC')
fr_timezone = tz.gettz('Europe/Paris')


def get_current_time():
    return datetime.utcnow().replace(tzinfo=utc_timezone).astimezone(fr_timezone)


class Store:
    def __init__(self):
        self.connection = DB(dbname=environ.get('POSTGRESQL_ADDON_DB'),
                             host=environ.get('POSTGRESQL_ADDON_HOST'),
                             port=environ.get('POSTGRESQL_ADDON_PORT'),
                             user=environ.get('POSTGRESQL_ADDON_USER'),
                             passwd=environ.get('POSTGRESQL_ADDON_PASSWORD '))
        try:
            self.connection.query("SELECT * FROM stats")
        except ProgrammingError:
            print "Create Table"
            self.connection.query("""CREATE TABLE stats (timestamp TIMESTAMP PRIMARY KEY,value NUMERIC(5,2))""")
            # self.connection.query("truncate stats")

    def add(self, value):
        if float(value) > 0.1:
            self.connection.insert('stats', timestamp=get_current_time(), value=value)

    def display(self):
        self.connection.query("SELECT * FROM stats")

    def get_values(self, value='{}-{}-{}'.format(datetime.now().year, datetime.now().month, datetime.now().day)):
        result = self.connection.query(
            "SELECT extract(DOW FROM timestamp)::INT AS dow, timestamp, value FROM stats WHERE timestamp >= '" +
            value + "' AND timestamp < ('" + value + "'::DATE + '1 day'::INTERVAL) ORDER BY 2")
        return result

    def get_average_values(self,
                           value='{}-{}-{}'.format(datetime.now().year, datetime.now().month, datetime.now().day)):
        result = self.connection.query(
            "SELECT extract(DOW FROM timestamp)::INT AS dow, "
            "to_timestamp('" + value + " ' || "
                                       "LPAD(extract(HOUR FROM timestamp)::TEXT,2,'0') || ':' ||"
                                       "        LPAD(extract(MINUTE FROM timestamp)::TEXT,2,'0') ||"
                                       " ':00', 'YYYY-MM-DD HH24:MI:SS') AS timestamp,"
                                       "       round(avg(value)::NUMERIC,2) AS value FROM stats"
                                       " GROUP BY 1,2 ORDER BY 1,2")

        return result
