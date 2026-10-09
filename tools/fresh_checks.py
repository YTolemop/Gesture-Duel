"""Verify the independent bundles in a Unicode/spaced path, retaining local dependencies."""
import json, os, subprocess, zipfile, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'evidence/全新安裝 空白路徑'
BASE.mkdir(parents=True,exist_ok=True)
for name in ['gesture-arena','gesture-player']:
    with zipfile.ZipFile(ROOT/'delivery'/f'{name}-1.0.0.zip') as archive:
        assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in archive.namelist())
        archive.extractall(BASE)
arena=BASE/'gesture-arena';player=BASE/'gesture-player';py=player/'.venv/Scripts/python.exe'
steps=[
 ('fresh-npm-ci',arena,['npm.cmd','ci','--offline']),
 ('fresh-build',arena,['npm.cmd','run','build']),
 ('fresh-vitest',arena,['npm.cmd','test']),
 ('fresh-pip-install',player,[str(py),'-m','pip','install','-r','requirements-lock.txt']),
 ('fresh-pip-check',player,[str(py),'-m','pip','check']),
 ('fresh-pytest',player,[str(py),'-m','pytest','-ra']),
 ('fresh-player-check',player,[str(py),'main.py','check']),
 ('fresh-gui',player,[str(py),'-c',"from ui.app import App; from main import config; a=App(config()); a.root.withdraw(); a.root.update(); a.close(); print('Fresh Unicode path GUI PASS')"]),
]
env={**os.environ,'PYTHONUTF8':'1','PYTHONIOENCODING':'utf-8'};results=[]
if '--reuse' in sys.argv: steps=steps[1:3]
for name,cwd,command in steps:
    p=subprocess.run(command,cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300)
    path=ROOT/'evidence'/f'{name}.log';path.write_text(p.stdout+'\nSTDERR:\n'+p.stderr,encoding='utf-8')
    results.append({'name':name,'cwd':str(cwd),'command':command,'exitCode':p.returncode,'log':str(path.relative_to(ROOT))})
    print(f'{name}: exit {p.returncode}',flush=True)
(ROOT/'evidence'/('fresh-final-commands.json' if '--reuse' in sys.argv else 'fresh-commands.json')).write_text(json.dumps(results,indent=2),encoding='utf-8')
raise SystemExit(0 if all(r['exitCode']==0 for r in results) else 1)
