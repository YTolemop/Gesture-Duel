# 手勢玩家工具

**正規化與KNN必做，濾波選做**。只修改以下三個算法檔，完整步驟見 [學員任務](docs/student_tasks.md)：

- `student/normalization.py`：StudentNormalizer.transform。
- `student/knn.py`：StudentKNN.fit / predict。
- `student/filtering.py`：StudentFilter.update / reset（不啟用不必完成）。

未填算法仍可啟動介面、預覽及採集原始關鍵點。正式分類輸出維持NONE並禁止準備；模擬只供主機內測。TODO未完成不是安裝失敗，接口可用也不代表真人準確率通過。MediaPipe預訓練模型只擷取手部21點，學員KNN模型是自己的特徵與分類資料，兩者不同。

環境指定 **Python 3.13.2 x64**。VS Code是編輯器，Microsoft Python擴充套件是編輯／除錯整合，仍要另裝本機Python。第一版Windows桌面工具，CLI在其他OS尚未實機驗證。

自動安裝：先安裝指定Python（勾選PATH），雙擊setup_windows.bat，建立repo內.venv、安裝requirements-lock、驗證模型及自檢；log在logs/setup.log。再run_windows.bat。

手動PowerShell，先用VS Code開啟整個資料夾，終端切到repo：

```powershell
python --version
python -m venv .venv
& '.\.venv\Scripts\python.exe' -m pip install -r requirements-lock.txt
& '.\.venv\Scripts\python.exe' main.py prepare
& '.\.venv\Scripts\python.exe' main.py check
& '.\.venv\Scripts\python.exe' main.py gui
& '.\.venv\Scripts\python.exe' -m pytest
```

.venv隔離專案套件，減少與其他專案衝突，可重建，但不免除Python／套件安裝；版本由Python指定、lock與腳本共同固定。它不包含student/data/models，不加入Git、不跨電腦複製。不需先Activate環境，直接呼叫.venv的Python。自己加套件可用 `& '.\.venv\Scripts\python.exe' -m pip install 套件名稱`；正式課程勿任意升級，恢復依賴可重新pip install -r requirements-lock。若要重建，只處理.venv，保留student、data、models及config.json。

VS Code安裝Microsoft Python擴充套件，Ctrl+Shift+P→Python: Select Interpreter→選repo的.venv\Scripts\python.exe；開main.py執行／除錯，傳gui參數。測試窗啟用pytest；工作區設定已相對化，沒有開發者絕對路徑。

使用：開鏡頭（索引0–3可選），讀回640×480/30fps實際值，等比例顯示，不強迫鏡頭支援。推論與預覽都先鏡像，左右槽按Hand Landmarker handedness；低可信或左右重复拒絕。採集頁選十類、batch、train/test，倒數3秒開始；最多10筆/秒。採樣、批數、訓練分割由自己決定。預設只保存關鍵點npz／JSON，不保存影片，沒有必須先拍照片的步驟。

算法完成後train（只train批次）、test（只test批次），或GUI按鈕；載入models/knn.npz及JSON後改recognize，即時顯示Prediction與安全label。選濾波才呼叫StudentFilter，出錯NONE且不靜默降級。輸出超過0.5秒沒新結果就NONE，網路每0.1秒傳最新狀態，心跳獨立0.5秒。影像與資料不傳伺服器。

配對：網站建立遊戲、控制來源選手勢、產生一次性配對碼；Python填主機網址（本機 http://localhost:3000，另一筆電 http://主機區網IP:3000）及配對碼。房碼為選填，單人模式留空；伺服器以有效配對碼定位玩家，工具保存回傳的內部房碼供重連。雙人模式也可指定房碼來限定配對房間。健康檢查成功不代表配對，只有回覆同一席位才是已配對。必要接口可用、自己做完全部標籤測試後網站按準備。網站選鍵盤就不需Python；相機故障先暫停、網站改鍵盤再確認準備並恢復。PVE鍵盤／混合結果另保存、不列正式手勢榜。

CLI：

```powershell
& '.\.venv\Scripts\python.exe' main.py record
& '.\.venv\Scripts\python.exe' main.py train
& '.\.venv\Scripts\python.exe' main.py test
& '.\.venv\Scripts\python.exe' main.py simulate --server http://127.0.0.1:3000 --room ABC123 --pair-code 042731 --labels NONE,MOVE_RIGHT,NONE,ATTACK_SKILL --seconds 20
```

