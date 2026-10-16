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

    def test_invalid_calendar_day_and_header_clock_are_ignored(self):
        self.assertIsNone(parse_header('AdminLog started on 2026-02-30 at 12:00:00'))
        self.assertIsNone(parse_header('AdminLog started on 2026-10-15 at 25:00:00'))
        self.assertEqual(parse_header('AdminLog started on 2024-02-29 at 23:59:59'),
                         date(2024, 2, 29))

    def test_synthetic_combat_and_building_words_are_whole_tokens(self):
        for fragment, expected in (
            ('Player "SYNTH" (id=SYNTH_1) was killed by unknown', 'death'),
            ('Player "SYNTH" (id=SYNTH_1) hit by object', 'hit'),
            ('Player "SYNTH" (id=SYNTH_1) has dismantled a structure', 'build'),
            ('Player "SYNTH" (id=SYNTH_1) studied the record', 'unknown'),
            ('Player "SYNTH" (id=SYNTH_1) rebuilt the notes', 'unknown'),
            ('Player "SYNTH" (id=SYNTH_1) listed damaged items', 'unknown'),
        ):
            with self.subTest(fragment=fragment):
                event = parse_line('12:01:00 | ' + fragment)
                self.assertEqual(event.kind, expected)
                self.assertEqual(event.player_id, 'SYNTH_1')

    def test_non_finite_synthetic_position_does_not_enter_coordinates(self):
        huge = '9' * 400
        event = parse_line(
            '12:01:00 | Player "SYNTH" (id=SYNTH_1 pos=<' +
            huge + ', 2, 3>)'
        )
        self.assertEqual(event.kind, 'unknown')
        self.assertEqual(event.player_id, 'SYNTH_1')
        self.assertIsNone(event.x)
        self.assertIsNone(event.z)
        self.assertIsNone(event.altitude)
        self.assertIn(huge, event.raw)

    def test_ordinary_synthetic_position_still_parses(self):
        event = parse_line('12:00:01 | Player "SYNTH" (id=SYNTH_1 pos=<-2, 3.5, 4>)')
        self.assertEqual(event.kind, 'position')
        self.assertEqual((event.x, event.z, event.altitude), (-2.0, 3.5, 4.0))

if __name__=='__main__':unittest.main()
