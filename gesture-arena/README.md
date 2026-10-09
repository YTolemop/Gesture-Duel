# GESTURE ARENA

React＋TypeScript＋Vite／Phaser 網站、Socket.IO Node權威伺服器及獨立 GameCore。包含25招、PVP、技能圖鑑、練習、PVE及本機SQLite榜。

驗證環境：Node.js **22.19.0 x64**、npm **10.9.3**。依賴版本固定於package-lock.json。Windows腳本以自身資料夾啟動，支援空白／中文路徑。

雙擊setup_windows.bat安裝並建置，再start_windows.bat。或PowerShell：

```powershell
npm ci
npm run build
npm start
```

可複製.env.example為.env；HOST=0.0.0.0、PORT=3000，MAX_ROOMS=32可調。主機使用 http://localhost:3000；其他筆電填主機區網IP，例如 http://192.168.1.100:3000 。0.0.0.0不是玩家網址。啟動會列網卡候選，需要自行確認實體網卡。Windows防火牆只放行所選TCP埠的私人網路入站，勿關閉整個防火牆。`GET /health`看版本與容量，不代表已配對。連接埠占用、建置缺失會顯示錯誤。

首頁建立PVP，其他人輸入房號按「加入房間」，自動安排空玩家席或觀戰席；最多三人。房內可換紅／藍／觀戰，已有人時互換，換位取消準備且需重新配對辨識器。紅藍各一人且都準備後，自動5秒倒數進選技；觀戰可空缺。紅方固定先選，ABBAABBA先隱藏大招，再三類普通技能，每手30秒逾時自選。左右顯示已選技能，中間分類、說明及鎖定狀態。選完自動5秒開戰；双方介面相同。戰鬥畫面以1920×1080場景全視窗顯示，觀眾可全螢幕移至HDMI。

同一瀏覽器可開多個分頁，分別建立房間或加入紅／藍／觀戰席位。複製分頁及window.open會複製sessionStorage；網站以BroadcastChannel檢查活躍分頁，複製的新頁自動清除所複製的玩家憑證，原頁重新整理則保留席位。同一玩家憑證仍只容許一條有效連線。鍵盤只接收目前有焦點的視窗，切換分頁會解除按鍵。

正式預設手勢，選鍵盤無需Python與內測。A/D/W/S/Space/J/K/L/U/I；最後按下有效鍵優先，放開回前鍵，失焦解除。紅鍵盤／藍手勢可獨立使用。手勢：Python工具填主機網址、房碼、自己的配對碼；必要正規化與KNN接口可用才可準備，濾波未啟用不擋。鏡頭故障先暫停，在網站改鍵盤、確認準備；PVP雙方準備後5秒恢復，單人3秒，保留生命與冷卻。

技能圖鑑有25招，搜尋／分類及真實練習試用。練習與一命連戰先在準備區設定來源與全局選項，確認準備後進分類選技，四類各一招、每手30秒，逾時自選；選完自動3秒開局。重新整理可接續短暫斷線前的選技。練習四姿態、位置及四輔助只能在配置／暫停調整；套用會重建練習。正式PVE不接受輔助；整次配置鎖定、一命90秒每關，存活過關+250血/+3氣且封頂，5秒間歇再3秒倒數，保留冷卻與累計解鎖時間。

單人模式房號不顯示；每個玩家或獨立分頁建立自己的內部房間，伺服器防止房碼碰撞，配置／核心／runId／來源互不共用。手勢配對可不填房碼，六位一次性配對碼在有效期內全主機唯一；Python取得實際房碼後保存供重連。「套用練習設定」只在練習顯示，修改假人及輔助後會重建場景並重設戰鬥狀態；確認準備也會自動套用。進行中需先暫停再套用，一命連戰不提供這個重設設定按鈕。

榜按規則／AI版本分組，正式榜只收全程辨識器死亡／超時結果；鍵盤／混合／內測／退出另存。沒有防作弊認證。資料預設使用者主目錄 `.gesture-arena/leaderboard.sqlite`，可設ARENA_DATA_DIR到私有資料夾；不在repo，不保存影像或token。主機崩潰不恢复正在打的局。房主權限不自動轉移。

維護只在主機CLI：

```powershell
npx tsx apps/server/maintenance.ts backup "D:\備份\排行榜.json"
npx tsx apps/server/maintenance.ts export "D:\備份\排行榜.csv"
npx tsx apps/server/maintenance.ts import "D:\備份\排行榜.json"
npx tsx apps/server/maintenance.ts clear numeric-v2-2026-10-08 ai-v1 --confirm
```

重複runId須內容一致；不同內容拒絕，匯入交易回滾。清榜只指定版本；一般玩家及房主沒有伺服器清榜API。DATA_WARNING_MB預設512；資料庫加WAL達門檻時，/health的storage.warning為true，主機每分鐘顯示容量告警，沒有自動刪分。

```powershell
npm test
npm run test:e2e
npm run soak -- 30
npm run soak -- 480
npx tsx tests/network-soak.ts http://localhost:3000 30
npx tsx tests/network-soak.ts http://localhost:3000 480 --recovery
```

soak為混合房核心／完整序列化效能測試，報告明列是否網路傳輸；8小時必須實際跑滿才算通過。首次Playwright需要 `npx playwright install chromium`；測試前保持3000埠空閒，测试會啟動自己的正式模式伺服器，資料隔離於evidence/e2e-data。開發網站 `npm run dev`，伺服器仍需先build/start，Vite proxy同origin。

離線執行：先完成npm ci/build，網站資源全部本機供應，無CDN。拔外網保留區網的實機驗收另見交付報告，不等於安裝可離線。沒有代為公開部署、購買網域或修改場地網路。

檔案索引：apps/web為網站與繪圖；apps/server/index啟動／健康／固定步，rooms為席位／配對／選技／模式與投影，leaderboard為SQLite，maintenance為私有CLI。packages/game-core中skills為唯一數值表，core為戰鬥，input為重武裝，geometry為碰撞，ai為延遲觀察及可重現AI。packages/protocol及protocol為協定。tests/core/server為規則／權限測試，tests/e2e為多context網站，tests/soak為長測。所有第一方程式由教學維護者維護；學員不在此repo填算法。

協定、核心、區網部署與現場表：docs/。验收與原始證據：docs/validation/acceptance_report.md。本機SQLite API在此Node版本有experimental警告；已以固定版本測試，升級Node需重驗。
