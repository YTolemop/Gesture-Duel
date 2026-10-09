from pathlib import Path
p=Path(__file__).resolve().parents[1]/'gesture-arena/tests/e2e/arena.spec.ts'
s=p.read_text(encoding='utf-8');a=s.index('test("independent red/blue/spectator');b=s.index('test("PVE configuration',a)
s=s[:a]+'''test("self-service PVP draft, locked slots, background health and full stage", async ({ browser }) => {
  const contexts = await Promise.all(Array.from({length:4},()=>browser.newContext({viewport:{width:1920,height:1080}})));
  const [red,blue,watch,extra] = await Promise.all(contexts.map(c=>c.newPage()));
  await blue.addInitScript(()=>{ const original=window.setInterval; (window as any).testIntervals=[]; window.setInterval=((...args:any[])=>{const id=original(...args as [any,number]);if(args[1]===100||args[1]===500)(window as any).testIntervals.push(id);return id;}) as typeof window.setInterval; });
  const states:any[]=[];
  watch.on("websocket", ws=>ws.on("framereceived",frame=>{const payload=String(frame.payload);if(payload.startsWith("42/arena,")){try{const [event,state]=JSON.parse(payload.slice(payload.indexOf("[")));if(event==="room:state"||event==="match:snapshot")states.push(state);}catch{}}}));
  await Promise.all([red,blue,watch,extra].map(p=>p.goto("/")));
  await red.getByRole("button",{name:/雙人對決/}).click();
  await expect(red.locator(".pvp-lobby")).toBeVisible();
  const room=await red.evaluate(()=>JSON.parse(sessionStorage.getItem("arena-auth")!).roomCode);
  for(const p of [blue,watch,extra]) { await p.getByLabel("房間碼").fill(room);await p.getByRole("button",{name:"加入房間",exact:true}).click(); }
  await expect(extra.getByRole("alert")).toContainText("SPECTATOR_FULL");
  await expect(red.getByRole("button",{name:"開始選技"})).toHaveCount(0);
  await expect(blue.getByRole("button",{name:"確認準備"})).toBeVisible();
  await expect(watch.getByRole("button",{name:"確認準備"})).toHaveCount(0);
  for(const p of [red,blue]) { await p.getByRole("combobox",{name:"控制來源",exact:true}).selectOption("keyboard");await p.getByRole("button",{name:"確認準備",exact:true}).click(); }
  await expect(red.getByRole("heading",{name:/秒後進入技能選擇/})).toBeVisible();
  await expect(red.locator(".draft-shell")).toBeVisible({timeout:8000});
  await expect(red.getByRole("heading",{name:"輪到你選擇技能"})).toBeVisible();
  const picks=["星隕光束","星隕光束","火球術","穿雲槍","護盾術","鏡返術","寒冰彈","束縛印"], turns=[red,blue,blue,red,red,blue,blue,red], categories=["大招","大招","攻擊","攻擊","防禦","防禦","控制","控制"];
  for(let i=0;i<8;i++) {
    const p=turns[i];await expect(p.locator(".draft-heading")).toContainText(`第 ${i+1} 手 / 8`);
    await p.getByRole("navigation",{name:"選技分類"}).getByRole("button",{name:categories[i],exact:true}).click();
    if(i===2){await p.getByRole("button",{name:"火球術",exact:true}).hover();await expect(p.getByRole("tooltip")).toContainText("冷卻");}
    if(i===3){await expect(p.getByRole("button",{name:"火球術",exact:true})).toBeDisabled();await expect(p.getByRole("alert")).toHaveCount(0);}
    await p.getByRole("button",{name:picks[i],exact:true}).click();
    if(i===3)await expect(red.getByRole("navigation",{name:"選技分類"}).getByRole("button",{name:"攻擊 ✓",exact:true})).toBeDisabled();
    if(i===4)await red.screenshot({path:"evidence/draft-v2.png",fullPage:true});
  }
  await expect(red.locator("canvas")).toBeVisible();
  await expect.poll(()=>states.at(-1)?.phase,{timeout:8000}).toBe("PLAYING");
  const stage=await red.locator("canvas").boundingBox();expect(stage?.width).toBe(1920);expect(stage?.height).toBe(1080);
  await red.locator("canvas").click();const x=states.at(-1).core.actors[0].x;
  await red.keyboard.down("d");await red.waitForTimeout(600);await red.keyboard.up("d");
  await expect.poll(()=>states.at(-1).core.actors[0].x).toBeGreaterThan(x+20);
  await blue.evaluate(()=>(window as any).testIntervals.forEach((id:number)=>clearInterval(id)));
  await red.waitForTimeout(6500);
  expect(states.at(-1).phase).toBe("PLAYING");expect(states.at(-1).players[1].connected).toBe(true);
  await red.screenshot({path:"evidence/pvp-v2.png",fullPage:true});
  await Promise.all(contexts.map(c=>c.close()));
});
''' + s[b:]
p.write_text(s,encoding='utf-8')
print('PVP browser acceptance updated')
