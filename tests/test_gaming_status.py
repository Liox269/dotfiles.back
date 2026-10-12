import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / 'extras/gaming-center/status.py'
spec = importlib.util.spec_from_file_location('gaming_status', PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class TestGames(unittest.TestCase):
    def test_detects_steam_and_gamescope(self):
        sample = [{'class':'steam_app_1245620','title':'Elden Ring','pid':23, 'workspace':{'name':'2'}},
                  {'class':'firefox','title':'Browser'}, {'class':'gamescope','title':'Wrapper'},
                  {'class':'com.example.foo','tags':['game'],'title':'Tagged'}]
        self.assertEqual(len(module.clients_to_games(sample)), 3)
        self.assertEqual(module.clients_to_games(sample)[0]['title'], 'Elden Ring')
    def test_invalid_values(self):
        self.assertEqual(module.clients_to_games(None), [])
        self.assertEqual(module.clients_to_games([{}, 'wrong', {'class':'steam'}]), [])
        self.assertIsNone(module.safe_json('not json'))

if __name__ == '__main__':
    unittest.main()
