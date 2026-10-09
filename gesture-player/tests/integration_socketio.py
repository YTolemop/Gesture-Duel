"""Actual python-socketio to Node test. Requires running internal-mode arena."""
import json
import sys
import time
import uuid
import threading
from pathlib import Path
import socketio
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core.features import OutputRouter
from core.labels import LABELS
from core.types import Prediction
from network.arena_client import ArenaClient

URL='http://127.0.0.1:3102'
browser=socketio.Client();states=[];browser.on('room:state',lambda v:states.append(v),namespace='/arena');browser.on('match:snapshot',lambda v:states.append(v),namespace='/arena')
browser.connect(URL,namespaces=['/arena'])
heartbeat_stop=threading.Event()
def heartbeat():
    while not heartbeat_stop.wait(.5):
        if browser.connected:
            try:browser.emit('client:heartbeat',{},namespace='/arena')
            except Exception:pass
threading.Thread(target=heartbeat,daemon=True).start()
def call(event,**v):
    ack=browser.call(event,{**v,'requestId':str(uuid.uuid4())},namespace='/arena',timeout=5)
    assert ack['ok'],ack
    return ack
def wait(predicate,timeout=8):
    start=time.monotonic()
    while time.monotonic()-start<timeout:
        browser.emit('client:heartbeat',{},namespace='/arena')
        if predicate():return
        time.sleep(.05)
    raise AssertionError('timeout waiting for state')

def exercise(mode):
    auth=call('solo:create',nickname='跨語言測試',mode=mode);pair=call('controller:code')
    router=OutputRouter();client=ArenaClient(router)
    try:
        paired=client.connect(URL,'',pair['pairCode'],'simulated')
        assert client.room==auth['roomCode']
        assert paired['seat']=='red'
        for i,label in enumerate(LABELS):
            payload={'protocolVersion':1,'sessionId':client.context['sessionId'],'matchId':None,'seq':100+i,'gesture':label,'generation':client.context['generation']}
            ack=client.sio.call('input:state',payload,namespace='/controller');assert ack['ok'],(label,ack)
        client.seq=120
        call('player:ready',ready=True)
        if mode=='PRACTICE':
            call('solo:configure',loadout={'attack':'fireball','defense':'shield','control':'ice','ultimate':'beam'},aids={'infiniteQi':True,'noCooldown':True,'unlock':True,'immortal':True},dummy='stand',dummyX=700)
            call('practice:start')
        else:call('pve:start')
        wait(lambda:states and states[-1]['phase']=='PLAYING')
        match=states[-1]['matchId'];assert client.context['matchId']==match
        router.update(Prediction('NONE',True,0,1),True)
        for _ in range(5):router.update(Prediction('NONE',True,0,1),True);time.sleep(.1);browser.emit('client:heartbeat',{},namespace='/arena')
        for _ in range(6):router.update(Prediction('ATTACK_SKILL',True,0,1),True);time.sleep(.1);browser.emit('client:heartbeat',{},namespace='/arena')
        wait(lambda:any(s.get('core') and 'fireball' in s['core']['actors'][0]['cooldowns'] for s in states))
        ack=client.sio.call('input:state',{'protocolVersion':1,'sessionId':client.context['sessionId'],'matchId':'old-match','seq':999,'gesture':'ULTIMATE','generation':client.context['generation']},namespace='/controller');assert ack['errorCode']=='STALE_MATCH'
        # Deliberate recognizer stall but heartbeat alive -> NONE, not old attack.
        wait(lambda:states[-1]['core']['actors'][0]['label']=='NONE')
        old_session=client.context['sessionId']
        client.sio.disconnect()
        client.sio.connect(URL,namespaces=['/controller'])
        wait(lambda:client.context.get('sessionId') not in (None,old_session))
        call('player:ready',ready=True)
        if mode=='PRACTICE':
            call('match:pause',hostToken=auth['hostToken']);call('practice:reset')
            wait(lambda:client.context.get('matchId')!=match)
        else:
            call('pve:quit');wait(lambda:states[-1]['phase']=='RESULT');assert states[-1]['run']['result']['eligible'] is False
        return {'mode':mode,'labels':11,'context':True,'oldMatchRejected':True,'newSession':True,'safeTimeout':True}
    finally:
        client.close();call('room:leave')

try:
    results=[exercise('PRACTICE'),exercise('PVE')]
    print(json.dumps({'pass':True,'results':results},ensure_ascii=False))
finally:
    heartbeat_stop.set();browser.disconnect()
