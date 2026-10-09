"""Create independent source bundles, never include dependencies, data or tokens."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile
ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'.venv','node_modules','dist','.pytest_cache','__pycache__','test-results','playwright-report','data','models','logs','evidence','.git'}
def main():
    output=ROOT/'delivery';output.mkdir(exist_ok=True)
    manifest=[]
    for name in ['gesture-arena','gesture-player']:
        source=ROOT/name
        (source/'docs').mkdir(exist_ok=True)
        for doc in ['protocol.md','core.md','hosting_local.md','onsite_acceptance.md']:
            shutil.copy2(ROOT/'docs'/doc,source/'docs'/doc)
        report=ROOT/'acceptance_report.md'
        if report.exists():
            validation=source/'docs/validation';validation.mkdir(exist_ok=True)
            (validation/'tools').mkdir(exist_ok=True)
            shutil.copy2(ROOT/'tools/numeric_audit.py',validation/'tools/numeric_audit.py')
            (validation/'acceptance_report.md').write_text(report.read_text(encoding='utf-8').replace('gesture-arena/evidence/','evidence/arena/'),encoding='utf-8')
            evidence=validation/'evidence';evidence.mkdir(exist_ok=True)
            for path in (ROOT/'evidence').iterdir():
                if path.is_file() and path.suffix in ['.json','.log']:shutil.copy2(path,evidence/path.name)
            arenaEvidence=evidence/'arena';arenaEvidence.mkdir(exist_ok=True)
            for filename in ['network-soak-30min.json','network-final.log','network-final-exit.json','network-baseline-30min.json','network-soak-6min.json','network-recovery.log','network-v2-6min.json','network-v2.log','network-v2-exit.json','soak-30min.json','maintenance.json','registry.json','pvp.png','practice.png','lobby-v2.png','draft-v2.png','pvp-v2.png','home-v3.png','board-v3.png','solo-draft-v3.png','hud-v4.png','hud-countdown-v4.png','art-idle-v6.png','art-crouch-v6.png','art-guard-v6.png','art-beam-v6.png','art-browser-v6.json']:
                path=ROOT/'gesture-arena/evidence'/filename
                if path.exists():shutil.copy2(path,arenaEvidence/filename)
        archive=output/f'{name}-1.0.0.zip'
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for path in sorted(source.rglob('*')):
                rel=path.relative_to(source)
                # Keep assets/models: this is the public landmark asset, not student models.
                parts=set(rel.parts)
                if 'assets' in rel.parts:parts.discard('models')
                if 'validation' in rel.parts:parts.discard('evidence')
                if parts.intersection(EXCLUDED) or not path.is_file() or path.name in ['.env','config.json'] or (path.suffix in ['.log','.db','.sqlite','.pyc'] and 'validation' not in rel.parts):continue
                z.write(path,f'{name}/{rel.as_posix()}')
        manifest.append({'file':archive.name,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size})
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest))
if __name__=='__main__':main()
