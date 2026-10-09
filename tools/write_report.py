"""Write acceptance evidence from completed runs, never from expected results."""
import json,re
from pathlib import Path
from datetime import datetime, timezone, timedelta
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))
commands=read('evidence/commands.json');fresh=read('evidence/fresh-commands.json');fresh_final=read('evidence/fresh-final-commands.json')
network=read('gesture-arena/evidence/network-soak-30min.json')
assert network['pass'] and network['durationSeconds']>=1800
assert all(c['exitCode']==0 for c in commands+fresh+fresh_final)
assert '95 passed' in (ROOT/'evidence/vitest.log').read_text(encoding='utf-8')
assert '9 passed' in (ROOT/'evidence/playwright.log').read_text(encoding='utf-8')
recovery=read('gesture-arena/evidence/network-soak-6min.json')
assert recovery['pass'] and recovery['intentionalReconnects']>=1
audit=read('evidence/numeric_audit.json');assert audit['allPass']
m=network['metrics'];p95=max([v['p95StepMs'] for v in m]+[network['final']['p95StepMs']])
rss=[v['rss']/1024**2 for v in m]+[network['final']['rss']/1024**2]
first,last=m[0],m[-1]
cpu=lambda v:sum(v['cpuMicros'].values())
cpu_percent=(cpu(last)-cpu(first))/((last['seconds']-first['seconds'])*1e6)*100
today=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
report=f'''# 手勢工作坊交付與驗收報告

日期：{today}（Asia/Taipei）。規則 numeric-v2-2026-10-08；協定1；AI ai-v1。

**程式已交付，自動化驗證通過。實機驗證及活動就緒為 NOT_RUN。** 必要學員正規化、KNN依規格保留TODO；濾波選做、預設未啟用。沒有用MediaPipe Gesture Recognizer、內建分類器或隱藏答案替代學員算法。固定／模擬輸出只能證明安全路由與傳輸。

使用者當次要求製作與驗證，是本次開發授權；規格內「本次只修改文件、未授權製作」為歷史修訂說明。本次依完整產品要求實作，沒有沿用文件中的歷史計算結果當作測試證據。

## 交付物與啟動

- gesture-arena：獨立React／TypeScript／Vite／Phaser網站、Node Socket.IO權威伺服器、純GameCore、SQLite及主機維護CLI。
- gesture-player：獨立Python／OpenCV／MediaPipe Hand Landmarker／NumPy／Tkinter／Socket.IO工具，含錄製、資料／模型、安全輸出與學員任務。
- 兩個zip排除node_modules、.venv、個人資料、個人模型、token與.env；含鎖檔、啟動腳本、協定schema／fixtures／manifest、操作文件及本報告證據副本。公開Hand Landmarker模型已綁定本機並驗SHA-256。
- 主機：解壓後setup_windows.bat → start_windows.bat → localhost:3000。學員：setup_windows.bat → run_windows.bat。安裝需外網；活动執行資源本機供應。未交付離線npm／wheel安裝包。
- 跨機、防火牆、鏡頭、HDMI與離線驗收依各repo docs/hosting_local.md、docs/onsite_acceptance.md執行。

## 實際環境

| 項目 | 本次實際值 |
|---|---|
| OS | Windows10 x64，10.0.19045；不是Windows11 |
| CPU／RAM | {network['hardware']['cpu']['model'].strip()}／{network['hardware']['memory']/1024**3:.0f} GiB |
| Node／npm | 22.19.0 x64／10.9.3 |
| Python | 3.13.2 x64，MSC1942 |
| 玩家主要依賴 | MediaPipe0.10.32、NumPy2.2.6、opencv-contrib-python5.0.0.93、python-socketio5.14.1；完整35個固定版本見requirements-lock.txt |
| 網站依賴 | React19.1.1、Phaser3.90.0、Vite6.3.6、TS5.9.2、Socket.IO4.8.1；完整版本見package-lock.json |
| 獨立路徑 | evidence/全新安裝 空白路徑/gesture-arena與gesture-player；各自安裝依賴並執行 |

Node內建SQLite的experimental警告、MediaPipe模型feedback tensor提示有保留於log，沒有將警告隱藏或假稱完全沒有診斷訊息。固定版本實際載入與測試通過；升級依賴需重验。

## 驗收項目

PASS指所列測試證據通過，不能推論所有環境／所有對戰排列都已實測。

| 項目 | 狀態 | 證據／邊界 |
|---|---|---|
| 兩個獨立交付包與中文／空白路徑 | PASS | 獨立npm ci、build、95項測試；另一個venv依鎖檔安裝、pip check、11通過3跳過、模型與GUI安全啟動 |
| 建置與型別檢查 | PASS | tsc --noEmit及Vite production build，退出0 |
| 25招註冊表及接受／耗氣／冷卻／準備tick | PASS | 每招參數化核心測試；獨立數值腳本{audit['count']}項全過 |
| 解析跳躍、蹲躲、圓角掃掠及早接觸 | PASS | 固定tick、解析窗口核對、相對運動／邊界／反射回程測試；單步角色弧線以端點線段近似，見core.md |
| 傷害、多段、格擋／不屈／護盾、零氣、控制、反射及領域 | PASS | 16種傷害施法的獨立期望總量、432組簡化傷害oracle枚舉及其他交互測試；不宣稱窮舉所有連招 |
| 地面穿越限制、空中限制、打斷、加賽／同死 | PASS | 固定tick核心測試 |
| PVP ABBAABBA、互斥普通招、大招私密投影 | PASS | 核心／伺服器測試與獨立紅藍觀戰browser contexts；首次接受大招揭露 |
| 權限、來源generation、舊session／match／seq、一次配對、滿席 | PASS | 伺服器權限測試；真正Python傳輸及正式模式模擬配對拒絕 |
| 明確退出／席位撤銷、空單人房30秒／結果10分鐘回收 | PASS | 伺服器fake clock生命周期測試；不自動轉移房主 |
| Python到Node全部11標籤 | PASS | PRACTICE／PVE各11，context、旧match拒絕、NONE安全逾時及斷線重連新session；loopback實際Socket.IO，不是跨筆電 |
| 推論停滯但心跳持續、安全解除／不補送攻擊 | PASS | OutputRouter freshness與真正網路安全逾時、context清除測試 |
| 必要算法缺漏及選做濾波安全提示 | PASS | TODO明確NotImplementedError；無手／無效維度／finite／過期／未完成濾波輸出NONE，共用工具測試 |
| Hand Landmarker本機模型載入、中文路徑 | PASS | SHA驗證與實際模型black-image無手處理；buffer載入修正原生中文路徑問題。不是鏡頭追蹤驗收 |
| Tkinter安全啟動與原始資料保存 | PASS | GUI建立／退出、原始npz roundtrip、無pickle、train/test用途、NONE僅test；真人錄製與完整GUI人工操作NOT_RUN |
| PVE一命、最後tick、同死、回復上限與獎勵冪等 | PASS | GameCore與RoomManager測試；死亡不回血救活，quit未完成 |
| 真正Python PVE跨關 | PASS | 隔離server-owned HP／位置fixture；真正普攻擊敗，400→650血、1.5→4.5氣，新matchId同runId、失衡清除、舊match拒絕。fixture不證明真人算法或自然AI對局難度 |
| PVE冷卻／局時凍結、來源切換保留資源、配置鎖定 | PASS | 伺服器及瀏覽器pause／source／PVE配置流程 |
| AI難度參數、同seed重現、未揭露資料隔離 | PASS | 所有難度界線測試，同seed核心快照重現；強制未揭露配置時兩種玩家大招得到相同AI決策。所有AI動作仍經InputRouter；真人難度平衡NOT_RUN |
| SQLite版本榜、排序、唯一runId及拒絕客戶端寫分 | PASS | Repository測試、HTTP POST404且榜不變；quit／鍵盤／內測不入正式榜 |
| 重啟保存、備份恢復、清榜權限、匯入衝突回滾 | PASS | 真正SQLite＋maintenance CLI六組檢查，隔離資料庫 |
| 惡意暱稱純文字顯示 | PASS | Playwright榜單渲染fixture顯示字串而不產生img；API寫分另有真實測試 |
| 資料容量告警 | PASS | /health低門檻隔離測試及主機console告警；DATA_WARNING_MB預設512、最低1MiB，保留所有分數不自動刪除 |
| 圖鑑25條目、搜尋、試用、練習輔助與失焦 | PASS | 9個Playwright測試，真實穿雲槍240傷害、canvas、獨立紅藍觀戰context、失焦NONE；四姿態與輔助使用同核心，真鏡頭試用NOT_RUN |
| 初版30分鐘混合網路負載（歷史） | PASS | 正式模式、4房9客戶端、loopback WebSocket；詳見下節 |
| 定時斷線恢復長測分支 | PASS | 另跑6分鐘、实际恢復{recovery['intentionalReconnects']}次；不是8小時通過 |
| 正規化／KNN算法、63／128维golden與真人準確率 | NOT_RUN | 指定學員TODO；pytest對應2項SKIP，须完成接口及個人train/test資料再測 |
| 選做濾波品質 | NOT_RUN | 預設未啟用；第3個SKIP，未選用不阻擋必要流程 |
| Windows11、兩款真攝影機、另一台筆電區網、HDMI | NOT_RUN | 本環境只有一台Windows10主機，缺指定設備；依onsite_acceptance.md實測 |
| 拔外網保留區網的離線活動 | NOT_RUN | 本機資源與準備機制完成，不把程式檢查當拔線實測 |
| 8小時完整soak／超过4房活動量 | NOT_RUN | 已提供480分鐘含恢复脚本；沒有跑滿，不宣稱32房可穩定活動 |

最終自動化沒有未解決FAIL。測試期間修正過原生模型中文路徑、瀏覽器鍵盤焦點、同步投影接收與測試driver選技競態；之後以最終程式重新驗證。未完成硬體或學員算法是上述NOT_RUN，不能稱活動已就緒。

## 初版完整30分鐘網路長測（歷史證據）

命令：`npx tsx tests/network-soak.ts http://127.0.0.1:3105 30`。正式模式 ENABLE_INTERNAL_TEST_MODE=false。1PVP＋2PRACTICE＋1PVE，各一觀眾，總9個真實Node Socket.IO WebSocket客戶端。每0.1秒輸入與心跳、循環結算再開局；使用正式核心與同來源鍵盤流程。

- 實際{network['durationSeconds']:.3f}秒；errors={len(network['errors'])}；程式退出0。
- 每分鐘p95樣本與結尾p95的最大值 **{p95:.3f}ms**，小於16.67ms；結尾{network['final']['p95StepMs']:.3f}ms。p95是伺服器最近10000步窗口，不是聲稱整段所有步的全量p95。
- 累計落後步數 **{network['final']['behindSteps']}**；固定60Hz保留補步時間，沒有降低頻率。伺服器已完成{network['final']['totalSteps']}步（包括負載啟動前的短暫空跑）。
- 每分鐘及結尾RSS樣本範圍 **{min(rss):.1f}–{max(rss):.1f}MiB**，結尾{network['final']['rss']/1024**2:.1f}MiB；不是瞬間峰值探針。
- 首尾分鐘樣本推算CPU平均約 **{cpu_percent:.2f}%單核心**；raw process.cpuUsage user／system保留。系統總CPU百分比與GPU未測。
- 客戶端累計RoomState／snapshot內容 **{network['receivedSnapshotBytes']/1024**2:.1f}MiB**，全9端平均{network['receivedSnapshotBytes']/network['durationSeconds']/1024:.1f}KiB/s。/health的歷史欄位snapshotBytes為Socket.IO所有outgoing packet內容計數，包含狀態與ACK，非純snapshot專項或網卡線路bytes。
- 4房是本次實測穩定基準。MAX_ROOMS=32只是可配置拒絕門檻；沒有做32房效能保證，也沒有跨筆電網卡延遲／封包丟失測試。
- 長測使用合法32容量設定。最後新增的非法MAX_ROOMS啟動拒絕僅在建構時檢查，未改戰鬥迴圈；NaN／Infinity／0／負數／小數及2房拒絕第3房由單元測試另驗，沒有把這個啟動分支當作30分鐘負載證據。

此次雙人介面與連線修正後另跑6分鐘混合網路及恢復驗證，見文末；以下30分鐘數據來自初版，不能視為本次版本重新跑滿30分鐘。另存首輪30分鐘網路baseline及較早30分鐘in-process核心長測；它們明确標記傳輸方式，不取代本次最終網路結果。最終長測期間另有隔離的建置／驗收及6分鐘恢復測試，不是專用空閒硬體基準。6分鐘恢復測試累計落後步數為{recovery['final']['behindSteps']}，之後保留時間補步、沒有降低60Hz；該短測的PASS僅表示恢復成功、無連線錯誤且p95達標，不表示任何時候均零延遲。

## 命令、退出碼與原始證據

- [完整命令、日期、cwd與退出碼](evidence/commands.json)：{len(commands)}組全部退出0。build、vitest、pytest、player-check、pip-check、numeric、GUI、Python傳輸、PVE跨關、維護CLI及Playwright。
- [獨立安裝命令](evidence/fresh-commands.json)：{len(fresh)}組全0；[最終新增測試同步](evidence/fresh-final-commands.json)：{len(fresh_final)}組全0。
- [Windows安裝腳本](evidence/batch-commands.json)：兩個setup_windows.bat實際退出0；主機start_windows.bat真正啟動，/health與首頁200。玩家run_windows.bat互動視窗及鏡頭人工操作尚未實測，安全GUI建構／退出另有自動測試。
- [95項Vitest](evidence/vitest.log)、[Python11通過3跳過](evidence/pytest.log)、[9項Playwright](evidence/playwright.log)、[模型／環境](evidence/player-check.log)。
- [獨立數值重算](evidence/numeric_audit.json)、[Python真正連線](evidence/cross-language.log)、[PVE跨關](evidence/pve-round-transport.log)、[SQLite維護](evidence/maintenance.log)、[容量告警](evidence/storage-warning.json)。
- [初版30分鐘網路結果](gesture-arena/evidence/network-soak-30min.json)、[第一輪網路baseline](gesture-arena/evidence/network-baseline-30min.json)、[較早in-process30分鐘](gesture-arena/evidence/soak-30min.json)、[6分鐘恢復](gesture-arena/evidence/network-soak-6min.json)。
- [30分鐘原始log](gesture-arena/evidence/network-final.log)、[實際退出碼](gesture-arena/evidence/network-final-exit.json)、[恢復原始log](gesture-arena/evidence/network-recovery.log)。
- [PVP畫面](gesture-arena/evidence/pvp.png)、[練習畫面](gesture-arena/evidence/practice.png)。原始log保留warning；沒有把SKIP算通過。

## 重現及後續

各repo README有安装及操作步骤。網站：`npm ci`、`npm run build`、`npm test`、`npm run test:e2e`（首次`npx playwright install chromium`）。玩家：自建venv、依requirements-lock.txt安裝、`main.py check`、`python -m pytest -ra`。聯合測試需要先啟動隔離內測主機；integration_socketio.py預設3102，PVE fixture自己啟動3104。不要在活動主機開內測flag。

獨立數值重算：主機repo執行`npx tsx tests/export-registry.ts`再`python docs/validation/tools/numeric_audit.py evidence/registry.json`。省略registry參數會核對隨驗收包保存的註冊表副本；要驗修改後產品請先匯出實際表，不能只比對舊副本。

8小時：正式主機啟動後執行`npx tsx tests/network-soak.ts http://localhost:3000 480 --recovery`，完整跑滿且errors為空、p95達標才記PASS。定時恢復分支已短測，不等於480分鐘驗證。

必要學員算法完成後重跑tests/test_student_contracts.py，建立獨立train/test原始批次並查看11類混淆矩陣、各類recall與unknown比例；不得拿訓練資料當準確率。兩款攝影機、Windows11、多筆電區網、HDMI及拔外網各填現場表。這些NOT_RUN項目會影響活動可用性，須在宣布活動就緒前完成。
'''
if (ROOT/'evidence/tab-session.json').exists():
    patch=read('evidence/tab-session.json')
    report += f"\n## 多分頁修正補充驗收\n\n日期：{patch['date']}。原始交付後修正sessionStorage被複製時玩家憑證共用的問題；新分頁獨立身分、原頁重新整理保留席位。同一瀏覽器window.open建立第二頁、加入藍方及原紅方刷新均通過；全部6個Playwright流程通過，網站重新建置退出0。戰鬥核心、伺服器及數值未修改，本次未重跑30分鐘長測。\n\n[分頁驗收及退出碼](evidence/tab-session.json)、[完整瀏覽器結果](evidence/tab-session-playwright.json)。更新後請關閉旧分頁再重新開啟網站。\n"
