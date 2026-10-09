import json
import re
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
from core.camera import Camera
from core.landmarks import Landmarks
from core.features import OutputRouter, feature, raw_valid
from core.labels import LABELS
from core.dataset import save_batch
from core.model_io import train, evaluate, load_model
from core.types import Prediction
from network.arena_client import ArenaClient

ROOT=Path(__file__).resolve().parents[1]
CONNECTIONS=[(0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),(5,9),(9,10),(10,11),(11,12),(9,13),(13,14),(14,15),(15,16),(13,17),(0,17),(17,18),(18,19),(19,20)]

class App:
    def __init__(self,config):
        self.config=config;self.root=tk.Tk();self.root.title('手勢競技場 · 玩家工作坊');self.root.geometry('1150x850')
        self.router=OutputRouter();self.camera=None;self.landmarks=None;self.model=None;self.client=None
        self.running=threading.Event();self.image_lock=threading.Lock();self.latest=None;self.notice='開啟鏡頭預覽；正規化與KNN必做，濾波選做。'
        self.algorithm_status={'normalization':False,'knn':False,'filter':False};self.recording=False;self.samples=[];self.labels=[];self.record_start=0;self.last_record=0;self.feature_count=0
        self.filter_enabled=False;self.mode='preview';self.simulated='NONE';self.raw_result=None;self.record_label=0;self.record_batch='batch-01';self.record_purpose='train';self.worker=None
        main=ttk.Frame(self.root,padding=15);main.pack(fill='both',expand=True)
        ttk.Label(main,text='手勢玩家工具',font=('Microsoft JhengHei',22,'bold')).pack(anchor='w')
        ttk.Label(main,text='MediaPipe只取得關鍵點。請完成 student/normalization.py 與 student/knn.py；濾波預設關閉。').pack(anchor='w',pady=7)
        self.tabs=ttk.Notebook(main);self.tabs.pack(fill='both',expand=True)
        preview=ttk.Frame(self.tabs,padding=12);connect=ttk.Frame(self.tabs,padding=12);data=ttk.Frame(self.tabs,padding=12)
        self.tabs.add(preview,text='關鍵點／即時辨識');self.tabs.add(data,text='採集／訓練／評估');self.tabs.add(connect,text='配對／內測模擬')
        bar=ttk.Frame(preview);bar.pack(fill='x');self.camera_index=tk.StringVar(value='0');ttk.Label(bar,text='鏡頭索引').pack(side='left');ttk.Combobox(bar,textvariable=self.camera_index,values=['0','1','2','3'],width=5).pack(side='left',padx=8)
        ttk.Button(bar,text='開啟鏡頭',command=self.start_camera).pack(side='left');ttk.Button(bar,text='停止鏡頭',command=self.stop_camera).pack(side='left',padx=8)
        self.mode_var=tk.StringVar(value='preview');ttk.Combobox(bar,textvariable=self.mode_var,values=['preview','recognize'],state='readonly',width=12).pack(side='left');self.mode_var.trace_add('write',lambda *_:setattr(self,'mode',self.mode_var.get()))
        self.filter_var=tk.BooleanVar(value=False);ttk.Checkbutton(bar,text='使用學員濾波（選做）',variable=self.filter_var,command=self.change_filter).pack(side='left',padx=8)
        self.preview=ttk.Label(preview,text='鏡頭尚未開啟',anchor='center');self.preview.pack(fill='both',expand=True,pady=10)
        self.details=ttk.Label(preview,text='',wraplength=1000);self.details.pack(anchor='w')
        self.class_var=tk.StringVar(value=LABELS[0]);self.batch_var=tk.StringVar(value='batch-01');self.purpose_var=tk.StringVar(value='train')
        for title,var,values in [('錄製類別（NONE只作選擇性未知測試）',self.class_var,LABELS),('用途',self.purpose_var,['train','test'])]:
            ttk.Label(data,text=title).pack(anchor='w');ttk.Combobox(data,textvariable=var,values=values,state='readonly').pack(anchor='w',pady=5)
        ttk.Label(data,text='批次名稱（同一批保持一致；測試資料不加入訓練）').pack(anchor='w');ttk.Entry(data,textvariable=self.batch_var).pack(anchor='w',pady=5)
        ttk.Button(data,text='倒數3秒後錄製（最多10筆／秒）',command=self.begin_record).pack(anchor='w',pady=5)
        ttk.Button(data,text='停止並保存原始關鍵點',command=self.save_record).pack(anchor='w',pady=5)
        self.counts=ttk.Label(data,text='原始有效0筆／可用特徵0筆');self.counts.pack(anchor='w',pady=5)
        ttk.Label(data,text='個人資料批次（不保存影像；刪除不會改動學員程式）').pack(anchor='w',pady=10)
        self.files=tk.Listbox(data,width=80,height=8);self.files.pack(anchor='w');ttk.Button(data,text='重新讀取',command=self.refresh_files).pack(anchor='w');ttk.Button(data,text='刪除所選批次',command=self.delete_batch).pack(anchor='w',pady=5)
        ttk.Button(data,text='訓練（只使用train批次）',command=lambda:self.background(self.train)).pack(anchor='w',pady=5)
        ttk.Button(data,text='獨立評估（只使用test批次）',command=lambda:self.background(self.evaluate)).pack(anchor='w',pady=5)
        ttk.Button(data,text='載入個人KNN模型',command=lambda:self.background(self.load)).pack(anchor='w',pady=5)
        self.server_var=tk.StringVar(value='http://127.0.0.1:3000');self.room_var=tk.StringVar();self.pair_var=tk.StringVar();self.source_var=tk.StringVar(value='recognizer')
        for title,var in [('主機網址（其他筆電使用主機區網IP）',self.server_var),('房間碼（選填，單人留空）',self.room_var),('一次性配對碼',self.pair_var)]:
            ttk.Label(connect,text=title).pack(anchor='w',pady=5);ttk.Entry(connect,textvariable=var,width=60).pack(anchor='w')
        ttk.Combobox(connect,textvariable=self.source_var,values=['recognizer','simulated'],state='readonly').pack(anchor='w',pady=10)
        ttk.Button(connect,text='健康檢查（不代表已配對）',command=self.health).pack(anchor='w',pady=5)
        ttk.Button(connect,text='配對',command=self.connect).pack(anchor='w',pady=5);ttk.Button(connect,text='解除本機連線',command=self.disconnect).pack(anchor='w',pady=5)
        ttk.Label(connect,text='以下按鈕僅供 simulated 來源；主機必須開啟內測，不能進正式榜。').pack(anchor='w',pady=15)
        buttons=ttk.Frame(connect);buttons.pack(anchor='w')
        for i,label in enumerate(LABELS):
            ttk.Button(buttons,text=label,command=lambda l=label:self.simulate(l)).grid(row=i//3,column=i%3,padx=4,pady=4)
        self.status=ttk.Label(main,text=self.notice,wraplength=1080);self.status.pack(anchor='w',pady=10)
        self.root.protocol('WM_DELETE_WINDOW',self.close);self.root.after(50,self.render);self.refresh_files()

    def background(self,fn):
        def run():
            try:fn()
            except Exception as exc:self.notice=f'工具提示：{exc}（算法TODO不等於安裝失敗）'
        threading.Thread(target=run,daemon=True).start()

    def start_camera(self):
        if self.camera:return
        index=int(self.camera_index.get())
        def start():
            try:
                self.camera=Camera(index);self.landmarks=Landmarks();self.running.set();self.worker=threading.Thread(target=self.process,daemon=True);self.worker.start();self.notice=f'鏡頭實際設定：{self.camera.actual}'
            except Exception as exc:
                self.notice=str(exc);self.stop_camera()
        self.background(start)

    def process(self):
        last=0;previous=time.monotonic()
        while self.running.is_set():
            frame,timestamp=self.camera.latest()
            if frame is None or timestamp==last:
                if frame is None:self.router.update(tracked=False)
                time.sleep(.01);continue
            last=timestamp;start=time.monotonic()
            try:
                sample=self.landmarks.detect(frame,timestamp,self.camera.actual);sample.batch=self.record_batch
                tracked,reason=raw_valid(sample,self.config);result=None;pred=None
                try:
                    result=feature(sample,self.config)
                    if result.valid:self.algorithm_status['normalization']=True
                except Exception as exc:
                    self.algorithm_status['normalization']=False;reason=str(exc)
                if self.mode=='recognize' and result and result.valid:
                    if self.model is None:reason='請訓練或載入個人KNN模型'
                    else:
                        pred=self.model.predict(result.features);self.algorithm_status['knn']=True
                self.raw_result=pred
                self.router.update(pred,tracked=tracked and pred is not None,enabled=self.filter_enabled)
                if self.router.error:reason=self.router.error;self.algorithm_status['filter']=False
                elif self.filter_enabled and pred:self.algorithm_status['filter']=True
                now=time.monotonic()
                if self.recording and now>=self.record_start and now-self.last_record>=.1 and tracked:
                    self.samples.append(sample);self.labels.append(self.record_label);self.last_record=now
                    if result and result.valid:self.feature_count+=1
                for hand in (sample.left,sample.right):
                    if hand is None:continue
                    points=[(int(p[0]*sample.width),int(p[1]*sample.height)) for p in hand]
                    for a,b in CONNECTIONS:cv2.line(frame,points[a],points[b],(90,220,160),2)
                    for point in points:cv2.circle(frame,point,4,(100,180,255),-1)
                fps=1/max(1e-6,now-previous);previous=now
                self.notice=f'{reason or "追蹤正常"} · FPS {fps:.1f} · 辨識 {(now-start)*1000:.1f}ms · 安全輸出 {self.router.read()}'
                with self.image_lock:self.latest=frame
            except Exception as exc:
                self.router.update(tracked=False);self.notice=str(exc)
                if self.client:
                    try:self.client.availability(normalization=False,knn=False)
                    except Exception:pass

    def stop_camera(self):
        self.running.clear()
        if self.worker and self.worker is not threading.current_thread():self.worker.join(timeout=2)
        if self.camera:self.camera.close();self.camera=None
        if self.landmarks:self.landmarks.close();self.landmarks=None
        self.router.update(tracked=False)

    def change_filter(self):
        self.filter_enabled=self.filter_var.get();self.config['filter_enabled']=self.filter_enabled
        try:self.router.clear(self.filter_enabled)
        except Exception as exc:self.notice=str(exc)
        if self.client:self.background(lambda:self.client.availability(**self.flags()))

    def flags(self):
        return {**self.algorithm_status,'filterEnabled':self.filter_enabled}

    def begin_record(self):
        if not self.camera:messagebox.showinfo('請開鏡頭','先在關鍵點頁開啟鏡頭。');return
        if not re.fullmatch(r'[\w-]{1,40}',self.batch_var.get()):messagebox.showerror('批次名稱','只接受文字、數字、底線及連字號。');return
        if self.recording:messagebox.showinfo('錄製中','先停止並保存。');return
        self.record_batch=self.batch_var.get();self.record_purpose=self.purpose_var.get();self.record_label=LABELS.index(self.class_var.get());self.samples=[];self.labels=[];self.feature_count=0;self.record_start=time.monotonic()+3;self.last_record=0;self.recording=True
        if self.record_label==10:self.record_purpose='test';self.purpose_var.set('test')

    def save_record(self):
        self.recording=False
        if not self.samples:messagebox.showinfo('沒有有效樣本','無手或倒數期間不會計入。');return
        path=ROOT/'data'/f'{self.record_batch}-{self.record_label}-{time.time_ns()}.npz'
        save_batch(path,list(self.samples),list(self.labels),self.record_purpose,dict(self.config));self.notice=f'已保存 {len(self.samples)} 筆原始關鍵點';self.refresh_files()

    def refresh_files(self):
        self.files.delete(0,'end')
        for p in sorted((ROOT/'data').glob('*.npz')):self.files.insert('end',p.name)

    def delete_batch(self):
        selected=self.files.curselection()
        if selected and messagebox.askyesno('刪除批次','確認刪除所選原始資料及metadata？'):
            p=ROOT/'data'/self.files.get(selected[0]);p.unlink();p.with_suffix('.json').unlink(missing_ok=True);self.refresh_files()

    def train(self):
        self.notice=json.dumps(train(list((ROOT/'data').glob('*.npz')),ROOT/'models/knn.npz',self.config),ensure_ascii=False);self.load()

    def evaluate(self):
        result=evaluate(list((ROOT/'data').glob('*.npz')),ROOT/'models/knn.npz',self.config);(ROOT/'models/evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');self.notice=f'獨立測試報告保存 models/evaluation.json：{result}'

    def load(self):
        self.model=load_model(ROOT/'models/knn.npz',self.config);self.algorithm_status['knn']=True;self.notice='KNN模型已載入；接口可用不代表真人準確率通過'
        if self.client:self.client.availability(**self.flags())

    def connect(self):
        server,room,code,source=self.server_var.get(),self.room_var.get().upper(),self.pair_var.get(),self.source_var.get()
        def run():
            if self.client:self.client.close()
            self.client=ArenaClient(self.router,lambda msg:setattr(self,'notice',msg),lambda:self.router.clear(self.filter_enabled));self.client.connect(server,room,code,source,self.flags())
        self.background(run)

    def disconnect(self):
        if self.client:self.background(self.client.close);self.client=None

    def simulate(self,label):
        if self.source_var.get()!='simulated':messagebox.showinfo('內測限制','先選 simulated 並完成內測配對。');return
        self.simulated=label

    def health(self):
        server=self.server_var.get()
        def run():
            import urllib.request
            with urllib.request.urlopen(server.rstrip('/')+'/health',timeout=5) as response:self.notice=f'健康檢查成功（尚未代表配對）：{response.read().decode()}'
        self.background(run)

    def render(self):
        if self.source_var.get()=='simulated':self.router.update(Prediction(self.simulated,True,0,1),True,False)
        self.status.config(text=self.notice);self.counts.config(text=f'原始有效{len(self.samples)}筆／可用特徵{self.feature_count}筆'+(f' · 倒數{max(0,self.record_start-time.monotonic()):.1f}s' if self.recording else ''))
        self.details.config(text=f'正規化：{"可用" if self.algorithm_status["normalization"] else "未完成／無效"} · KNN：{"可用" if self.algorithm_status["knn"] else "未完成／未載入"} · 濾波：{"啟用" if self.filter_enabled else "未啟用（選做）"} · 原分類 {self.raw_result}')
        with self.image_lock:frame=self.latest
        if frame is not None:
            h,w=frame.shape[:2];scale=min(900/w,460/h);image=Image.fromarray(cv2.cvtColor(cv2.resize(frame,(int(w*scale),int(h*scale))),cv2.COLOR_BGR2RGB));self.photo=ImageTk.PhotoImage(image);self.preview.config(image=self.photo,text='')
        self.root.after(50,self.render)

    def close(self):
        self.stop_camera()
        if self.client:self.client.close()
        self.root.destroy()

    def run(self):self.root.mainloop()
