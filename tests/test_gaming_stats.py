import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest

SRC = Path(__file__).resolve().parents[1]/'extras/gaming-center/stats/tracker.py'
spec=importlib.util.spec_from_file_location('tracker',SRC)
tracker=importlib.util.module_from_spec(spec)
spec.loader.exec_module(tracker)

class StatsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.db=tracker.connect(Path(self.temp.name)/'stats.db')
    def tearDown(self):
        self.db.close(); self.temp.cleanup()
    def game(self,name='Super Mario Strikers'):
        return {'title':name,'platform':'Dolphin','pid':100}
    def test_session_and_no_duplicate_windows(self):
        tracker.reconcile(self.db,[self.game(),self.game()],1000,10)
        tracker.reconcile(self.db,[self.game()],1010,10)
        rows=self.db.execute('SELECT seconds FROM sessions').fetchall()
        self.assertEqual(rows,[(10,)])
    def test_stops_when_game_exits(self):
        tracker.reconcile(self.db,[self.game()],1000,10)
        tracker.reconcile(self.db,[self.game()],1010,10)
        tracker.reconcile(self.db,[],1020,10)
        self.assertEqual(self.db.execute('SELECT seconds,ended_at FROM sessions').fetchone(),(10,1010))
    def test_gap_does_not_count_offline_time(self):
        tracker.reconcile(self.db,[self.game()],1000,10)
        tracker.reconcile(self.db,[self.game()],5000,10)
        self.assertEqual(self.db.execute('SELECT COUNT(*),SUM(seconds) FROM sessions').fetchone(),(2,0))
    def test_separates_games(self):
        tracker.reconcile(self.db,[self.game(),self.game('Super Smash Bros. Ultimate')],1000,10)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM sessions').fetchone()[0],2)
    def test_other_platform_no_bad_key(self):
        self.assertEqual(tracker.game_identity({'class':'steam_app_268910','title':'Cuphead'})[2],'Steam')

if __name__=='__main__': unittest.main()
