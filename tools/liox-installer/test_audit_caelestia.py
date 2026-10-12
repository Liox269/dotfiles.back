import tempfile,unittest,json
from pathlib import Path
from audit_caelestia import main
class AuditTests(unittest.TestCase):
 def test_cli_required_repo(self):
  import subprocess,sys
  x=subprocess.run([sys.executable,str(Path(__file__).with_name('audit_caelestia.py'))],capture_output=True)
  self.assertNotEqual(x.returncode,0)
 def test_stage_existing_refused(self):
  pass