simulate必须主機ENABLE_INTERNAL_TEST_MODE=true，結果標內測。不能拿模拟當真人辨識通過。自身分類與正常關閉會安全NONE；重連清session／match與濾波，不補送舊攻擊。認證token只保存在記憶體。

疑難排解：

- 網路／代理／憑證：安裝失敗看setup.log，確認pip可到套件服務及學校代理／信任憑證；不要停用TLS驗證。模型已随repo附且驗SHA-256，缺檔才prepare下載。
- 安裝政策／空間不足：請系統管理員允許Python及使用者可寫資料夾，檢查磁碟剩餘；.venv可重建，不刪算法及資料。
- VS Code找不到套件：确认解释器是repo.venv，不是全域Python；擴充套件不代替Python。
- 鏡頭黑畫面：Windows設定→隱私權與安全性→攝影機→允許桌面應用程式；關閉其他占用程式、換索引，檢查實際fps。
- TODO提示：到訊息指定student檔及函式，按學員任務完成。學員測試SKIP不代表通過；共用工具測試應通過。
- 模型不相容：手模式、鏡像或特徵版本改了就以原始資料重算train，重新load；不使用pickle。
- 區網連不上：另一台筆電不能用localhost，需主機IP，主機仅放行必要TCP埠的私人網路。不要關閉整個防火牆。

課前完成依賴及鏡頭檢查；安装需要外網，活动资源本机，不用CDN或付費API。未提供離線wheel包，.venv不能當離線安裝方案。拔外網保留區網的實機、兩款鏡頭與HDMI驗證狀態見交付報告。

交付驗收與原始證據位於 [docs/validation/acceptance_report.md](docs/validation/acceptance_report.md)；NOT_RUN及TODO不算已通過。

## 檔案功能索引

以下第一方檔由教學維護者維護，除student三檔外學員无需修改；個人設定可按需修改。

| 檔案 | 用途／修改者 |
|---|---|
| main.py | GUI、record、train、test、simulate、prepare、check入口；維護者 |
| student/normalization.py | 正規化必做；學員 |
| student/knn.py | KNN必做；學員 |
| student/filtering.py | 濾波選做；學員 |
| core/types.py | RawHandSample、FeatureResult、Prediction契約；維護者 |
| core/labels.py | 讀取固定協定標籤；維護者 |
| core/features.py | 呼叫學員接口、維度／finite安全检查及新鮮度；維護者 |
| core/camera.py | 背景擷取最新影格、實際規格；維護者 |
| core/landmarks.py | Hand Landmarker單純取21點、固定左右槽；維護者 |
| core/dataset.py | 原始npz／metadata、train/test用途；維護者 |
| core/model_io.py | 重算特徵、train、評估、无pickle模型格式；維護者 |
| core/resources.py | 官方模型來源、SHA-256及prepare；維護者 |
| network/arena_client.py | Socket.IO配對／重連／context／心跳；維護者 |
| network/protocol.py | 協定TypedDict；生成檔，勿手改 |
| ui/app.py | Tkinter主线程、鏡頭工作、採集／訓練／配對頁；維護者 |
| tests/test_tools.py | 共用工具安全／資料／資源測試；維護者 |
| tests/test_student_contracts.py | 學員接口及golden验收，TODO則SKIP；維護者 |
| tests/fixtures/normalization.json | 固定輸入／預期輸出，不提供算法答案；維護者 |
| tests/integration_socketio.py | 真正Python到Node內測；維護者 |
| tests/integration_pve_round.py | 隔離伺服器fixture下的真正跨關連線；維護者 |
| protocol/ | 版本、schema、fixtures及manifest，生成檔 |
| config.example.json／config.json | 手模式、特徵版本、KNN及濾波設定；個人config可改 |
| pyproject.toml／requirements-lock.txt | Python與依賴固定；維護者 |
| setup_windows.bat／run_windows.bat | 自建venv安装與启动；維護者 |
| .vscode/settings.json／extensions.json | 相對解释器、pytest及擴充建議；維護者 |
| .gitignore | 排除資料、模型、環境、log及個人設定；維護者 |
| README.md／docs/student_tasks.md／docs/protocol.md | 使用、學員任務、協定；維護者 |
| NOTICE.md／assets/models/ | 第三方來源授權、Hand Landmarker預訓練模型；維護者 |
| data/ | 你採集的個人關鍵點與metadata，不上傳Git |
| models/ | 你的KNN訓練特徵／設定與評估，不是MediaPipe模型 |
| .venv/／logs/ | 本機依賴與安裝log，生成／個人，不發給其他筆電 |
