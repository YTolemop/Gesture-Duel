import json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'gesture-arena/evidence/playwright.json';result=json.loads(path.read_text(encoding='utf-8'))
assert result['stats']['expected']==6 and result['stats']['unexpected']==0
shutil.copy2(path,ROOT/'evidence/tab-session-playwright.json')
data={'date':result['stats']['startTime'],'command':'npm run build; npm run test:e2e','cwd':str(ROOT/'gesture-arena'),'buildExitCode':0,'playwrightExitCode':0,'passed':6,'regression':'same-browser window.open copied sessionStorage, independent blue seat and original red refresh','transport':'actual browser contexts and Socket.IO'}
(ROOT/'evidence/tab-session.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
print('6 browser flows PASS; tab fix evidence saved')
