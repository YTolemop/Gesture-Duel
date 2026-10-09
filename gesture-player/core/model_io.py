from pathlib import Path
import json
import numpy as np
from core.dataset import read_batch
from core.features import feature, validate_prediction
from core.labels import LABELS
from student.knn import StudentKNN

def features_from(paths, config, purpose):
    x, y, rejected = [], [], 0
    for path in paths:
        samples, labels, meta = read_batch(path)
        if meta['purpose'] != purpose:
            continue
        for sample, label in zip(samples, labels):
            result = feature(sample, config)
            if result.valid:
                x.append(result.features); y.append(label)
            else:
                rejected += 1
    if not x:
        raise ValueError(f'沒有可用的 {purpose} 特徵；檢查資料用途及正規化 TODO')
    return np.asarray(x,dtype=np.float32), np.asarray(y,dtype=np.int64), rejected

def save_model(path, x, y, config):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, features=x, labels=y)
    path.with_suffix('.json').write_text(json.dumps({'format':1,'labels':LABELS,'config':{k:v for k,v in config.items() if k!='filter_enabled'}},ensure_ascii=False,indent=2),encoding='utf-8')

def load_model(path, config):
    path=Path(path); meta=json.loads(path.with_suffix('.json').read_text(encoding='utf-8'))
    if meta != {'format':1,'labels':LABELS,'config':{k:v for k,v in config.items() if k!='filter_enabled'}}:
        raise ValueError('模型與特徵／手模式／標籤／設定版本不相容，請重算並訓練')
    with np.load(path, allow_pickle=False) as data:
        x, y = data['features'], data['labels']
    d=128 if config['hand_mode']=='dual' else 63
    if x.ndim!=2 or x.shape[1]!=d or y.shape!=(len(x),) or x.dtype!=np.float32 or not np.isfinite(x).all() or not np.issubdtype(y.dtype,np.integer) or ((y<0)|(y>9)).any():
        raise ValueError('模型資料格式無效')
    model=StudentKNN(); model.fit(x,y,config); return model

def train(paths, path, config):
    x,y,rejected=features_from(paths,config,'train'); model=StudentKNN(); model.fit(x,y,config); save_model(path,x,y,config)
    return {'training_samples':len(y),'normalization_rejected':rejected,'independent_test':False}

def evaluate(paths,path,config):
    model=load_model(path,config);x,y,rejected=features_from(paths,config,'test');matrix=np.zeros((11,11),dtype=int)
    for row,label in zip(x,y):
        pred=model.predict(row); value=validate_prediction(pred); matrix[label,LABELS.index(value) if value!='NONE' else 10]+=1
    recalls=[float(matrix[i,i]/matrix[i].sum()) if matrix[i].sum() else None for i in range(11)]
    return {'independent_test':True,'samples':len(y),'normalization_rejected':rejected,'labels':LABELS,'confusion_matrix':matrix.tolist(),'recall':recalls,'unknown_ratio':float(matrix[:,10].sum()/len(y))}
