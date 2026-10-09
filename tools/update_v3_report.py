from pathlib import Path
root=Path(__file__).resolve().parents[1];p=root/'tools/write_report.py';s=p.read_text(encoding='utf-8')
start=s.index("v2=read(")
s=s[:start].replace('92 passed','94 passed').replace('7 passed','8 passed').replace('92項','94項').replace('7個Playwright','8個Playwright').replace('7項Playwright','8項Playwright')+s[start:]
marker="(ROOT/'acceptance_report.md').write_text(report,encoding='utf-8')"
section='''assert read('evidence/ui-final.json')['exitCode']==0
report += f"""
## GESTURE ARENA 介面精簡與單人選技修正

日期：{today}。網站品牌與頁面標題統一GESTURE ARENA；移除頁尾、右上名稱徽章、首頁標語，改為簡潔模式入口。等待室第一行置中「紅方先選」、主標「準備對戰」、第三行置中，房間標記改「房號：」。圖鑑分類改「全部」。排行榜保留前兩排標題，移除說明／切換鈕，欄位改「擊殺／遊戲時間／操作模式」，操作模式顯示手勢辨識／鍵盤／模擬輸入，不混入終止原因。

假人練習／一命連戰：外面只顯示來源、準備及相關全局設定；確認準備保存設定後進伺服器SOLO_DRAFT。分類選大招／攻擊／防禦／控制各一招，每手30秒、自動選合法技能，四招選完自動3秒進遊戲。已選欄位锁定，hover顯示技能說明。練習輔助保留，一命連戰建立新runId並鎖定配置。刷新可接續選技；短暫斷線留5秒恢復窗口，必要控制器不可用回準備。觀戰只能看選技，不能代選，也不顯示尚未揭露的大招。

94項Vitest、完整8個瀏覽器流程、Python11通過3跳過、跨語言與既有維護驗證全部通過。最後補上選技觀戰唯讀及大招保密後，再執行94項測試與1個完整聚焦瀏覽器流程，驗證品牌、文字、來源與輔助準備、四類選技、刷新、觀戰、開局。未為本次改動重跑混合長測；前文6／30分鐘均為之前修正的歷史結果。

[完整回歸命令](evidence/commands.json)、[最後聚焦驗收](evidence/ui-final.json)、[原始log](evidence/ui-final.log)、[首頁](gesture-arena/evidence/home-v3.png)、[排行榜](gesture-arena/evidence/board-v3.png)、[單人選技](gesture-arena/evidence/solo-draft-v3.png)。
"""
'''
if "## GESTURE ARENA 介面精簡" not in s:s=s.replace(marker,section+marker)
p.write_text(s,encoding='utf-8')
