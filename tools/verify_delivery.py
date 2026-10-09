"""Check portable archive content, protocol SHA and required teaching TODOs."""
import hashlib,json,zipfile,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];rows=[];protocol_hashes=[]
for item in json.loads((ROOT/'delivery/manifest.json').read_text()):
    path=ROOT/'delivery'/item['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
    repo=item['file'].removesuffix('-1.0.0.zip');prefix=repo+'/'
    with zipfile.ZipFile(path) as z:
        names=z.namelist();assert z.testzip() is None
        assert all(n.startswith(prefix) and '..' not in Path(n).parts for n in names)
        assert not any(set(Path(n).parts)&{'node_modules','.venv','.git','__pycache__','dist'} for n in names)
        assert not any(Path(n).name in ['.env','config.json'] for n in names)
        for required in ['README.md','setup_windows.bat','docs/protocol.md','docs/hosting_local.md','docs/onsite_acceptance.md','docs/validation/acceptance_report.md']:
            assert prefix+required in names,required
        manifest=json.loads(z.read(prefix+'protocol/manifest.json'));protocol_hashes.append(manifest['sha256'])
        for filename,digest in manifest['fileHashes'].items():assert hashlib.sha256(z.read(prefix+'protocol/'+filename)).hexdigest()==digest
        if repo=='gesture-arena':
            for asset in ['terrace-v6.png','mage-sheet-v6.png','README.md']:
                assert prefix+'apps/web/src/assets/'+asset in names
            assert prefix+'apps/web/src/arena.tsx' in names
        if repo=='gesture-player':
            for file in ['normalization','knn','filtering']:assert b'raise NotImplementedError' in z.read(prefix+'student/'+file+'.py')
            assert hashlib.sha256(z.read(prefix+'assets/models/hand_landmarker.task')).hexdigest()=='fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1'
        report=z.read(prefix+'docs/validation/acceptance_report.md').decode('utf-8')
        for link in re.findall(r'\]\(([^)]+)\)',report):
            if link.startswith('evidence/'):assert prefix+'docs/validation/'+link in names,link
        rows.append({**item,'files':len(names),'protocol':protocol_hashes[-1],'pass':True})
assert len(set(protocol_hashes))==1
(ROOT/'delivery/verification.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps(rows))
