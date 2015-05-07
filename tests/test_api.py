"""Unit Tests for Twisted EvE API."""
import xml.etree.ElementTree as ET

from twisted.trial import unittest

from eve_api import EvECreds, EvEAPI, EvEResult


class EvEAPITestCase(unittest.TestCase):
    """Main test class."""

    mock_data = {
        'calendar_events': EvEResult(
            ET.fromstring('''<row eventID="15" ownerName="foo"
                eventDate="bar" eventTitle="foobar" duration="1"
                eventText="barfoo"/>'''),
            # Make sure cache won't expire.
            99999999999999.0)
    }

    def setUp(self):
        self.creds = EvECreds('foo', 'bar')
        self.api = EvEAPI(self.creds)

    def test_creds(self):
        """Test Credentials."""
        self.assertEqual(self.creds.keyID, 'foo')
        self.assertEqual(self.creds.vCode, 'bar')

    def test_params(self):
        """Test Parameters."""
        self.assertEqual(self.api.params, '?keyID=foo&vCode=bar')

    def test_events(self):
        """Test Parameters."""
        self.api.cache['calendar_events'] = self.mock_data['calendar_events']
        d = self.api.get_events()
        d.addCallback(self.assertEqual, [
            {'duration': '1',
             'eventDate': 'bar',
             'eventID': '15',
             'eventText': 'barfoo',
             'eventTitle': 'foobar',
             'ownerName': 'foo'}])
        return d