v2=read('gesture-arena/evidence/network-v2-6min.json')
assert v2['pass'] and v2['durationSeconds']>=360 and v2['intentionalReconnects']>=1
assert read('gesture-arena/evidence/network-v2-exit.json')['exitCode']==0
report += f"""
## 雙人流程與全畫面修正驗收

日期：{today}。單一加入房間按鈕，最多三人；等待室紅／藍／觀戰原子互換，受影響玩家取消準備。紅藍各一人且準備後自動5秒進選技，觀戰可空缺。紅方固定先選，每手30秒、逾時自選合法技能；已選欄位及普通重複技能禁點，左右列出已選技能，大招公開仍保密，分類與滑鼠說明可用。8手完成自動5秒開戰。兩方介面相同，1920×1080全場景及背景。

92項Vitest、7個完整瀏覽器流程、Python11通過3跳過及跨語言傳輸全部通過。瀏覽器驗證三人成員換位後身分同步、準備重設、觀戰離開後兩人仍可開局、第四人拒絕、完整8手選技及角色移動。停止藍方網站100／500ms計時器後等待6.5秒，實際Socket.IO連線保持PLAYING，證明不再因網站心跳被降速而誤判；真正斷線及辨識器心跳逾時仍安全暫停。1920×1080瀏覽器實測canvas邊界為1920×1080；其他比例保留場景比例。

本次正式設定實際WebSocket混合負載：4房9客戶端、{v2['durationSeconds']:.3f}秒、有意斷線恢復{v2['intentionalReconnects']}次、errors為空；最後p95 {v2['final']['p95StepMs']:.4f}ms、累計落後步數{v2['final']['behindSteps']}。本次未重新跑滿30分鐘，前文數據明列歷史；沒有把舊長測當成本次版本結果。

長測啟動後另補上等待室成員離開的即時狀態廣播；此補丁已經92項單元測試與完整7項瀏覽器回歸驗證，六分鐘負載未涵蓋該離開通知分支。

[本次6分鐘結果](gesture-arena/evidence/network-v2-6min.json)、[原始log](gesture-arena/evidence/network-v2.log)、[退出碼](gesture-arena/evidence/network-v2-exit.json)、[等待室](gesture-arena/evidence/lobby-v2.png)、[選技畫面](gesture-arena/evidence/draft-v2.png)、[對戰畫面](gesture-arena/evidence/pvp-v2.png)。
"""
assert read('evidence/ui-final.json')['exitCode']==0
report += f"""
## GESTURE ARENA 介面精簡與單人選技修正

日期：{today}。網站品牌與頁面標題統一GESTURE ARENA；移除頁尾、右上名稱徽章、首頁標語，改為簡潔模式入口。等待室第一行置中「紅方先選」、主標「準備對戰」、第三行置中，房間標記改「房號：」。圖鑑分類改「全部」。排行榜保留前兩排標題，移除說明／切換鈕，欄位改「擊殺／遊戲時間／操作模式」，操作模式顯示手勢辨識／鍵盤／模擬輸入，不混入終止原因。

假人練習／一命連戰：外面只顯示來源、準備及相關全局設定；確認準備保存設定後進伺服器SOLO_DRAFT。分類選大招／攻擊／防禦／控制各一招，每手30秒、自動選合法技能，四招選完自動3秒進遊戲。已選欄位锁定，hover顯示技能說明。練習輔助保留，一命連戰建立新runId並鎖定配置。刷新可接續選技；短暫斷線留5秒恢復窗口，必要控制器不可用回準備。觀戰只能看選技，不能代選，也不顯示尚未揭露的大招。

94項Vitest、完整8個瀏覽器流程、Python11通過3跳過、跨語言與既有維護驗證全部通過。最後補上選技觀戰唯讀及大招保密後，再執行94項測試與1個完整聚焦瀏覽器流程，驗證品牌、文字、來源與輔助準備、四類選技、刷新、觀戰、開局。未為本次改動重跑混合長測；前文6／30分鐘均為之前修正的歷史結果。

[完整回歸命令](evidence/commands.json)、[最後聚焦驗收](evidence/ui-final.json)、[原始log](evidence/ui-final.log)、[首頁](gesture-arena/evidence/home-v3.png)、[排行榜](gesture-arena/evidence/board-v3.png)、[單人選技](gesture-arena/evidence/solo-draft-v3.png)。
"""
if (ROOT/'evidence/hud-v4.json').exists():
    hud=read('evidence/hud-v4.json'); assert hud['exitCode']==0
    report += f"\n## 對戰 HUD 精簡與鏡像排列\n\n日期：{hud['date']}。倒計時以1920×1080畫面的中心960為基準；開場／恢復倒數提示置於畫面中心。兩側血條各800px、外側留64px，中央留192px；六格氣與血條等寬，填充方向左右鏡像。移除血條下玩家／HP／護盾及技能／冷卻文字、底部場次統計文字與背景月亮，保留場地與角色狀態反饋。共用Arena繪圖適用PVP、PVE與練習，未修改伺服器、戰鬥規則或協定。\n\n建置／型別檢查退出0；完整PVP選技、倒數、1920×1080canvas、角色移動及背景連線健康流程通過，並檢視開場與戰鬥截圖確認排版。此次只對繪圖與相關流程做驗證，未重跑混合長測。[驗證紀錄](evidence/hud-v4.json)、[原始log](evidence/hud-v4.log)、[開場倒數](gesture-arena/evidence/hud-countdown-v4.png)、[戰鬥HUD](gesture-arena/evidence/hud-v4.png)。\n"
