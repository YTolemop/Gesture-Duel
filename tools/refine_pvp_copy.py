from pathlib import Path
p=Path(__file__).resolve().parents[1]/'gesture-arena/apps/web/src/pvp.tsx'
s=p.read_text(encoding='utf-8').replace('雙人對戰 · 房間 <b>','雙人對戰 · 房號：<b>')
s=s.replace('<span>紅方先選 · 最多 3 人</span><button onClick={leave}>離開房間</button></div>\n    <h1>', '<span className="lobby-first-pick">紅方先選</span><button onClick={leave}>離開房間</button></div>\n    <h1>')
s=s.replace('"入席，準備對戰"','"準備對戰"').replace('<span>房間 {state.roomCode}</span>','<span>房號：{state.roomCode}</span>').replace('房間 {state.roomCode} ·','房號：{state.roomCode} ·')
p.write_text(s,encoding='utf-8')
