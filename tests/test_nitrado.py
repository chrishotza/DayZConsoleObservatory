"""Offline verification: Nitrado integration requires no token or network."""
import io
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from dayz_observatory.nitrado import NitradoClient, NitradoError, MAX_LOG_BYTES, MAX_API_BYTES

ROOT = '/games/tester/noftp/dayzxb/config'
FILE = ROOT + '/Test.ADM'


class FakeResponse:
    def __init__(self, data: bytes):
        self.data = io.BytesIO(data)
    def read(self, size=-1):
        return self.data.read(size)
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False


class NitradoTests(unittest.TestCase):
    def setUp(self):
        self.client = NitradoClient('offline-fixture')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dest = Path(self.tmp.name) / 'test.ADM'
        self.token_response = {'data': {'token': {'url': 'https://files.nitrado.net/download?id=1', 'token':'one-use'}}}

    def test_no_token(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(NitradoError):
                NitradoClient()

    def test_invalid_token_rejected(self):
        with self.assertRaises(NitradoError):
            NitradoClient('token\nHeader: bad')

    def test_wrong_game_rejected(self):
        with patch.object(self.client, 'gameserver', return_value={'game':'dayz','username':'foo'}):
            with self.assertRaises(NitradoError):
                self.client.discover_log_directory(123)

    def test_xbox_directory(self):
        with patch.object(self.client, 'gameserver', return_value={'game':'dayzxb','username':'tester'}):
            directory,_ = self.client.discover_log_directory(123)
        self.assertEqual(directory, ROOT)

    def test_reject_traversal_username(self):
        with patch.object(self.client, 'gameserver', return_value={'game':'dayzxb','username':'../../other'}):
            with self.assertRaises(NitradoError):
                self.client.discover_log_directory(123)

    def test_service_id_positive(self):
        with self.assertRaises(ValueError):
            self.client.gameserver(-1)

    def test_reject_unsafe_remote_paths_before_api(self):
        paths = ['/secret/OTHER.ADM', ROOT+'/../other.ADM', ROOT+'/subdir/x.ADM', ROOT+'/x.RPT\\evil']
        with patch.object(self.client, '_json') as remote:
            for path in paths:
                with self.subTest(path=path), self.assertRaises(NitradoError):
                    self.client.download_log(123, path, self.dest, ROOT)
            remote.assert_not_called()

    def test_list_excludes_unsafe_entries(self):
        entries = [
            {'name':'one.ADM', 'path':ROOT+'/one.ADM','type':'file'},
            {'name':'notes.txt','path':ROOT+'/notes.txt','type':'file'},
            {'name':'dir.ADM','path':ROOT+'/dir.ADM','type':'directory'},
            {'name':'../evil.ADM','path':ROOT+'/../evil.ADM','type':'file'},
            {'name':'outside.RPT','path':'/other/outside.RPT','type':'file'},
        ]
        with patch.object(self.client, '_json', return_value={'data':{'entries':entries}}):
            self.assertEqual([e['name'] for e in self.client.list_logs(123,ROOT)],['one.ADM'])

    def test_api_rejects_oversized_response(self):
        with patch.object(self.client,'_open',return_value=FakeResponse(b'x'*(MAX_API_BYTES+1))):
            with self.assertRaisesRegex(NitradoError, '2 MiB'):
                self.client._json('/services/1/gameservers')

    def test_api_rejects_non_dict_json(self):
        with patch.object(self.client,'_open',return_value=FakeResponse(b'[1,2,3]')):
            with self.assertRaisesRegex(NitradoError, 'response shape'):
                self.client._json('/services/1/gameservers')

    def test_api_does_not_log_token_in_http_error(self):
        err = urllib.error.HTTPError('https://api.nitrado.net/any', 403, 'Forbidden', {}, None)
        with patch.object(self.client,'_open',side_effect=err):
            with self.assertRaises(NitradoError) as caught:
                self.client._json('/services/1/gameservers')
        self.assertNotIn('offline-fixture',str(caught.exception))
        self.assertIn('403',str(caught.exception))

    def test_redirects_disabled_for_bearer_and_download_token(self):
        self.assertIsNone(self.client._opener.handlers[0].redirect_request(
            None,None,302,'Found',{},'https://evil.com/steal') if hasattr(self.client._opener.handlers[0], 'redirect_request') else None)
        self.assertTrue(any(type(h).__name__ == '_RejectRedirects' for h in self.client._opener.handlers))

    def test_download_validates_host(self):
        bad = ('https://evil.com/file', 'https://nitrado.net.evil.com/file',
               'http://nitrado.net/file', 'https://admin:pw@nitrado.net/file',
               'https://nitrado.net:8443/file', 'https://nitrado.net/file#fragment')
        with patch.object(self.client,'_json') as metadata, patch.object(self.client,'_open') as opened:
            for url in bad:
                with self.subTest(url=url), self.assertRaises(NitradoError):
                    metadata.return_value = {'data':{'token':{'url':url,'token':'secret'}}}
                    self.client.download_log(123,FILE,self.dest,ROOT)
            opened.assert_not_called()

    def test_download_rejects_double_token(self):
        with patch.object(self.client,'_json',return_value={'data':{'token':{'url':'https://files.nitrado.net/data?token=old','token':'secret'}}}):
            with self.assertRaises(NitradoError):
                self.client.download_log(123,FILE,self.dest,ROOT)

    def test_download_atomic_and_account_token_is_not_forwarded(self):
        with patch.object(self.client,'_json',return_value=self.token_response), \
             patch.object(self.client,'_open',return_value=FakeResponse(b'example\n')) as opened:
            self.assertEqual(self.client.download_log(123,FILE,self.dest,ROOT),self.dest)
        self.assertEqual(self.dest.read_bytes(),b'example\n')
        self.assertEqual(list(self.dest.parent.glob('*.part')),[])
        request = opened.call_args.args[0]
        self.assertNotIn('offline-fixture',str(request.full_url))
        self.assertNotIn('Authorization',request.headers)
        self.assertIn('one-use',request.full_url)

    def test_oversized_download_keeps_previous_file(self):
        self.dest.write_bytes(b'original')
        with patch.object(self.client,'_json',return_value=self.token_response), \
             patch.object(self.client,'_open',return_value=FakeResponse(b'x'*(MAX_LOG_BYTES+1))):
            with self.assertRaisesRegex(NitradoError, '50 MiB'):
                self.client.download_log(123,FILE,self.dest,ROOT)
        self.assertEqual(self.dest.read_bytes(),b'original')
        self.assertEqual(list(self.dest.parent.glob('*.part')),[])


if __name__=='__main__':
    unittest.main()
