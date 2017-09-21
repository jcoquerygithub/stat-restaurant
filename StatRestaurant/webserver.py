#!/usr/bin/env python
# -*- coding: UTF-8
from SimpleHTTPServer import SimpleHTTPRequestHandler
from datetime import datetime
from json import dumps
from threading import Event, Thread
from clientapi import restaurant
from storeapi.psql import Store
from dateutil import tz
from os import environ
import BaseHTTPServer
import signal
import sys
import urlparse

utc_timezone = tz.gettz('UTC')
fr_timezone = tz.gettz('Europe/Paris')


def get_current_time():
    return datetime.utcnow().replace(tzinfo=utc_timezone).astimezone(fr_timezone)


def log(data):
    print '[' + str(get_current_time()) + '] - ' + data


class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)


class RequestHandler(SimpleHTTPRequestHandler):
    def list_directory(self, path):
        # No no no...
        # pass
        SimpleHTTPRequestHandler.list_directory(self, path)

    def log_message(self, format, *args):
        """
        Override logging to write into logger
        :param format:
        :param args:
        """
        message = "[%s] - %s - - %s" % (self.log_date_time_string(), self.client_address[0], format % args)
        print message

    def end_headers(self):
        """
        To deal with CORS
        """
        self.send_header("Access-Control-Allow-Origin", "*")
        SimpleHTTPRequestHandler.end_headers(self)

    def do_GET(self):
        weekday_name = [
            "Lundi", "Mardi",
            "Mercredi", "Jeudi", "Vendredi",
            "Samedi", "Dimanche"
        ]
        # Parse query data & params to find out what was passed
        parsed_params = urlparse.urlparse(self.path)
        query_parsed = urlparse.parse_qs(parsed_params.query)

        if parsed_params.path == '/data':
            rows = []
            store = Store()
            if 'date' in query_parsed:
                date_arg = query_parsed.get('date')[0]
                current_dow = datetime.strptime(date_arg, '%Y-%m-%d').weekday()
                values = store.get_values(date_arg).namedresult()
                average_values = store.get_average_values(date_arg).namedresult()
            else:
                current_dow = datetime.now().weekday()
                values = store.get_values().namedresult()
                average_values = store.get_average_values().namedresult()
            try:
                # Ajout de +1 sur le dow car psql 0=Dimanche et python(current_dow) 0=Lundi
                average_values = [t for t in average_values if t.dow == current_dow + 1]
            except Exception, e:
                log(average_values)
                log(e.message)
                
            for r in average_values:
                current_values = [t for t in values if
                                  t.dow == r.dow and
                                  t.timestamp.hour == r.timestamp.hour and
                                  t.timestamp.minute == r.timestamp.minute]
                # les moyennes sont sur la minutes, donc 1 mesure par minute
                # les valeurs sont toutes les 30 secondes donc jusqu'a deux par minutes
                # les valeurs peuvent ne pas être là pour cette minutes (en cours par exemple)
                # Si on a deux valeurs, on met 2 fois la même moyenne sinon si 1 valeurs
                # alors 1 moyenne sinon 1 moyenne et pas de valeur.
                if len(current_values) == 1 or len(current_values) == 2:
                    rows.append({"c": [{"v": 'Date(%d,%d,%d,%d,%d,%d)' % (r.timestamp.year,
                                                                          r.timestamp.month - 1,
                                                                          r.timestamp.day,
                                                                          r.timestamp.hour,
                                                                          r.timestamp.minute,
                                                                          current_values[0].timestamp.second)},
                                       {"v": '%d' % current_values[0].value},
                                       {"v": '%d' % r.value}]})
                else:
                    rows.append({"c": [{"v": 'Date(%d,%d,%d,%d,%d,%d)' % (r.timestamp.year,
                                                                          r.timestamp.month - 1,
                                                                          r.timestamp.day,
                                                                          r.timestamp.hour,
                                                                          r.timestamp.minute,
                                                                          r.timestamp.second)},
                                       {"v": None},
                                       {"v": '%d' % r.value}]})

                if len(current_values) == 2:
                    rows.append({"c": [{"v": 'Date(%d,%d,%d,%d,%d,%d)' % (r.timestamp.year,
                                                                          r.timestamp.month - 1,
                                                                          r.timestamp.day,
                                                                          r.timestamp.hour,
                                                                          r.timestamp.minute,
                                                                          current_values[1].timestamp.second)},
                                       {"v": '%d' % current_values[1].value},
                                       {"v": '%d' % r.value}]})

            data = {"cols": [
                {"id": "A", "label": "X", "type": "datetime"},
                {"id": "B", "label": "Taux d'occupation", "type": "number"},
                {"id": "B", "label": "Taux d'occupation moyen d'un " + weekday_name[current_dow], "type": "number"}
            ], 'rows': rows}
            result = dumps(data)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(result)
            store.connection.close()
        else:
            SimpleHTTPRequestHandler.do_GET(self)


class Data(Thread):
    def __init__(self, event):
        Thread.__init__(self)
        self.stopped = event

    def run(self):
        while not self.stopped.wait(30):
            start_date = get_current_time().replace(hour=11, minute=45, second=0)
            stop_date = get_current_time().replace(hour=14, minute=15, second=0)
            if start_date < get_current_time() < stop_date:
                try:
                    store = Store()
                    current_taux = restaurant.get_taux()
                    store.add(current_taux)
                    store.connection.close()
                except Exception, e:
                    log(e.message)


def signal_term_handler(signal, frame):
    stopping_server()


def stopping_server():
    log('Stopping Server')
    server.server_close()
    stopFlag.set()
    sys.exit(0)


if __name__ == '__main__':
    sys.stdout = Unbuffered(sys.stdout)
    signal.signal(signal.SIGTERM, signal_term_handler)
    log('Starting Server')
    server = BaseHTTPServer.HTTPServer(('0.0.0.0', int(environ.get('PORT'))), RequestHandler)
    stopFlag = Event()
    thread = Data(stopFlag)
    thread.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        stopping_server()
    except Exception, e:
        log(e.message)
