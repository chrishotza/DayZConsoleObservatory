import os
import unittest
from unittest.mock import patch,MagicMock
from dayz_observatory.nitrado import NitradoClient,NitradoError

class NitradoTests(unittest.TestCase):
    def test_no_token(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(NitradoError):NitradoClient()
    def test_wrong_game_rejected(self):
        c=NitradoClient('fake')
        with patch.object(c,'gameserver',return_value={'game':'dayz','username':'foo'}):
            with self.assertRaises(NitradoError): c.discover_log_directory(123)
    def test_xbox_directory(self):
        c=NitradoClient('fake')
        with patch.object(c,'gameserver',return_value={'game':'dayzxb','username':'server123'}):
            directory,_=c.discover_log_directory(123)
        self.assertEqual(directory,'/games/server123/noftp/dayzxb/config')
    def test_reject_traversal_username(self):
        c=NitradoClient('fake')
        with patch.object(c,'gameserver',return_value={'game':'dayzxb','username':'../../other'}):
            with self.assertRaises(NitradoError):c.discover_log_directory(123)
    def test_download_rejects_untrusted_path(self):
        c=NitradoClient('fake')
        with self.assertRaises(NitradoError):c.download_log(123,'/secret/OTHER.ADM','out.ADM','/games/name/noftp/dayzxb/config')
    def test_list_excludes_unsafe_entries(self):
        c=NitradoClient('fake')
        data={'data':{'entries':[{'name':'one.ADM','type':'file'}, {'name':'notes.txt','type':'file'}, {'name':'dir.ADM','type':'directory'}]}}
        with patch.object(c,'_json',return_value=data):
            self.assertEqual(len(c.list_logs(123,'/logs')),1)

if __name__=='__main__':unittest.main()
