import json,subprocess
from pathlib import Path
from datetime import datetime,timezone
root=Path.cwd();rows=[]
for name,cmd,cwd in [('build',['npm.cmd','run','build'],root/'gesture-arena'),('vitest',['npm.cmd','test'],root/'gesture-arena'),('browser',['npm.cmd','run','test:e2e'],root/'gesture-arena')]:
 p=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300)
 (root/'evidence'/f'art-{name}-v6.log').write_text(p.stdout+'\nSTDERR:\n'+p.stderr,encoding='utf-8')
 rows.append({'name':name,'date':datetime.now(timezone.utc).isoformat(),'exitCode':p.returncode,'log':f'evidence/art-{name}-v6.log'})
 print(name,'exit',p.returncode,flush=True)
 (root/'evidence/art-checks-v6.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
 if p.returncode:break
raise SystemExit(0 if len(rows)==3 and all(r['exitCode']==0 for r in rows) else 1)
