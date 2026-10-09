"""Single protocol source generator; emits self-contained copies and identical fixtures."""
from pathlib import Path
import json
import hashlib

ROOT=Path(__file__).resolve().parents[1]
LABELS=['MOVE_LEFT','MOVE_RIGHT','JUMP','CROUCH','BLOCK','NORMAL_ATTACK','ATTACK_SKILL','DEFENSE_SKILL','CONTROL_SKILL','ULTIMATE','NONE']
EVENTS={
 'room:create':{'nickname':'string'},'room:join':{'roomCode':'string'},'room:resume':{'roomCode':'string','playerToken':'string'},'room:leave':{},'room:seat':{'seat':'string'},'player:pause':{},'player:next':{},
 'room:assign':{'hostToken':'string','seat':'string','action':'string'},
 'solo:create':{'nickname':'string','mode':'string'},'solo:configure':{'loadout':'object'},'solo:select':{},'solo:pick':{'skillId':'string'},'player:source':{'source':'string'},'player:ready':{'ready':'boolean'},
 'controller:code':{},'controller:pair':{'protocolVersion':'integer','pairCode':'string','source':'string'},'controller:resume':{'roomCode':'string','controllerToken':'string'},'controller:unbind':{},'controller:availability':{'normalization':'boolean','knn':'boolean'},
 'draft:start':{'hostToken':'string'},'draft:pick':{'skillId':'string'},'match:start':{'hostToken':'string'},'match:pause':{'hostToken':'string'},'match:resume':{'hostToken':'string'},'match:rematch':{'hostToken':'string'},'match:next':{'hostToken':'string'},'match:forfeit':{'hostToken':'string','player':'integer','reason':'string'},
 'practice:start':{},'practice:reset':{},'practice:pause':{'hostToken':'string'},'practice:resume':{'hostToken':'string'},'practice:stats-reset':{},'pve:start':{},'pve:quit':{},'leaderboard:list':{}
}
def write(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

def main():
 files={'gesture_labels.json':{'protocolVersion':1,'labels':LABELS,'classIds':{str(i):v for i,v in enumerate(LABELS[:10])}}}
 inp={'$schema':'https://json-schema.org/draft/2020-12/schema','title':'InputState','type':'object','additionalProperties':False,'required':['protocolVersion','sessionId','matchId','seq','gesture','generation'],'properties':{'protocolVersion':{'const':1},'sessionId':{'type':'string','minLength':1},'matchId':{'type':['string','null']},'seq':{'type':'integer','minimum':0},'generation':{'type':'integer','minimum':1},'gesture':{'enum':LABELS},'diagnostics':{'type':'object'}}}
 files['schemas/input-state.schema.json']=inp
 files['schemas/requests.schema.json']={event:{'type':'object','required':['requestId',*fields],'properties':{'requestId':{'type':'string','minLength':1},**{k:{'type':v} for k,v in fields.items()}}} for event,fields in EVENTS.items()}
 files['schemas/ack.schema.json']={'type':'object','required':['requestId','ok'],'properties':{'requestId':{'type':'string'},'ok':{'type':'boolean'},'errorCode':{'type':'string'}}}
 files['schemas/context.schema.json']={'type':'object','required':['protocolVersion','roomId','roomCode','matchId','phase','mode','generation','source','sessionId','rulesVersion','aiVersion'],'properties':{'protocolVersion':{'const':1},'roomId':{'type':'string'},'roomCode':{'type':'string'},'matchId':{'type':['string','null']},'phase':{'enum':['LOBBY','DRAFT','READY','CONFIG','COUNTDOWN','PLAYING','OVERTIME','PAUSED','RESUME_COUNTDOWN','INTERMISSION','RESULT']},'mode':{'enum':['PVP','PRACTICE','PVE']},'generation':{'type':'integer','minimum':1},'source':{'enum':['recognizer','keyboard']},'sessionId':{'type':'string'},'runId':{'type':['string','null']},'roundIndex':{'type':['integer','null']},'rulesVersion':{'type':'string'},'aiVersion':{'type':'string'}}}
 actor={'type':'object','required':['x','y','hp','qi','ground','loadout','cooldowns'],'properties':{'hp':{'type':'number','minimum':0,'maximum':1000},'qi':{'type':'number','minimum':0,'maximum':6},'loadout':{'type':'object','properties':{'ultimate':{'type':['string','null']}}}}}
 core={'type':['object','null'],'required':['tick','actors','objects','elapsed','remaining','result'],'properties':{'tick':{'type':'integer','minimum':0},'actors':{'type':'array','minItems':2,'maxItems':2,'items':actor},'objects':{'type':'array'}}}
 files['schemas/snapshot.schema.json']={'type':'object','required':['protocolVersion','roomId','roomCode','mode','phase','matchId','rulesVersion','aiVersion','snapshotSeq','players'],'properties':{'protocolVersion':{'const':1},'snapshotSeq':{'type':'integer'},'matchId':{'type':['string','null']},'core':core}}
 files['schemas/result.schema.json']={'type':'object','additionalProperties':False,'required':['runId','playerId','nickname','defeated','reason','ticks','hp','rulesVersion','aiVersion','sourceHistory','eligible','internal','completedAt','seed'],'properties':{**{k:{'type':'string'} for k in ['runId','playerId','nickname','reason','rulesVersion','aiVersion','completedAt']},'defeated':{'type':'integer','minimum':0},'ticks':{'type':'integer','minimum':0},'hp':{'type':'number','minimum':0,'maximum':1000},'seed':{'type':'integer'},'eligible':{'type':'boolean'},'internal':{'type':'boolean'},'sourceHistory':{'type':'array','items':{'enum':['recognizer','keyboard','simulated']}}}}
 files['fixtures/inputs.json']={'valid':[{'protocolVersion':1,'sessionId':'fixture','matchId':None,'seq':i,'gesture':v,'generation':1} for i,v in enumerate(LABELS)],'invalid':[{'protocolVersion':2,'sessionId':'fixture','matchId':None,'seq':0,'gesture':'NONE','generation':1},{'protocolVersion':1,'sessionId':'fixture','matchId':None,'seq':-1,'gesture':'NONE','generation':1}]}
 files['fixtures/ack.json']={'ok':True,'requestId':'fixture','protocolVersion':1,'roomCode':'ABC123','seat':'red','sessionId':'fixture','generation':1,'matchId':None}
 digest=hashlib.sha256(json.dumps(files,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
 files['manifest.json']={'protocolVersion':1,'sha256':digest,'files':list(files),'fileHashes':{p:hashlib.sha256((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()).hexdigest() for p,v in files.items()}}
 for folder in [ROOT/'protocol',ROOT/'gesture-arena/protocol',ROOT/'gesture-player/protocol']:
  for path,value in files.items():write(folder/path,value)
 python="from typing import TypedDict, Optional\n\nclass InputState(TypedDict):\n    protocolVersion: int\n    sessionId: str\n    matchId: Optional[str]\n    seq: int\n    gesture: str\n    generation: int\n"
 (ROOT/'gesture-player/network/protocol.py').write_text(python,encoding='utf-8')
 print(digest)

if __name__=='__main__':main()
