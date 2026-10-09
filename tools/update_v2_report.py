"""Keep historical long tests distinct from the current PVP revision."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'tools/write_report.py'
s=p.read_text(encoding='utf-8')
for a,b in [('89 passed','92 passed'),('5 passed','7 passed'),('89項','92項'),('5個Playwright','7個Playwright'),('5項Playwright','7項Playwright'),('最終版本30分鐘混合網路負載','初版30分鐘混合網路負載（歷史）'),('## 完整30分鐘網路長測','## 初版完整30分鐘網路長測（歷史證據）'),('最終30分鐘網路結果','初版30分鐘網路結果')]:
    s=s.replace(a,b)
s=s.replace('另存首輪30分鐘網路baseline', '此次雙人介面與連線修正後另跑6分鐘混合網路及恢復驗證，見文末；以下30分鐘數據來自初版，不能視為本次版本重新跑滿30分鐘。另存首輪30分鐘網路baseline')
marker="(ROOT/'acceptance_report.md').write_text(report,encoding='utf-8')"
section='''v2=read('gesture-arena/evidence/network-v2-6min.json')
assert v2['pass'] and v2['durationSeconds']>=360 and v2['intentionalReconnects']>=1
assert read('gesture-arena/evidence/network-v2-exit.json')['exitCode']==0
report += f"""
## 雙人流程與全畫面修正驗收

日期：{today}。單一加入房間按鈕，最多三人；等待室紅／藍／觀戰原子互換，受影響玩家取消準備。紅藍各一人且準備後自動5秒進選技，觀戰可空缺。紅方固定先選，每手30秒、逾時自選合法技能；已選欄位及普通重複技能禁點，左右列出已選技能，大招公開仍保密，分類與滑鼠說明可用。8手完成自動5秒開戰。兩方介面相同，1920×1080全場景及背景。

92項Vitest、7個完整瀏覽器流程、Python11通過3跳過及跨語言傳輸全部通過。瀏覽器驗證三人成員換位後身分同步、準備重設、觀戰離開後兩人仍可開局、第四人拒絕、完整8手選技及角色移動。停止藍方網站100／500ms計時器後等待6.5秒，實際Socket.IO連線保持PLAYING，證明不再因網站心跳被降速而誤判；真正斷線及辨識器心跳逾時仍安全暫停。1920×1080瀏覽器實測canvas邊界為1920×1080；其他比例保留場景比例。

本次正式設定實際WebSocket混合負載：4房9客戶端、{v2['durationSeconds']:.3f}秒、有意斷線恢復{v2['intentionalReconnects']}次、errors為空；最後p95 {v2['final']['p95StepMs']:.4f}ms、累計落後步數{v2['final']['behindSteps']}。本次未重新跑滿30分鐘，前文數據明列歷史；沒有把舊長測當成本次版本結果。

[本次6分鐘結果](gesture-arena/evidence/network-v2-6min.json)、[原始log](gesture-arena/evidence/network-v2.log)、[退出碼](gesture-arena/evidence/network-v2-exit.json)、[等待室](gesture-arena/evidence/lobby-v2.png)、[選技畫面](gesture-arena/evidence/draft-v2.png)、[對戰畫面](gesture-arena/evidence/pvp-v2.png)。
"""
'''
if "v2=read(" not in s:s=s.replace(marker,section+marker)
p.write_text(s,encoding='utf-8')
print('Updated report generator')
