import json,subprocess
from pathlib import Path
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1]
p=subprocess.run(['npx.cmd','playwright','test','-g','minimal copy','--reporter=list'],cwd=root/'gesture-arena',capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
(root/'evidence/ui-final.log').write_text(p.stdout+'\nSTDERR:\n'+p.stderr,encoding='utf-8')
(root/'evidence/ui-final.json').write_text(json.dumps({'date':datetime.now(timezone.utc).isoformat(),'exitCode':p.returncode,'scope':'English branding, minimal copy, solo preparation/selection, refresh persistence, read-only observer with hidden ultimate, aids retained, battle countdown'},indent=2),encoding='utf-8')
print('Focused browser check exit',p.returncode)
raise SystemExit(p.returncode)
