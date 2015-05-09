# file-encoding: utf-8
"""EvE API for Twisted."""
import calendar
from collections import namedtuple
import time
import shelve
import sys
import xml.etree.ElementTree as ET
import urllib

from twisted.internet import task, defer, reactor
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

    def __init__(self, creds, endpoint=ENDPOINT, db_file=DB_FILE):
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
        self.agent = Agent(reactor, context_factory)

    def get_cred_params(self):
        """Get credentials params for API requests."""
        self.params = '?'+urllib.urlencode(vars(self.creds))

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
        Extract UNIX timestamp from date and time.

        @param value: date and time.
        @type value: string.
        @return value: string.
        """
        tst = calendar.timegm(time.strptime(value, "%Y-%m-%d %H:%M:%S"))
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
        expire = self.get_ts(result.find('cachedUntil').text)
        res = EvEResult(result, expire)
        self.cache[key] = res
        return result

    def _get_api(self, mapping, **kwargs):
        """
        Get elements from cache or API.

        @param mapping: dict of action, key and fields.
        @type : dict.
        @return deferred or cached result.
        """
        action = mapping['action']
        url = self.endpoint + action + self.params
        if kwargs:
            url += '&'+urllib.urlencode(kwargs)
        cache_res = self.cache.get(url)
        if cache_res and not time.time() > cache_res.expire:
            log.msg('Cache Hit: %s.' % time.ctime(cache_res.expire))
            res = self.parse(cache_res.xml, mapping['fields'])
            return res
        else:
            log.msg('Calling API with URL: %s.' % url)
            d = self.agent.request('GET', url)
            d.addCallback(readBody)
            d.addCallback(self.save, url)
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

    def get_contracts(self):
        """
        Get contracts from cache or API.

        @return deferred.
        """
        from mapping import contracts_mapping
        d = defer.maybeDeferred(self._get_api, contracts_mapping)
        return d

    def get_contract_items(self, contract_id):
        """
        Get contracts from cache or API.

        @return deferred.
        """
        from mapping import contract_items_mapping
        d = defer.maybeDeferred(
            self._get_api, contract_items_mapping, contractID=contract_id)
        return d

    def get_corp_contracts(self):
        """
        Get corp contracts from cache or API.

        @return deferred.
        """
        from mapping import corp_contracts_mapping
        d = defer.maybeDeferred(self._get_api, corp_contracts_mapping)
        return d

    def get_corp_contract_items(self, contract_id):
        """
        Get contracts from cache or API.

        @return deferred.
        """
        from mapping import corp_contract_items_mapping
        d = defer.maybeDeferred(
            self._get_api, corp_contract_items_mapping, contractID=contract_id)
        return d


def main(reactor):
    """Main function, testing purposes."""
    log.startLogging(sys.stdout)
    from auth import keyID, vCode
    from auth import corp_keyID, corp_vCode
    creds = EvECreds(keyID, vCode)
    corp_creds = EvECreds(corp_keyID, corp_vCode)
    api = EvEAPI(creds, ENDPOINT, DB_FILE)
    corp_api = EvEAPI(corp_creds, ENDPOINT, 'corp_api.db')
    events = api.get_events()
    contracts = corp_api.get_corp_contracts()
    contracts.addCallback(log.msg)
    events.addCallback(log.msg)
    return defer.DeferredList([contracts, events])

if __name__ == '__main__':
    task.react(main)
