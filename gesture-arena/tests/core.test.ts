import { describe, it, expect } from "vitest";
import { GameCore } from "../packages/game-core/core.js";
import {
  SKILLS,
  BY_ID,
  DEFAULT_LOADOUT,
  ticks,
} from "../packages/game-core/skills.js";
import { InputRouter } from "../packages/game-core/input.js";
import { box, overlap, sweep } from "../packages/game-core/geometry.js";
import {
  AIController,
  aiLoadout,
  difficulty,
} from "../packages/game-core/ai.js";
const run = (c: GameCore, n: number) => {
  for (let i = 0; i < n; i++) c.step();
};
const start = (c: GameCore, i: number, label: any) => {
  c.input(i, "NONE");
  run(c, 6);
  c.input(i, label);
  c.step();
};
describe("independent numeric geometry and input contracts", () => {
  it("25 unique registry entries, exact costs and whole ticks", () => {
    expect(SKILLS).toHaveLength(25);
    expect(new Set(SKILLS.map((s) => s.id)).size).toBe(25);
    for (const s of SKILLS) {
      for (const v of [
        s.cooldown,
        s.prepare,
        s.recovery,
        s.window ?? 0,
        s.life ?? 0,
        s.duration ?? 0,
      ])
        expect(v * 60).toBeCloseTo(ticks(v));
      if (s.speed) expect(s.speed * s.life!).toBeCloseTo(s.range!);
    }
  });
  it("strict overlap and rounded swept circle corners", () => {
    expect(
      overlap({ kind: "rect", w: 100, h: 120 }, 132, 840, box(214, 900)),
    ).toBe(false);
    expect(overlap(BY_ID.spear.shape!, 480, 784, box(480, 900, true))).toBe(
      false,
    );
    expect(
      sweep({ kind: "circle", r: 10 }, -20, -20, 10, 10, {
        x: 0,
        y: 0,
        w: 20,
        h: 20,
      }),
    ).toBeNull();
    expect(
      sweep({ kind: "circle", r: 10 }, -30, 10, 100, 0, {
        x: 0,
        y: 0,
        w: 20,
        h: 20,
      }),
    ).toBeCloseTo(0.2);
  });
  it("exact 224px apex and .8s flight", () => {
    const c = new GameCore("PRACTICE");
    start(c, 0, "JUMP");
    run(c, 23);
    expect(c.actors[0].y).toBeCloseTo(676);
    run(c, 24);
    expect(c.actors[0].y).toBe(900);
    expect(c.actors[0].ground).toBe(true);
  });
  it("per-label rearm, fast A→B, NONE jitter and timeout", () => {
    const r = new InputRouter();
    r.receive("NONE", 0);
    r.advance(6);
    r.receive("NORMAL_ATTACK", 6);
    expect(r.consume()).toEqual(["NORMAL_ATTACK"]);
    r.receive("ATTACK_SKILL", 7);
    expect(r.consume()).toEqual(["ATTACK_SKILL"]);
    r.receive("NORMAL_ATTACK", 8);
    expect(r.consume()).toEqual([]);
    r.receive("NONE", 9);
    r.receive("NORMAL_ATTACK", 14);
    expect(r.consume()).toEqual([]);
    r.receive("NONE", 15);
    r.receive("NORMAL_ATTACK", 21);
    expect(r.consume()).toEqual(["NORMAL_ATTACK"]);
    r.receive("MOVE_RIGHT", 22);
    r.advance(53);
    expect(r.label).toBe("NONE");
  });
  it("holding rejected action never queues it", () => {
    const c = new GameCore("PRACTICE");
    c.actors[0].qi = 0;
    start(c, 0, "ATTACK_SKILL");
    c.actors[0].qi = 720;
    for (let i = 0; i < 180; i++) {
      c.input(0, "ATTACK_SKILL");
      c.step();
    }
    expect(c.hits).toHaveLength(0);
    expect(c.actors[0].cooldowns.fireball).toBeUndefined();
  });
});
describe("all skills, timing, damage and interactions", () => {
  for (const skill of SKILLS)
    it(`${skill.id} accepted, pays exact cost, generates at prepare tick`, () => {
      const c = new GameCore("PRACTICE");
      if (skill.slot !== "normal") c.actors[0].loadout[skill.slot] = skill.id;
      c.elapsed[0] = 1200;
      c.actors[1].x = 700;
      const label: any =
        skill.slot === "normal"
          ? "NORMAL_ATTACK"
          : (
              {
                attack: "ATTACK_SKILL",
                defense: "DEFENSE_SKILL",
                control: "CONTROL_SKILL",
                ultimate: "ULTIMATE",
              } as any
            )[skill.slot];
      start(c, 0, label);
      const cast = c.actors[0].cast!;
      expect(cast.skill).toBe(skill.id);
      expect(c.actors[0].qi).toBe(720 - skill.cost * 120);
      expect(c.actors[0].cooldowns[skill.id]).toBe(
        cast.start + ticks(skill.cooldown),
      );
      run(c, ticks(skill.prepare) - 1);
      expect(c.actors[0].cast).not.toBeNull();
      c.step();
      expect(c.actors[0].cast).toBeNull();
      expect(c.actors[0].busy).toBe(
        cast.generate + ticks(skill.recovery) + (skill.id === "normal" ? 6 : 0),
      );
    });
  it("spear can be ducked; fireball cannot", () => {
    for (const [id, hp] of [
      ["spear", 1000],
      ["fireball", 900],
    ] as const) {
      const c = new GameCore("PRACTICE");
      c.actors[0].loadout.attack = id;
      c.actors[1].x = 700;
      c.actors[1].input.needsNone = false;
      c.actors[1].input.label = "CROUCH";
      c.actors[1].input.lastTick = 1000;
      start(c, 0, "ATTACK_SKILL");
      run(c, 150);
      expect(c.actors[1].hp).toBe(hp);
    }
  });
  it("normal edge contact, miss never drains guard", () => {
    const c = new GameCore("PRACTICE");
    c.actors[1].x = 644;
    c.actors[1].input.needsNone = false;
    c.actors[1].input.label = "BLOCK";
    c.actors[1].input.lastTick = 1000;
    start(c, 0, "NORMAL_ATTACK");
    run(c, 50);
    expect(c.actors[1].hp).toBe(1000);
    expect(c.actors[1].qi).toBe(720);
  });
  it("meteor blocks three waves for132hp and only half qi", () => {
    const c = new GameCore("PRACTICE");
    c.actors[0].loadout.ultimate = "meteor";
    c.elapsed[0] = 1200;
    c.actors[1].input.needsNone = false;
    c.actors[1].input.label = "BLOCK";
    c.actors[1].input.lastTick = 1000;
    start(c, 0, "ULTIMATE");
    run(c, 160);
    expect(c.actors[1].hp).toBe(868);
    expect(c.actors[1].qi).toBe(660);
    expect(c.hits).toHaveLength(3);
  });
  it("zero qi first hit still blocks, subsequent hit does not", () => {
    const c = new GameCore("PRACTICE");
    const a = c.actors[1];
    a.qi = 60;
    a.input.needsNone = false;
    a.input.label = "BLOCK";
    a.input.lastTick = 1000;
    const cast: any = {
      id: 1,
      skill: "fireball",
      owner: 0,
      start: 0,
      generate: 0,
      x: 480,
      target: a.x,
      dir: 1,
      phaseDir: 1,
    };
    c.add(cast, 0, a.x, 844, BY_ID.fireball.shape!, 0, 2);
    c.add({ ...cast, id: 2 }, 0, a.x, 844, BY_ID.fireball.shape!, 0, 2);
    c.step();
    expect(a.hp).toBe(880);
    expect(a.imbalance).toBe(180);
    expect(c.hits.map((h) => h.blocked)).toEqual([true, false]);
  });
  it("resolve cap, then shield, decimal hp and no stacking with block", () => {
    const c = new GameCore("PRACTICE");
    const a = c.actors[1];
    a.resolve = 360;
    a.budget = 40;
    a.shield = 15;
    a.shieldEnd = 100;
    const cast: any = {
      id: 1,
      skill: "ice",
      owner: 0,
      start: 0,
      generate: 0,
      x: 480,
      target: a.x,
      dir: 1,
      phaseDir: 1,
    };
    c.add(cast, 0, a.x, 844, BY_ID.ice.shape!, 0, 2);
    c.step();
    expect(a.hp).toBe(975);
    expect(a.shield).toBe(0);
    expect(a.budget).toBe(0);
    expect(a.resolve).toBe(0);
    expect(c.hits[0]).toMatchObject({
      raw: 80,
      reduced: 40,
      absorbed: 15,
      health: 25,
    });
  });
  it("mirror conserves lifetime and travel, cannot re-reflect", () => {
    const c = new GameCore("PRACTICE");
    c.actors[1].x = 700;
    c.actors[1].mirror = 100;
    start(c, 0, "ATTACK_SKILL");
    run(c, 30);
    const o = c.objects[0];
    expect(o.reflected).toBe(true);
    expect(o.owner).toBe(1);
    expect(o.vx).toBe(-800);
    expect(o.end - o.start).toBe(84);
    expect(o.travel).toBeGreaterThan(0);
    c.actors[0].mirror = 100;
    run(c, 40);
    expect(c.actors[0].hp).toBe(900);
  });
  it("ground-only attack ignores airborne overlapping box", () => {
    const c = new GameCore("PRACTICE");
    const a = c.actors[1];
    a.ground = false;
    a.y = 890;
    a.vy = -100;
    const cast: any = {
      id: 1,
      skill: "bind",
      owner: 0,
      start: 0,
      generate: 0,
      x: 480,
      target: a.x,
      dir: 1,
      phaseDir: 1,
    };
    c.add(cast, 0, a.x, 850, BY_ID.bind.shape!, 0, 6);
    c.step();
    expect(a.hp).toBe(1000);
  });
  it("simultaneous lethals resolve together", () => {
    const c = new GameCore();
    for (const a of c.actors) a.hp = 70;
    for (let i = 0; i < 2; i++) {
      const cast: any = {
        id: i + 1,
        skill: "normal",
        owner: i,
        start: 0,
        generate: 0,
        x: c.actors[i].x,
        target: c.actors[1 - i].x,
        dir: i ? -1 : 1,
        phaseDir: 1,
      };
      c.add(cast, 0, c.actors[1 - i].x, 840, BY_ID.normal.shape!, 0, 6);
    }
    c.step();
    expect(c.actors.map((a) => a.hp)).toEqual([0, 0]);
    expect(c.result?.winner).toBeNull();
  });
  it("PVE final tick defeat takes priority; mutual death is death", () => {
    for (const both of [false, true]) {
      const c = new GameCore("PVE");
      c.tick = 5399;
      c.actors[1].hp = 70;
      if (both) c.actors[0].hp = 70;
      for (let i = 0; i < (both ? 2 : 1); i++) {
        const cast: any = {
          id: i + 1,
          skill: "normal",
          owner: i,
          start: 5399,
          generate: 5399,
          x: c.actors[i].x,
          target: c.actors[1 - i].x,
          dir: 1,
          phaseDir: 1,
        };
        c.add(cast, 0, c.actors[1 - i].x, 840, BY_ID.normal.shape!, 5399, 5400);
      }
      c.step();
      expect(c.result?.reason).toBe(both ? "death" : "defeat");
    }
  });
  it("PVP overtime extends only once and retains state", () => {
    const c = new GameCore();
    c.tick = 5399;
    c.step();
    expect(c.overtime).toBe(true);
    expect(c.deadline).toBe(6300);
    c.tick = 6299;
    c.step();
    expect(c.result?.reason).toBe("draw");
  });
  it("all practice aids isolated from PVP/PVE", () => {
    for (const mode of ["PVP", "PVE"] as const) {
      const c = new GameCore(mode, undefined, {
        infiniteQi: true,
        noCooldown: true,
        unlock: true,
        immortal: true,
      });
      expect(Object.values(c.aids).some(Boolean)).toBe(false);
    }
  });
  it("phase legal sides at walls, no invulnerability", () => {
    const c = new GameCore("PRACTICE");
    c.actors[0].x = 1680;
    c.actors[1].x = 1750;
    c.actors[0].loadout.defense = "phase";
    c.actors[0].recentDir = 1;
    c.actors[0].recentTick = 0;
    start(c, 0, "DEFENSE_SKILL");
    run(c, 13);
    expect(c.actors[0].x).toBe(1686);
  });
  it("shield replacement retains higher value own expiration", () => {
    const c = new GameCore();
    const a = c.actors[0];
    c.shield(a, 120, 100);
    c.shield(a, 120, 200);
    expect(a.shieldEnd).toBe(100);
    c.shield(a, 600, 300);
    expect(a.shieldEnd).toBe(300);
  });
  it("fixed AI ordering, difficulty and deterministic replay", () => {
    expect(aiLoadout(1)).toEqual({
      attack: "fireball",
      defense: "wall",
      control: "pull",
      ultimate: "beam",
    });
    expect(difficulty(10)).toEqual({ delay: 12, chance: 0.8 });
    const results = [];
    for (let j = 0; j < 2; j++) {
      const c = new GameCore("PVE", [DEFAULT_LOADOUT, aiLoadout(1)]),
        ai = new AIController(12345, 1);
      for (let n = 0; n < 1800; n++) {
        ai.step(c);
        c.step();
      }
      results.push(JSON.stringify(c.publicState(null)));
    }
    expect(results[0]).toBe(results[1]);
  });
  it("AI decisions ignore a player's unrevealed ultimate and honor all difficulty ranges", () => {
    for (const [round, delay, chance] of [[1,36,.35],[3,36,.35],[4,27,.5],[6,27,.5],[7,18,.65],[9,18,.65],[10,12,.8],[20,12,.8]])
      expect(difficulty(round)).toEqual({ delay, chance });
    const replay = (ultimate: string) => {
      const c = new GameCore("PVE", [{ ...DEFAULT_LOADOUT, ultimate }, aiLoadout(4)]);
      c.actors[0].revealed = false;
      const ai = new AIController(7543, 4), labels: string[] = [];
      for (let n = 0; n < 1200; n++) {
        c.input(0, "NONE"); ai.step(c); c.step(); labels.push(ai.label);
        for (const h of ai.history) expect(h.state.actors[0].loadout.ultimate).toBeNull();
      }
      return labels;
    };
    expect(replay("meteor")).toEqual(replay("silence"));
  });
});
