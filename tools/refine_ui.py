from pathlib import Path
root=Path(__file__).resolve().parents[1]; p=root/'gesture-arena/apps/web/src/main.tsx';s=p.read_text(encoding='utf-8')
s=s.replace('import { PvpRoom } from "./pvp";', 'import { PvpRoom } from "./pvp";\nimport { SoloDraft } from "./solo-draft";')
s=s.replace('✦ 手勢競技場 <small>GESTURE ARENA</small>', 'GESTURE ARENA')
s=s.replace('        <span className="badge">{health?.arenaName ?? "本機競技場"}</span>\n','')
a=s.index('            <section className="hero">');b=s.index('            <section className="entry">',a)
s=s[:a]+'''            <section className="home-intro"><p className="eyebrow">PLAY</p><h1>選擇模式</h1></section>
'''+s[b:]
s=s.replace('全部 25 招','全部')
a=s.index('            <p>\n              擊敗數由');b=s.index('            <table>',a);s=s[:a]+s[b:]
s=s.replace('<th>擊敗</th>','<th>擊殺</th>').replace('<th>有效時間</th>','<th>遊戲時間</th>').replace('<th>來源／終止</th>','<th>操作模式</th>')
s=s.replace('{r.sourceHistory.join(" → ")} / {r.reason}', '{r.sourceHistory.map((source:string)=>({recognizer:"手勢辨識",keyboard:"鍵盤",simulated:"模擬輸入"} as Record<string,string>)[source]??source).join(" → ")}')
s=s.replace('            <div className="room-body">','            {state.phase === "SOLO_DRAFT" ? <SoloDraft state={state} request={request}/> : <div className="room-body">')
s=s.replace('                {state.core ? (','                {state.core && state.phase !== "CONFIG" ? (')
s=s.replace('<h3>房間 {state.roomCode}</h3>', '<h3>房號：{state.roomCode}</h3>')
old='''onClick={() =>
                        request("player:ready", { ready: !me?.ready })
                      }'''
new='''disabled={me?.source !== "keyboard" && !me?.algorithmsAvailable}
                      onClick={async () => {
                        const ready = await request("player:ready", { ready: !me?.ready });
                        if (ready && !me?.ready && ["CONFIG","RESULT"].includes(state.phase)) {
                          const configured = await request("solo:configure", {loadout,dummy,dummyX,aids});
                          if (configured) await request("solo:select");
                        }
                      }}'''
assert old in s;s=s.replace(old,new)
a=s.index('                    <h3>技能配置</h3>');b=s.index('                    {state.mode === "PRACTICE" && (',a)
s=s[:a]+s[b:]
a=s.index('                    <button\n                      onClick={() =>\n                        request(\n                          state.mode === "PVE" ? "pve:start"');b=s.index('                    {state.mode === "PRACTICE" && (',a)
s=s[:a]+'''                    {["CONFIG","RESULT","PAUSED"].includes(state.phase) && !(state.mode==="PVE" && state.run && !state.run.result) && me?.ready && <button onClick={()=>request("solo:select")}>重新選技</button>}
'''+s[b:]
s=s.replace('                    <h3>本房管理</h3>', '                    <h3>對戰控制</h3>')
s=s.replace('            </div>\n          </>\n        )}\n      </main>', '            </div>}\n          </>\n        )}\n      </main>')
a=s.index('      <footer>');b=s.index('      </footer>',a)+len('      </footer>');s=s[:a]+s[b:]
p.write_text(s,encoding='utf-8')
p=root/'gesture-arena/apps/web/index.html';p.write_text(p.read_text().replace('<title>手勢競技場</title>','<title>GESTURE ARENA</title>'),encoding='utf-8')
p=root/'gesture-arena/apps/web/src/pvp.tsx';s=p.read_text();s=s.replace('雙人對戰 · 房間 <b>', '雙人對戰 · 房號：<b>');s=s.replace('<span>紅方先選 · 最多 3 人</span><button onClick={leave}>離開房間</button></div>\n    <h1>', '<span className="lobby-first-pick">紅方先選</span><button onClick={leave}>離開房間</button></div>\n    <h1>');s=s.replace('"入席，準備對戰"','"準備對戰"');s=s.replace('<span>房間 {state.roomCode}</span>','<span>房號：{state.roomCode}</span>');s=s.replace('房間 {state.roomCode} ·','房號：{state.roomCode} ·');p.write_text(s,encoding='utf-8')
print('UI refined')
