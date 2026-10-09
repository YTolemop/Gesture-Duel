"""Real Python-to-Node PVE round fixture, server-owned positions/hp only.
No client-reported damage/score and no fixture API in production."""
import sys,time,uuid,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import socketio
from core.features import OutputRouter
from core.types import Prediction
from network.arena_client import ArenaClient
URL='http://127.0.0.1:3104';browser=socketio.Client();states=[]
browser.on('room:state',lambda s:states.append(s),namespace='/arena');browser.on('match:snapshot',lambda s:states.append(s),namespace='/arena');browser.connect(URL,namespaces=['/arena'])
stop=threading.Event()
def heartbeat():
    while not stop.wait(.5):
        if browser.connected:browser.emit('client:heartbeat',{},namespace='/arena')
threading.Thread(target=heartbeat,daemon=True).start()
def call(event,**v):
    result=browser.call(event,{**v,'requestId':str(uuid.uuid4())},namespace='/arena',timeout=5);assert result['ok'],result;return result
def wait(predicate,timeout=12):
    begin=time.monotonic()
    while time.monotonic()-begin<timeout:
        if predicate():return
        time.sleep(.02)
    raise AssertionError('PVE round fixture timeout')
router=OutputRouter();client=ArenaClient(router)
try:
    auth=call('solo:create',mode='PVE',nickname='PVE跨關fixture');pair=call('controller:code');client.connect(URL,auth['roomCode'],pair['pairCode'],'simulated');call('player:ready',ready=True);call('pve:start')
    wait(lambda:states and states[-1]['phase']=='PLAYING' and states[-1]['core']['tick']>6)
    old=states[-1]['matchId'];run_id=states[-1]['run']['runId']
    for _ in range(5):router.update(Prediction('NONE',True,0,1),True);time.sleep(.1)
    begin=time.monotonic()
    while time.monotonic()-begin<5 and (not states or states[-1]['run']['round']==1):
        router.update(Prediction('NORMAL_ATTACK',True,0,1),True);time.sleep(.05)
    wait(lambda:states[-1]['run']['round']==2)
    s=states[-1];assert s['run']['runId']==run_id and s['matchId']!=old
    assert s['core']['actors'][0]['hp']==650
    assert s['core']['actors'][0]['qi']==4.5
    assert s['core']['actors'][0]['imbalance']==0
    wait(lambda:client.context.get('matchId')==s['matchId'])
    ack=client.sio.call('input:state',{'protocolVersion':1,'sessionId':client.context['sessionId'],'generation':client.context['generation'],'matchId':old,'seq':99999,'gesture':'ULTIMATE'},namespace='/controller')
    assert ack['errorCode']=='STALE_MATCH'
    print(json.dumps({'pass':True,'crossRoundContext':True,'sameRunId':True,'newMatchId':True,'rewardHp':650,'rewardQi':4.5,'clearedImbalance':True,'oldMatchRejected':True,'fixture':'server-owned deterministic hp/position; actual normal attack and Socket.IO'},ensure_ascii=False))
finally:
    client.close();stop.set();browser.disconnect()
