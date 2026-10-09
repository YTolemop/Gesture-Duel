import { test, expect } from "@playwright/test";
import { io } from "socket.io-client";
async function selectSolo(page:any) {
  await expect(page.locator(".solo-draft")).toBeVisible();
  for (const [category,skill] of [["大招","星隕光束"],["攻擊","穿雲槍"],["防禦","護盾術"],["控制","束縛印"]]) {
    await page.getByRole("navigation",{name:"選技分類"}).getByRole("button",{name:category,exact:true}).click();
    await page.getByRole("button",{name:skill,exact:true}).click();
  }
}
test("minimal copy and solo preparation leads to persistent in-game selection", async ({page})=>{
  await page.setViewportSize({width:1920,height:1080});await page.goto("/");
  await expect(page).toHaveTitle("GESTURE ARENA");await expect(page.locator(".brand")).toHaveText("GESTURE ARENA");
  await expect(page.locator("footer,.badge,.hero")).toHaveCount(0);
  await page.screenshot({path:"evidence/home-v3.png",fullPage:true});
  await page.getByRole("button",{name:"排行榜",exact:true}).click();
  for(const name of ["擊殺","遊戲時間","操作模式"])await expect(page.getByRole("columnheader",{name,exact:true})).toBeVisible();
  await expect(page.getByRole("button",{name:/切換/})).toHaveCount(0);
  await page.screenshot({path:"evidence/board-v3.png",fullPage:true});
  await page.getByRole("button",{name:"技能圖鑑",exact:true}).click();await expect(page.getByRole("option",{name:"全部",exact:true})).toHaveCount(1);
  await page.getByRole("button",{name:"首頁",exact:true}).click();await page.getByRole("button",{name:/假人練習/}).click();
  await expect(page.getByText("技能配置",{exact:true})).toHaveCount(0);await expect(page.locator("canvas")).toHaveCount(0);
  await page.getByRole("combobox",{name:"控制來源"}).selectOption("keyboard");await page.getByLabel("無限氣",{exact:true}).check();
  await page.getByRole("button",{name:"確認準備",exact:true}).click();await expect(page.locator(".solo-draft")).toBeVisible();
  await page.getByRole("button",{name:"星隕光束",exact:true}).click();
  await expect(page.getByRole("button",{name:"大招 ✓",exact:true})).toBeDisabled();
  await page.reload();await expect(page.locator(".solo-draft")).toBeVisible();await expect(page.getByRole("button",{name:"大招 ✓",exact:true})).toBeDisabled();
  const observer=await page.context().newPage();await observer.goto("/");
  const room=await page.evaluate(()=>JSON.parse(sessionStorage.getItem("arena-auth")!).roomCode);
  await observer.getByLabel("房間碼").fill(room);await observer.getByRole("button",{name:"加入房間",exact:true}).click();
  await expect(observer.locator(".solo-draft")).toBeVisible();await expect(observer.getByRole("button",{name:"穿雲槍",exact:true})).toBeDisabled();
  await expect(observer.locator(".selected-skill").first()).toContainText("已鎖定");await expect(observer.locator(".selected-skill").first()).not.toContainText("星隕光束");await observer.close();
  await page.getByRole("button",{name:"穿雲槍",exact:true}).hover();await expect(page.getByRole("tooltip")).toContainText("冷卻");
  await page.screenshot({path:"evidence/solo-draft-v3.png",fullPage:true});
  for (const [category,skill] of [["攻擊","穿雲槍"],["防禦","護盾術"],["控制","束縛印"]]) {await page.getByRole("navigation",{name:"選技分類"}).getByRole("button",{name:category,exact:true}).click();await page.getByRole("button",{name:skill,exact:true}).click();}
  await expect(page.locator("canvas")).toBeVisible();await expect(page.getByText("練習輔助：",{exact:false})).toContainText("無限氣");
});
test("copied same-browser tab gets its own seat while refresh restores the original", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /雙人對決/ }).click();
  await expect(page.locator(".pvp-lobby")).toBeVisible();
  const original = await page.evaluate(() => JSON.parse(sessionStorage.getItem("arena-auth")!));
  const [copy] = await Promise.all([
    page.waitForEvent("popup"), page.evaluate(() => { window.open("/", "_blank"); }),
  ]);
  await expect(copy.getByRole("button", { name: /雙人對決/ })).toBeEnabled();
  await copy.getByLabel("房間碼").fill(original.roomCode);
  await copy.getByRole("button", { name: "加入房間" }).click();
  await expect(copy.locator(".pvp-lobby")).toBeVisible();
  const blue = await copy.evaluate(() => JSON.parse(sessionStorage.getItem("arena-auth")!));
  expect(blue.seat).toBe("blue"); expect(blue.playerToken).not.toBe(original.playerToken);
  await page.reload();
  await expect(page.locator(".pvp-lobby")).toBeVisible();
  expect(await page.evaluate(() => JSON.parse(sessionStorage.getItem("arena-auth")!).playerToken)).toBe(original.playerToken);
  await expect(copy.locator(".pvp-lobby")).toBeVisible();
  await expect(copy.getByRole("alert")).toHaveCount(0);
  await copy.close();
});
test("room members swap occupied seats, reset readiness and can start without an observer", async ({ browser }) => {
  const contexts = await Promise.all(Array.from({length:3},()=>browser.newContext({viewport:{width:1920,height:1080}})));
  const [red,blue,watch] = await Promise.all(contexts.map(c=>c.newPage()));
  const seat = (p:any) => p.evaluate(()=>JSON.parse(sessionStorage.getItem("arena-auth") ?? "null")?.seat);
  try {
    await Promise.all([red,blue,watch].map(p=>p.goto("/")));
    await red.getByRole("button",{name:/雙人對決/}).click();
    await expect(red.locator(".pvp-lobby")).toBeVisible();
    const room = await red.evaluate(()=>JSON.parse(sessionStorage.getItem("arena-auth")!).roomCode);
    for (const p of [blue,watch]) { await p.getByLabel("房間碼").fill(room); await p.getByRole("button",{name:"加入房間",exact:true}).click(); }
    await expect.poll(()=>seat(watch)).toBe("spectator");
    await red.getByRole("combobox",{name:"控制來源",exact:true}).selectOption("keyboard");
    await red.getByRole("button",{name:"確認準備",exact:true}).click();
    await watch.getByRole("button",{name:"換到紅方",exact:true}).click();
    await expect.poll(()=>seat(watch)).toBe("red");
    await expect.poll(()=>seat(red)).toBe("spectator");
    await expect(red.getByRole("button",{name:"確認準備",exact:true})).toHaveCount(0);
    await expect(watch.getByRole("button",{name:"確認準備",exact:true})).toBeVisible();
    await blue.getByRole("button",{name:"換到紅方",exact:true}).click();
    await expect.poll(()=>seat(blue)).toBe("red");
    await expect.poll(()=>seat(watch)).toBe("blue");
    await expect(blue.getByRole("button",{name:"確認準備",exact:true})).toBeVisible();
    red.once("dialog",dialog=>dialog.accept());
    await red.getByRole("button",{name:"離開房間",exact:true}).click();
    await expect(watch.locator(".seat-spectator h2")).toHaveText("空位");
    await watch.screenshot({path:"evidence/lobby-v2.png",fullPage:true});
    for (const p of [blue,watch]) { await p.getByRole("combobox",{name:"控制來源",exact:true}).selectOption("keyboard"); await p.getByRole("button",{name:"確認準備",exact:true}).click(); }
    await expect(blue.getByRole("heading",{name:/秒後進入技能選擇/})).toBeVisible();
    await expect(blue.locator(".draft-shell")).toBeVisible({timeout:8000});
    await expect(blue.getByRole("heading",{name:"輪到你選擇技能",exact:true})).toBeVisible();
    for (const p of [blue,watch]) await expect(p.getByRole("alert")).toHaveCount(0);
  } finally { await Promise.all(contexts.map(c=>c.close())); }
});