report += f"""
## 單人房號隱藏與獨立配對

日期：{today}。假人練習、一命連戰所有一般畫面不顯示房號；每次建立獨立內部roomId／roomCode，生成時檢查碼碰撞，不會覆蓋其他房間。設定、核心、runId及控制器各自隔離。PVP房號照常顯示。「套用配置」改「套用練習設定」，僅練習提供，戰鬥中不可按；套用假人姿態、位置與全局輔助，重建場景並重設戰鬥狀態。確認準備也會自動套用，無需多按一次。

控制器可省略房號，以全主機唯一的有效六位一次性配對碼定位玩家；提供房碼時仍限制該房。無匹配、歧義或使用過的配對碼拒絕。Python從ACK取得內部房碼，保存供後续自動重連，GUI標示房碼為選填。95項單元測試、9個瀏覽器流程與Python11通過3跳過、實際跨語言全部通過。新增測試驗證不同單人roomId／roomCode、兩名控制器無房號配對正確定位、一次性碼不得重用、修改／啟動練習不改變另一個PVE，以及準備、選技、遊戲時房碼均不出现在畫面。真實Python以空房碼配對PRACTICE／PVE，全部標籤及斷線重連通過。

本次未重跑混合長測；前文長測為歷史證據。[完整驗證命令](evidence/commands.json)、[95項測試](evidence/vitest.log)、[9個瀏覽器流程](evidence/playwright.log)、[Python真實配對與重連](evidence/cross-language.log)。
"""
if (ROOT/'evidence/art-checks-v6.json').exists():
    art=read('evidence/art-checks-v6.json');assert len(art)==3 and all(x['exitCode']==0 for x in art)
    browser=read('gesture-arena/evidence/art-browser-v6.json');assert browser['errors']==[] and browser['phase']=='PLAYING'
    assert '10 passed' in (ROOT/'evidence/art-browser-v6.log').read_text(encoding='utf-8')
    report += f"""
## 競技場美術升級 v6

日期：{browser['date']}。新增本機 AI 生成的山間石造演武場與 RGBA 法師圖集。雙方都是兜帽長袍法師，以紅藍染色區分；待機、兩步走動、蹲下、施法與格擋六姿態依實際伺服器狀態切換，每姿態對齊腳底。1920×1080 場景使用靜態背景紋理，中央留空、兩側少量暖光，沒有月亮與環境粒子。血氣條保留中央鏡像排列與六格氣，新增低調金屬框線；倒數置中，不增加技能及數值字幕。

技能效果使用低透明填色、命中外緣、內圈／符紋及火球／冰晶／星形／光束細節；裝飾位於既有判定形狀內。受傷短暫角色亮色反饋，不使用全場閃光或鏡頭震動。核心數值、人物坐標／碰撞框、技能時間、傷害與伺服器協定未改動。角色服裝和手臂可超出碰撞框，練習的碰撞框顯示仍可用。素材、生成提示詞與整合說明收錄於主機 repo apps/web/src/assets/README.md；素材透過 Vite 本機打包，無執行期圖片服務依賴。

本次最終建置及95項Vitest通過，10個完整瀏覽器流程通過。新增美術流程用正式設定的真實練習伺服器，驗證兩個素材HTTP200、1920×1080全螢幕、待機／蹲下／格擋、火球、護盾、大招預警与有效光束；大招有效窗口僅0.2秒，透過真正暫停按鈕固定有效畫面並驗證恢復成功，避免截圖時序漏拍。瀏覽器pageerror為空，最終PLAYING。另有完整双人8手選技、開場倒數、移動、背景連線與单人隔離回歸。headless渲染取樣記於JSON，僅為診斷，不宣稱現場硬體的FPS保證。此次沒有重跑混合長測；前文的長測數據屬歷史。

[本次命令與退出碼](evidence/art-checks-v6.json)、[建置](evidence/art-build-v6.log)、[單元測試](evidence/art-vitest-v6.log)、[完整瀏覽器流程](evidence/art-browser-v6.log)、[素材與渲染取樣](gesture-arena/evidence/art-browser-v6.json)、[完整場景](gesture-arena/evidence/art-idle-v6.png)、[蹲下](gesture-arena/evidence/art-crouch-v6.png)、[格擋](gesture-arena/evidence/art-guard-v6.png)、[有效大招](gesture-arena/evidence/art-beam-v6.png)。
"""
(ROOT/'acceptance_report.md').write_text(report,encoding='utf-8')
print('Acceptance report generated from completed evidence')

