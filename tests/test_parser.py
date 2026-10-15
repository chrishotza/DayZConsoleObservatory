import unittest
from datetime import date
from dayz_observatory.parser import parse_line, parse_header, event_datetime

class ParserTests(unittest.TestCase):
    def test_header(self):
        self.assertEqual(parse_header('AdminLog started on 2026-10-14 at 23:56:00'),date(2026,10,14))
    def test_position_normal(self):
        e=parse_line('12:00:00 | Player "Test" (id=ABC pos=<1200, 3400.5, 19.2>)')
        self.assertEqual((e.kind,e.player_id,e.x,e.z,e.altitude),('position','ABC',1200,3400.5,19.2))
    def test_position_hyphen(self):
        e=parse_line('12:00:00 | Player "Test" (id=ABC - pos=<-1, -2, 0>)')
        self.assertEqual((e.x,e.z,e.altitude),(-1,-2,0))
    def test_connected(self):
        e=parse_line('14:30:04 | Player "T"(id=ABC) is connected')
        self.assertEqual((e.kind,e.player_name,e.player_id),('connected','T','ABC'))
    def test_disconnected(self):
        e=parse_line('14:30:04 | Player "T"(id=ABC) has been disconnected')
        self.assertEqual(e.kind,'disconnected')
    def test_unknown_preserved(self):
        e=parse_line('00:00:05 | undocumented record')
        self.assertEqual(e.kind,'unknown');self.assertIn('undocumented',e.raw)
    def test_no_header(self):
        self.assertIsNone(parse_line('AdminLog started on 2026-10-14 at 23:56:00'))
    def test_invalid_time(self):
        self.assertIsNone(parse_line('25:00:00 | bad'))
    def test_midnight_rollover(self):
        dt,seconds,day=event_datetime('00:02:00',date(2026,10,14),23*3600+59*60,0)
        self.assertEqual((dt,day),('2026-10-15T00:02:00',1))
    def test_unverified_date_not_invented(self):
        dt,_,_=event_datetime('00:02:00',None,None,0)
        self.assertIsNone(dt)

if __name__=='__main__':unittest.main()
