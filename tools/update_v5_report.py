from pathlib import Path
root=Path(__file__).resolve().parents[1];p=root/'tools/write_report.py';s=p.read_text(encoding='utf-8')
start=s.index("v2=read(")
s=s[:start].replace('94 passed','95 passed').replace('8 passed','9 passed').replace('94項','95項').replace('8個Playwright','9個Playwright').replace('8項Playwright','9項Playwright')+s[start:]
marker="(ROOT/'acceptance_report.md').write_text(report,encoding='utf-8')"
section='''report += f"""
## 單人房號隱藏與獨立配對

日期：{today}。假人練習、一命連戰所有一般畫面不顯示房號；每次建立獨立內部roomId／roomCode，生成時檢查碼碰撞，不會覆蓋其他房間。設定、核心、runId及控制器各自隔離。PVP房號照常顯示。「套用配置」改「套用練習設定」，僅練習提供，戰鬥中不可按；套用假人姿態、位置與全局輔助，重建場景並重設戰鬥狀態。確認準備也會自動套用，無需多按一次。

控制器可省略房號，以全主機唯一的有效六位一次性配對碼定位玩家；提供房碼時仍限制該房。無匹配、歧義或使用過的配對碼拒絕。Python從ACK取得內部房碼，保存供後续自動重連，GUI標示房碼為選填。95項單元測試、9個瀏覽器流程與Python11通過3跳過、實際跨語言全部通過。新增測試驗證不同單人roomId／roomCode、兩名控制器無房號配對正確定位、一次性碼不得重用、修改／啟動練習不改變另一個PVE，以及準備、選技、遊戲時房碼均不出现在畫面。真實Python以空房碼配對PRACTICE／PVE，全部標籤及斷線重連通過。

本次未重跑混合長測；前文長測為歷史證據。[完整驗證命令](evidence/commands.json)、[95項測試](evidence/vitest.log)、[9個瀏覽器流程](evidence/playwright.log)、[Python真實配對與重連](evidence/cross-language.log)。
"""
'''
if '## 單人房號隱藏與獨立配對' not in s:s=s.replace(marker,section+marker)
p.write_text(s,encoding='utf-8')