test("leaderboard renders hostile nicknames as text", async ({ page }) => {
  // Rendering fixture only; database integrity is independently checked with SQLite.
  await page.route("**/api/leaderboard*", (route) => route.fulfill({
    json: [{ runId: "render-fixture", nickname: "<img src=x>", defeated: 3, ticks: 600, reason: "death", sourceHistory: ["recognizer"] }],
  }));
  await page.goto("/");
  await page.getByRole("button", { name: "排行榜", exact: true }).click();
  await expect(page.getByRole("cell", { name: "<img src=x>", exact: true })).toBeVisible();
  await expect(page.locator("table img")).toHaveCount(0);
});
test("solo codes stay hidden and simultaneous practice/PVE sessions remain independent",async({browser})=>{
  const contexts=await Promise.all([browser.newContext(),browser.newContext()]);
  const [practice,pve]=await Promise.all(contexts.map(c=>c.newPage()));
  try{
    await Promise.all([practice,pve].map(p=>p.goto("/")));
    await practice.getByRole("button",{name:/假人練習/}).click();await pve.getByRole("button",{name:/一命連戰/}).click();
    await expect(practice.locator(".solo-lobby")).toBeVisible();await expect(pve.locator(".solo-lobby")).toBeVisible();
    const credentials=await Promise.all([practice,pve].map(p=>p.evaluate(()=>JSON.parse(sessionStorage.getItem("arena-auth")!))));
    expect(credentials[0].roomCode).not.toBe(credentials[1].roomCode);
    for(let i=0;i<2;i++)await expect([practice,pve][i].locator("body")).not.toContainText(credentials[i].roomCode);
    await practice.getByRole("combobox",{name:"控制來源"}).selectOption("keyboard");
    await practice.getByLabel("無限氣",{exact:true}).check();await practice.getByRole("button",{name:"確認準備",exact:true}).click();
    await selectSolo(practice);await expect(practice.locator("canvas")).toBeVisible();
    await expect(practice.getByText("練習輔助：",{exact:false})).toContainText("無限氣");
    await expect(pve.locator(".solo-lobby")).toBeVisible();await expect(pve.locator("canvas,.solo-draft")).toHaveCount(0);
    await expect(pve.getByRole("button",{name:"確認準備",exact:true})).toBeVisible();
    for(let i=0;i<2;i++)await expect([practice,pve][i].locator("body")).not.toContainText(credentials[i].roomCode);
  }finally{await Promise.all(contexts.map(c=>c.close()));}
});
test("self-service PVP draft, locked slots, background health and full stage", async ({ browser }) => {
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
  await red.waitForTimeout(200);
  await red.screenshot({path:"evidence/hud-countdown-v4.png",fullPage:true});
  await expect.poll(()=>states.at(-1)?.phase,{timeout:8000}).toBe("PLAYING");
  const stage=await red.locator("canvas").boundingBox();expect(stage?.width).toBe(1920);expect(stage?.height).toBe(1080);
  await red.locator("canvas").click();const x=states.at(-1).core.actors[0].x;
  await red.keyboard.down("d");await red.waitForTimeout(600);await red.keyboard.up("d");
  await expect.poll(()=>states.at(-1).core.actors[0].x).toBeGreaterThan(x+20);
  await blue.evaluate(()=>(window as any).testIntervals.forEach((id:number)=>clearInterval(id)));
  await red.waitForTimeout(6500);
  expect(states.at(-1).phase).toBe("PLAYING");expect(states.at(-1).players[1].connected).toBe(true);
  await red.screenshot({path:"evidence/pvp-v2.png",fullPage:true});
  await red.screenshot({path:"evidence/hud-v4.png",fullPage:true});
  await Promise.all(contexts.map(c=>c.close()));
});
test("PVE configuration lock, source switch during pause and keyboard blur safety", async ({
  page,
}) => {
  const states: any[] = [];
  page.on("websocket", (ws) =>
    ws.on("framereceived", (frame) => {
      const payload = String(frame.payload);
      if (payload.startsWith("42/arena,")) {
        try {
          const [event, state] = JSON.parse(
            payload.slice(payload.indexOf("[")),
          );
          if (event === "room:state" || event === "match:snapshot")
            states.push(state);
        } catch {}
      }
    }),
  );
  await page.goto("/");
  await page.getByRole("button", { name: /一命連戰/ }).click();
  await page
    .getByRole("combobox", { name: /控制來源/ })
    .selectOption("keyboard");
  await page.getByRole("button", { name: "確認準備", exact: true }).click();
  await selectSolo(page);
  await page.waitForTimeout(3400);
  await page.locator("canvas").click();
  await page.keyboard.down("d");
  await page.waitForTimeout(200);
  await page.evaluate(() => window.dispatchEvent(new Event("blur")));
  await expect.poll(() => states.at(-1)?.core?.actors[0]?.label).toBe("NONE");
  await page.keyboard.up("d");
  await page.getByRole("button", { name: "暫停", exact: true }).click();
  await expect.poll(() => states.at(-1)?.phase).toBe("PAUSED");
  const before = states.at(-1).core,
    run = states.at(-1).run.runId;
  await expect(page.getByRole("button", { name: "套用練習設定", exact:true })).toHaveCount(0);
  await page
    .getByRole("combobox", { name: /控制來源/ })
    .selectOption("recognizer");
  await expect.poll(() => states.at(-1)?.players[0]?.source).toBe("recognizer");
  await page
    .getByRole("combobox", { name: /控制來源/ })
    .selectOption("keyboard");
  await page.getByRole("button", { name: "確認準備", exact: true }).click();
  await expect.poll(() => states.at(-1)?.players[0]?.ready).toBe(true);
  expect(states.at(-1).core.tick).toBe(before.tick);
  expect(states.at(-1).core.actors[0].hp).toBe(before.actors[0].hp);
  expect(states.at(-1).run.runId).toBe(run);
});
test("formal simulated controller pairing rejected, no score write API", async ({
  page,
}) => {
  const before = await (await page.request.get("/api/leaderboard")).text();
  const score = await page.request.post("/api/leaderboard", {
    data: { defeated: 999999 },
  });
  expect(score.status()).toBe(404);
  expect(await (await page.request.get("/api/leaderboard")).text()).toBe(
    before,
  );
  await page.goto("/");
  await page.getByRole("button", { name: /假人練習/ }).click();
  await page.getByRole("button", { name: "產生配對碼" }).click();
  const code = (await page.locator(".pair-code").textContent())!.match(
    /\d{6}/,
  )![0];
  const room = await page.evaluate(()=>JSON.parse(sessionStorage.getItem("arena-auth")!).roomCode);
  const controller = io("http://127.0.0.1:3000/controller", {
    transports: ["websocket"],
  });
  try {
    await new Promise<void>((r) => controller.once("connect", () => r()));
    const ack: any = await controller
      .timeout(5000)
      .emitWithAck("controller:pair", {
        requestId: "formal-fixture",
        protocolVersion: 1,
        roomCode: room,
        pairCode: code,
        source: "simulated",
      });
    expect(ack.errorCode).toBe("INTERNAL_MODE_REQUIRED");
  } finally {
    controller.disconnect();
  }
});
test("codex 25 skills, search, real practice and aids", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "技能圖鑑", exact: true }).click();
  await expect(page.locator(".skill-grid article")).toHaveCount(25);
  await page.getByLabel("搜尋技能").fill("穿雲");
  await expect(page.locator(".skill-grid article")).toHaveCount(1);
  await page.getByRole("button", { name: /到練習場/ }).click();
  await page
    .getByRole("combobox", { name: /控制來源/ })
    .selectOption("keyboard");
  await page.getByLabel("無限氣", { exact: true }).check();
  await page.getByLabel("假人 x").fill("700");
  await page.getByRole("button", { name: "套用練習設定", exact:true }).click();
  await page.getByRole("button", { name: "確認準備", exact: true }).click();
  await selectSolo(page);
  await expect(page.locator("canvas")).toBeVisible();
  await page.waitForTimeout(3300);
  await page.locator("canvas").click();
  await page.keyboard.down("k");
  await page.waitForTimeout(1800);
  await page.keyboard.up("k");
  await page.getByText("最近命中詳細紀錄").click();
  await expect(page.getByText("原傷240", { exact: false })).toBeVisible();
  await expect(page.getByText("練習輔助：", { exact: false })).toBeVisible();
  await page.screenshot({ path: "evidence/practice.png", fullPage: true });
});
