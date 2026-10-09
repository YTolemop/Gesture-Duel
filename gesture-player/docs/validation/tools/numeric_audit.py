"""Independent numeric-v2 expectations transcribed from specification.
Does not import GameCore and does not reuse historical audit claims."""
import json
import math
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
registry_path=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'gesture-arena/evidence/registry.json'
if not registry_path.exists():registry_path=ROOT/'evidence/arena/registry.json'
registry=json.loads(registry_path.read_text(encoding='utf-8'))
skills={s['id']:s for s in registry['skills']}
checks=[]
def check(name,actual,expected,tolerance=1e-8):
    ok=abs(actual-expected)<=tolerance if isinstance(expected,(float,int)) else actual==expected
    checks.append({'name':name,'actual':actual,'expected':expected,'pass':ok})
expected={
'normal':(0,.8,.25,.35,70),'fireball':(1,2,.35,.25,100),'spear':(2,4,.6,.25,240),'flame':(2,4,.45,.25,220),'stars':(2,4,.4,.25,100),'bomb':(3,6,.5,.25,360),
'shield':(1,6,.2,.25,0),'mirror':(1,5,.2,.25,0),'wall':(2,7,.25,.25,0),'phase':(2,6,.2,.25,0),'cleanse':(1,6,.15,.25,0),
'ice':(1,4,.35,.25,80),'bind':(2,6,.7,.25,180),'repulse':(1,4,.4,.25,80),'pull':(2,5,.4,.25,190),'slowfield':(1,7,.45,.25,0),
'beam':(6,30,1,.6,600),'meteor':(6,30,1,.4,220),'nova':(6,30,.8,.4,600),'sanctuary':(6,30,.2,.4,0),'silence':(6,30,.2,.4,0),'resolve':(6,30,.2,.4,0),'gravity':(6,30,.9,.4,480),'frost':(6,30,.9,.4,510),'storm':(6,30,.8,.4,540)}
check('rules version',registry['rulesVersion'],'numeric-v2-2026-10-08')
check('25 skills',len(skills),25)
for id,values in expected.items():
    for k,v in zip(['cost','cooldown','prepare','recovery','damage'],values):check(f'{id}.{k}',skills[id][k],v)
for id,v in {'fireball':(800,1120,1.4),'spear':(1200,1200,1),'flame':(640,960,1.5),'stars':(700,560,.8),'ice':(720,1008,1.4),'pull':(520,1040,2)}.items():
    for key,value in zip(['speed','range','life'],v):check(f'{id}.{key}',skills[id][key],value)
    check(f'{id}.distance consistency',skills[id]['speed']*skills[id]['life'],skills[id]['range'])
for id,shape in {'fireball':{'kind':'circle','r':28},'spear':{'kind':'rect','w':100,'h':20},'flame':{'kind':'rect','w':100,'h':72},'stars':{'kind':'circle','r':16},'bomb':{'kind':'circle','r':150},'bind':{'kind':'rect','w':200,'h':100},'wall':{'kind':'rect','w':40,'h':300},'ice':{'kind':'circle','r':20},'pull':{'kind':'circle','r':26},'beam':{'kind':'rect','w':960,'h':120},'meteor':{'kind':'rect','w':360,'h':480},'nova':{'kind':'circle','r':220},'gravity':{'kind':'rect','w':360,'h':100},'frost':{'kind':'rect','w':720,'h':100},'storm':{'kind':'rect','w':600,'h':330},'slowfield':{'kind':'rect','w':320,'h':24}}.items():check(f'{id}.shape',skills[id]['shape'],shape)
for id,key,value in [('shield','shield',120),('shield','duration',2.5),('sanctuary','shield',600),('silence','shield',480),('resolve','duration',6),('cleanse','duration',2),('bind','root',.6),('frost','root',.6),('repulse','push',160),('nova','push',280),('storm','push',320),('pull','pull',200),('ice','slow',.2),('slowfield','slow',.3),('gravity','slow',.4)]:check(f'{id}.{key}',skills[id][key],value)
check('jump apex',900-1120*.4+1400*.4**2,676)
check('flight at0.8',900-1120*.8+1400*.8**2,900)
check('max horizontal jump',320*.8,256)
check('spear crouch gap',820-(784+10),26)
windows={}
for id in ['fireball','spear','flame','ice','pull','beam']:
    s=skills[id];top=s['y']-(s['shape'].get('r') or s['shape']['h']/2)
    safe=[n/60 for n in range(49) if 900-1120*n/60+1400*(n/60)**2<=top]
    windows[id]=[min(safe),max(safe)]
expected_windows={'fireball':(.1,.7),'ice':(5/60,43/60),'pull':(.1,.7),'flame':(5/60,43/60),'spear':(.15,.65),'beam':(11/60,37/60)}
for id,window in expected_windows.items():
    check(id+' safe start',windows[id][0],window[0]);check(id+' safe end',windows[id][1],window[1])
arrivals={}
for id in ['fireball','spear','flame','ice','pull']:
    s=skills[id];half=s['shape'].get('r') or s['shape']['w']/2
    arrivals[id]=s['prepare']+(960-64-32-half)/s['speed']
escapes={id:{str(speed):(width/2+32)/speed for speed in [320,256,224,192]} for id,width in [('bind',200),('meteor',360),('gravity',360)]}
result={'date':'2026-10-09','rulesVersion':registry['rulesVersion'],'source':'new independent script, not historical attachments','checks':checks,'count':len(checks),'passed':sum(c['pass'] for c in checks),'windows':windows,'arrivalSeconds':arrivals,'escapeSeconds':escapes,'allPass':all(c['pass'] for c in checks)}
(ROOT/'evidence/numeric_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'count':result['count'],'passed':result['passed'],'allPass':result['allPass']}))
raise SystemExit(0 if result['allPass'] else 1)
