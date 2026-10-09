"""Synthetic closed-form fixtures, not a reusable normalization implementation."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]/'gesture-player/tests/fixtures'
root.mkdir(parents=True,exist_ok=True)
right=[[.2+i*.01,.3,0] for i in range(21)]
left=[[.8-i*.01,.3,0] for i in range(21)]
expected=[value for i in range(21) for value in [i/9,0,0]]
base={'hand_mode':'single','single_hand':'right','mirror_left':True,'feature_version':'student-normalization-v1'}
fixtures=[{'name':'single right','left':None,'right':right,'width':640,'height':480,'config':base,'valid':True,'expected':expected},
{'name':'translated and scaled','left':None,'right':[[.1+i*.02,.6,0] for i in range(21)],'width':640,'height':480,'config':base,'valid':True,'expected':expected},
{'name':'mirrored left','left':left,'right':None,'width':640,'height':480,'config':{**base,'single_hand':'left'},'valid':True,'expected':expected},
{'name':'dual both','left':left,'right':right,'width':640,'height':480,'config':{**base,'hand_mode':'dual'},'valid':True,'expected':expected+expected+[1,1]},
{'name':'dual right missing','left':left,'right':None,'width':640,'height':480,'config':{**base,'hand_mode':'dual'},'valid':True,'expected':expected+[0]*63+[1,0]},
{'name':'no hands','left':None,'right':None,'width':640,'height':480,'config':base,'valid':False,'expected':None},
{'name':'palm too small','left':None,'right':[[.1+i*.0001,.3,0] for i in range(21)],'width':640,'height':480,'config':base,'valid':False,'expected':None}]
(root/'normalization.json').write_text(json.dumps(fixtures,indent=2),encoding='utf-8')
