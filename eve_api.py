#file-encoding: utf-8
"""EvE API for Twisted."""
import calendar
from collections import namedtuple
import time
import shelve
import sys
import xml.etree.ElementTree as ET

from twisted.internet import task, defer
from twisted.python import log
from twisted.web.client import Agent, WebClientContextFactory, readBody


ENDPOINT = 'https://api.eveonline.com'
DB_FILE = 'eve_api.db'


EvECreds = namedtuple('EvECreds', ['keyID', 'vCode'])
EvEResult = namedtuple('EvEResult', ['xml', 'expire'])


class EvEAPI(object):
    """
    Wrapped around EvE API.
    Returns deferred with dict from cache or endpoint API.
    """

    def __init__(self, creds, endpoint, db_file):
        """
        @param creds: API Credentials.
        @type creds: EvECreds.
        @param endpoint: API endpoint.
        @type endpoint: string.
        @param db_file: filename for cache db.
        @type db_file: string.
        """
        self.creds = creds
        self.get_cred_params()
        self.endpoint = endpoint
        self.cache = shelve.open(db_file)
        context_factory = WebClientContextFactory()
        from twisted.internet import reactor
        self.agent = Agent(reactor, context_factory)

    def get_cred_params(self):
        """Get credentials params for API requests."""
        self.params = '?'+'&'.join(
            ('keyID='+self.creds.keyID, 'vCode='+self.creds.vCode))

    @staticmethod
    def parse(result, fields):
        """
        Create dict from xml results.

        @param result: xml results.
        @type result: xml Element.
        @param fields: fields to retrieve.
        @type fields: list of strings.
        """
        res = []
        for elem in result.iter('row'):
            att = elem.attrib
            elem_dict = {}
            for field in fields:
                elem_dict[field] = att[field]
            res.append(elem_dict)
        return res

    @staticmethod
    def get_ts(value):
        """
        Extract UNIX timestamp from xml Element.

        @param value: xml Element.
        @type value: xml Element.
        @return value: string.
        """
        tst = calendar.timegm(time.strptime(value.text, "%Y-%m-%d %H:%M:%S"))
        return tst

    def save(self, result, key):
        """
        Save result in cache database.

        @param result: xml string.
        @type result: string.
        @param key: save key.
        @type key: string.
        """
        result = ET.fromstring(result)
        expire = self.get_ts(result.find('cachedUntil'))
        res = EvEResult(result, expire)
        self.cache[key] = res
        return result

    def _get_api(self, mapping):
        """
        Get elements from cache or API.

        @param mapping: dict of action, key and fields.
        @type : dict.
        @return deferred.
        """
        cache_res = self.cache.get(mapping['key'])
        if cache_res and not time.time() > cache_res.expire:
            log.msg('Cache Hit:', time.ctime(cache_res.expire))
            res = self.parse(cache_res.xml, mapping['fields'])
            return res
        else:
            log.msg('Cache Miss')
            action = mapping['action']
            url = self.endpoint + action + self.params
            d = self.agent.request('GET', url)
            d.addCallback(readBody)
            d.addCallback(self.save, mapping['key'])
            d.addCallback(self.parse, mapping['fields'])
            return d

    def get_events(self):
        """
        Get events from cache or API.

        @return deferred.
        """
        from mapping import calendar_events_mapping
        d = defer.maybeDeferred(self._get_api, calendar_events_mapping)
        return d


def main(reactor):
    """Main function, testing purposes."""
    log.startLogging(sys.stdout)
    from auth import keyID, vCode
    creds = EvECreds(keyID, vCode)
    api = EvEAPI(creds, ENDPOINT, DB_FILE)
    events = api.get_events()
    events.addCallback(log.msg)
    return events

if __name__ == '__main__':
    task.react(main)
