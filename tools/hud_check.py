import json, subprocess
from pathlib import Path
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1]
result=subprocess.run(['npx.cmd','playwright','test','-g','self-service PVP','--reporter=list'],cwd=root/'gesture-arena',capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
(root/'evidence/hud-v4.log').write_text(result.stdout+'\nSTDERR:\n'+result.stderr,encoding='utf-8')
(root/'evidence/hud-v4.json').write_text(json.dumps({'date':datetime.now(timezone.utc).isoformat(),'exitCode':result.returncode,'scope':'full PVP draft, centered countdown, mirrored health/qi HUD, no moon or HUD captions, 1920x1080 canvas, actual movement, background transport health','screenshots':['gesture-arena/evidence/hud-countdown-v4.png','gesture-arena/evidence/hud-v4.png']},indent=2),encoding='utf-8')
print('HUD browser check exit',result.returncode)
raise SystemExit(result.returncode)
