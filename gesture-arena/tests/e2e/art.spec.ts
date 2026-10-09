import { test, expect } from "@playwright/test";
import { writeFileSync } from "node:fs";

test("mage arena art loads and follows real combat poses and spells", async ({page}) => {
  test.setTimeout(90000);
  await page.setViewportSize({width:1920,height:1080});
  await page.addInitScript(()=>{
    const Original=window.WebSocket;
    (window as any).artFreezeBeam=false;
    window.WebSocket=class extends Original {
      constructor(url:string|URL, protocols?:string|string[]) {
        super(url,protocols);
        this.addEventListener("message",e=>{
          if(!(window as any).artFreezeBeam || typeof e.data!=="string" || !e.data.startsWith("42/arena,"))return;
          try {
            const [event,state]=JSON.parse(e.data.slice(e.data.indexOf("[")));
            if(["room:state","match:snapshot"].includes(event) && state.core?.objects?.some((o:any)=>o.skill==="beam")) {
              (window as any).artFreezeBeam=false;
              Array.from(document.querySelectorAll("button")).find(b=>b.textContent==="暫停")?.click();
            }
          }catch{}
        });
      }
    };
  });
  const states:any[]=[]; const errors:string[]=[]; const assets:string[]=[];
  page.on("pageerror",e=>errors.push(e.message));
  page.on("response",r=>{if(/(?:mage-sheet|terrace)-v6/.test(r.url())) {expect(r.status()).toBe(200);assets.push(r.url());}});
  page.on("websocket",ws=>ws.on("framereceived",frame=>{
    const payload=String(frame.payload);
    if(payload.startsWith("42/arena,"))try {
      const [event,state]=JSON.parse(payload.slice(payload.indexOf("[")));
      if(event==="room:state"||event==="match:snapshot") {
        states.push(state);
      }
    }catch{}
  }));
  await page.goto("/");
  await page.getByRole("button",{name:/假人練習/}).click();
  await page.getByRole("combobox",{name:"控制來源"}).selectOption("keyboard");
  for(const name of ["無限氣","取消冷卻","立即解鎖大招","假人不死"])await page.getByLabel(name,{exact:true}).check();
  await page.getByRole("button",{name:"確認準備",exact:true}).click();
  for(const [category,skill] of [["大招","星隕光束"],["攻擊","火球術"],["防禦","護盾術"],["控制","束縛印"]]) {
    await page.getByRole("navigation",{name:"選技分類"}).getByRole("button",{name:category,exact:true}).click();
    await page.getByRole("button",{name:skill,exact:true}).click();
  }
  await expect.poll(()=>states.at(-1)?.phase).toBe("PLAYING");
  await page.getByRole("button",{name:"全螢幕觀戰",exact:true}).click();
  await expect.poll(async()=> (await page.locator("canvas").boundingBox())?.width).toBeCloseTo(1920,0);
  await page.locator("canvas").click();await page.waitForTimeout(200);
  await page.screenshot({path:"evidence/art-idle-v6.png"});
  await page.keyboard.down("s");await expect.poll(()=>states.at(-1)?.core?.actors[0]?.crouch).toBe(true);
  await page.waitForTimeout(120);await page.screenshot({path:"evidence/art-crouch-v6.png"});await page.keyboard.up("s");
  await page.keyboard.down(" ");await expect.poll(()=>states.at(-1)?.core?.actors[0]?.blocking).toBe(true);
  await page.screenshot({path:"evidence/art-guard-v6.png"});await page.keyboard.up(" ");
  await page.waitForTimeout(180);await page.keyboard.down("k");
  await expect.poll(()=>states.at(-1)?.core?.actors[0]?.cast?.skill).toBe("fireball");
  await page.keyboard.up("k");
  await expect.poll(()=>states.at(-1)?.core?.objects?.some((o:any)=>o.skill==="fireball")).toBe(true);
  await page.screenshot({path:"evidence/art-fireball-v6.png"});
  await page.waitForTimeout(700);await page.keyboard.down("l");
  await expect.poll(()=>states.at(-1)?.core?.actors[0]?.shield).toBeGreaterThan(0);
  await page.keyboard.up("l");await page.screenshot({path:"evidence/art-shield-v6.png"});
  await page.waitForTimeout(400);await page.keyboard.down("i");
  await expect.poll(()=>states.at(-1)?.core?.actors[0]?.cast?.skill).toBe("beam");
  await page.keyboard.up("i");await page.screenshot({path:"evidence/art-warning-v6.png"});
  await expect.poll(()=>states.at(-1)?.core?.actors[0]?.busy).toBe(0);
  await page.evaluate(()=>(window as any).artFreezeBeam=true);
  await page.keyboard.down("i");
  await expect.poll(()=>states.at(-1)?.core?.actors[0]?.cast?.skill).toBe("beam");
  await page.keyboard.up("i");
  await expect.poll(()=>states.at(-1)?.phase,{timeout:5000}).toBe("PAUSED");
  expect(states.at(-1).core.objects.some((o:any)=>o.skill==="beam")).toBe(true);
  await page.screenshot({path:"evidence/art-beam-v6.png"});
  await page.evaluate(()=>Array.from(document.querySelectorAll("button")).find(b=>b.textContent==="確認準備並恢復")?.click());
  await expect.poll(()=>states.at(-1)?.phase,{timeout:8000}).toBe("PLAYING");
  const frameTimes=await page.evaluate(()=>new Promise<number[]>(resolve=>{
    const samples:number[]=[];let previous=performance.now();const start=previous;
    const frame=(now:number)=>{samples.push(now-previous);previous=now;if(now-start>=3000)resolve(samples);else requestAnimationFrame(frame);};requestAnimationFrame(frame);
  }));
  frameTimes.sort((a,b)=>a-b);
  expect(new Set(assets).size).toBe(2);expect(errors).toEqual([]);
  expect(states.at(-1).phase).toBe("PLAYING");
  writeFileSync("evidence/art-browser-v6.json",JSON.stringify({date:new Date().toISOString(),viewport:{width:1920,height:1080},assets,errors,phase:states.at(-1).phase,renderSample:{seconds:3,frames:frameTimes.length,medianMs:frameTimes[Math.floor(frameTimes.length*.5)],p95Ms:frameTimes[Math.floor(frameTimes.length*.95)]},scope:"Real practice server, fullscreen, idle, crouch, guard, fireball, shield, beam warning and active beam frozen through the real pause control for visual inspection, followed by successful resume. Headless frame timings are diagnostic, not an on-site hardware guarantee."},null,2));
});
