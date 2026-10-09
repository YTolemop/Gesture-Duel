"""Capture commands, exit codes and raw logs for the acceptance report."""
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];EVIDENCE=ROOT/'evidence';EVIDENCE.mkdir(exist_ok=True)
PYTHON=ROOT/'gesture-player/.venv/Scripts/python.exe'
commands=[
 ('build',ROOT/'gesture-arena',['npm.cmd','run','build']),
 ('vitest',ROOT/'gesture-arena',['npm.cmd','test']),
 ('pytest',ROOT/'gesture-player',[str(PYTHON),'-m','pytest','-ra']),
 ('player-check',ROOT/'gesture-player',[str(PYTHON),'main.py','check']),
 ('pip-check',ROOT/'gesture-player',[str(PYTHON),'-m','pip','check']),
 ('numeric',ROOT,[sys.executable,'tools/numeric_audit.py']),
 ('gui-smoke',ROOT/'gesture-player',[str(PYTHON),'-c',"from ui.app import App; from main import config; a=App(config()); a.root.withdraw(); a.root.update(); a.close(); print('Tkinter safe startup PASS')"]),
 ('cross-language',ROOT/'gesture-player',[str(PYTHON),'tests/integration_socketio.py']),
 ('pve-round-transport',ROOT/'gesture-arena',['npx.cmd','tsx','tests/cross-language-fixture.ts']),
 ('maintenance',ROOT/'gesture-arena',['npx.cmd','tsx','tests/maintenance-fixture.ts']),
 ('playwright',ROOT/'gesture-arena',['npm.cmd','run','test:e2e'])]
def main():
    results=[];env={**os.environ,'PYTHONUTF8':'1','PYTHONIOENCODING':'utf-8'}
    for name,cwd,command in commands:
        start=datetime.now(timezone.utc).isoformat();p=subprocess.run(command,cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240)
        path=EVIDENCE/f'{name}.log';path.write_text(p.stdout+'\nSTDERR:\n'+p.stderr,encoding='utf-8')
        results.append({'name':name,'startedAt':start,'cwd':str(cwd),'command':command,'exitCode':p.returncode,'log':str(path.relative_to(ROOT))})
        print(f'{name}: exit {p.returncode}',flush=True)
    (EVIDENCE/'commands.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    return 0 if all(r['exitCode']==0 for r in results) else 1
if __name__=='__main__':sys.exit(main())
