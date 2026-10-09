import json,subprocess
from pathlib import Path
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1]; started=datetime.now(timezone.utc).isoformat()
result=subprocess.run(['npm.cmd','run','test:e2e'],cwd=root/'gesture-arena',capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240)
(root/'evidence/playwright.log').write_text(result.stdout+'\nSTDERR:\n'+result.stderr,encoding='utf-8')
p=root/'evidence/commands.json';rows=json.loads(p.read_text(encoding='utf-8'))
for row in rows:
    if row['name']=='playwright':row.update(startedAt=started,exitCode=result.returncode)
p.write_text(json.dumps(rows,indent=2),encoding='utf-8')
print('Browser regression exit',result.returncode)
raise SystemExit(result.returncode)
