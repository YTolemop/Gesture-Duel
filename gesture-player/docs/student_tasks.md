# 學員任務：正規化與KNN必做，濾波選做

姿勢必須靜態且彼此明顯不同；十類是動作欄位，不要求比數字、不要求多角度。樣本數、批次及資料分配由你決定。約每類200筆、分批採集與獨立測試是建議，不是硬門檻，也不保證準確率。

1. **預覽關鍵點**。前置：完成安裝、`python main.py check`。開GUI、選鏡頭、開啟鏡頭；畫面連續讀取最新影格，再呼叫 Hand Landmarker，只取得21點及左右手。影像先鏡像，推論與顯示一致。預期看到關鍵點線條、鏡頭讀回設定、無手安全NONE。若無畫面檢查Windows隱私權、占用、索引。算法未填不能稱有分類。
2. **採集原始資料**。前置：鏡頭可用。在採集頁選0–9標籤、批次與train/test；倒數3秒後最多10筆/秒。原始有效及可用特徵分開顯示；TODO未填仍能保存原始資料。停止保存到data的npz+JSON，預設不保存照片影片。明確test不入train。重錄使用新批次，刪除要確認。相鄰影格混用訓練／測試會高估表現。
3. **完成正規化**。修改 `student/normalization.py: StudentNormalizer.transform`。輸入 RawHandSample，左右槽各(21,3)，附width/height、鏡像契約、批次時間；使用image landmarks。單手選config.single_hand；雙手left63+right63+兩旗標。按docstring完成像素尺度、手腕平移、手掌尺度、可選左手x鏡像與展平；不做完整旋轉對齊。掌尺度<10px、無手或非有限拒絕，FeatureResult(valid=False,features=None,reason,featureVersion)。有效向量float32 (63,)或(128,)。命令 `python -m pytest tests/test_student_contracts.py -k normalization`，比對golden原點、尺度不變、左右／缺手；未實作會SKIP，完成標準是fixtures通過且採集／訓練／即時均呼叫同函式。常見錯誤：x/y使用不同單位、用world坐標、依畫面左右排序、錯dtype、版本不符。
4. **建立KNN**。修改 `student/knn.py: fit/predict`。fit finite float32(N,D)與(N,)classId0–9；predict一筆(D,)回Prediction(label固定標籤或NONE,valid,nearest_distance非負或null,vote_ratio0–1)。自行設計距離、k、投票、同票規則及拒絕門檻，不硬把未知姿勢分到十類之一。命令 `python -m pytest tests/test_student_contracts.py -k knn`；再 `python main.py train`。只取train，保存models/knn.npz+JSON，不用pickle。`python main.py test`只取test，產生混淆矩陣、每類召回及拒絕率。GUI也有訓練、獨立評估、載入按鈕。完成標準為接口測試、自己的獨立資料及即時分類均可使用；不設固定準確率參賽門檻。常見錯誤：k>N、批次洩漏、返回數字而非固定label、載入錯手模式。
5. **練習場連線實測**。前置：正規化、KNN及個人模型已可用。網站建練習房、選辨識器、產生配對碼；Python載入模型，模式recognize，填主機區網IP／房號／碼並配對。介面聲明必要接口可用後在網站確認準備；逐一檢查十類及NONE、保持只觸發一次、無手停止、冷卻拒絕不排隊。自己觀察延遲、距離／投票及誤判；不以Python模擬替代真人品質。新局／重連清輸出，先NONE。濾波選擇在Python，控制來源選擇在網站。
6. **選擇濾波**。預設不用，直接輸出有效KNN分類。要用才修改 `student/filtering.py: update/reset`。update接受Prediction及本機monotonic秒，回固定label；reset清歷史。命令 `python -m pytest tests/test_student_contracts.py -k filter`；再GUI啟用，於同一練習場觀察效果。未完成啟用會NONE及明確提示，不靜默退回直接模式。無手／例外／0.5秒過期安全層不可覆蓋。沒有另設濾波測試台或品質分數。

算法相依：正規化→特徵→KNN→可選濾波。改正規化、左右手設定或特徵版本，更新config.feature_version，保留原始資料，再train重算、重建模型；舊模型不相容就拒絕。config變更後重新載入／訓練，重連會清filter。

共同工具測試：`python -m pytest tests/test_tools.py`。學員任務測試：`python -m pytest tests/test_student_contracts.py`，TODO的SKIP不是PASS。真人端到端需你的算法、資料、鏡頭與區網；準確率不能由fixtures或模擬證明。
