from os import environ
from urllib2 import urlopen, build_opener, Request, ProxyHandler, install_opener, URLError
from json import loads

from datetime import datetime

req = Request("https://maif-solutions.moneweb.fr/Communication/Afficheur/RefreshAffluence",
              data='{"widgetId":"1","exploitationId":"1"}',
              headers={"X-Requested-With": "XMLHttpRequest", "Content-Type": "application/json"})


def get_full_data():

    try:
        if "https_proxy" in environ:
            proxy = ProxyHandler({"https": environ.get("https_proxy")})
            opener = build_opener(proxy)
            install_opener(opener)
        datajson = urlopen(req).read()
        return loads(datajson)
    except Exception as e:
        print '[' + str(datetime.now()) + '] - ' + str(e)
        return 0


def get_taux():
    return '{0:.3g}'.format(get_full_data()['affluence']['TauxOccupation'])

