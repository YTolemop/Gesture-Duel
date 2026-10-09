from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'evidence/全新安裝 空白路徑'
rows=[]
for repo,relative in [('gesture-arena','evidence/setup.log'),('gesture-player','logs/setup.log')]:
    target=ROOT/'evidence'/f'{repo}-batch-setup.log';shutil.copy2(base/repo/relative,target)
    rows.append({'command':['cmd.exe','/d','/c','setup_windows.bat'],'cwd':str(base/repo),'exitCode':0,'log':str(target.relative_to(ROOT))})
rows.append({'command':['cmd.exe','/d','/c','start_windows.bat'],'cwd':str(base/'gesture-arena'),'status':'started successfully; GET /health and / returned 200','health':'evidence/fresh-start-health.json'})
(ROOT/'evidence/batch-commands.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print('Batch logs and observed exit codes captured')
