import { it, expect } from "vitest";
import { GameCore } from "../packages/game-core/core.js";
import { BY_ID, DEFAULT_LOADOUT } from "../packages/game-core/skills.js";
import { shapesOverlap, sweep, box } from "../packages/game-core/geometry.js";
const run = (c: GameCore, n: number) => {
  for (let i = 0; i < n; i++) c.step();
};
const cast = (id: string, owner = 0, start = 0, x = 480) => ({
  id: 1,
  skill: id,
  owner,
  start,
  generate: start,
  x,
  target: 1440,
  dir: owner ? -1 : 1,
  phaseDir: 1,
});
it("swept moving target crossing has earliest correct relative contact", () => {
  expect(
    sweep(
      { kind: "rect", w: 100, h: 20 },
      400,
      784,
      100,
      0,
      box(600, 900),
      -100,
      0,
    ),
  ).toBeCloseTo(0.59);
});
it("circle circle silence respects rounded corners", () => {
  expect(
    shapesOverlap(
      { kind: "circle", r: 360 },
      0,
      0,
      { kind: "circle", r: 28 },
      280,
      280,
    ),
  ).toBe(false);
  expect(
    shapesOverlap(
      { kind: "circle", r: 360 },
      0,
      0,
      { kind: "circle", r: 28 },
      387,
      0,
    ),
  ).toBe(true);
});
it("regen starts exactly after one second and gains120 per2s", () => {
  const c = new GameCore("PRACTICE");
  c.actors[0].qi = 120;
  run(c, 60);
  expect(c.actors[0].qi).toBe(120);
  c.step();
  expect(c.actors[0].qi).toBe(121);
  run(c, 119);
  expect(c.actors[0].qi).toBe(240);
});
it("imbalance cannot skill/block but can normal; expires at180 with1qi", () => {
  const c = new GameCore("PRACTICE");
  c.spend(c.actors[0], 720);
  expect(c.attempt(0, "ATTACK_SKILL")).toBe("IMBALANCE");
  expect(c.attempt(0, "NORMAL_ATTACK")).toBe("OK");
  c.actors[0].input.label = "BLOCK";
  expect(c.blocking(c.actors[0])).toBe(false);
  run(c, 180);
  expect(c.actors[0].qi).toBe(0);
  c.step();
  expect(c.actors[0].qi).toBeGreaterThanOrEqual(120);
  expect(c.actors[0].qi).toBeLessThanOrEqual(121);
});
it("air cannot attack, cast, or block; root blocks jump/phase but not attacks", () => {
  const c = new GameCore("PRACTICE");
  const a = c.actors[0];
  a.ground = false;
  a.input.label = "BLOCK";
  expect(c.attempt(0, "NORMAL_ATTACK")).toBe("ACTION_LOCKED");
  expect(c.blocking(a)).toBe(false);
  a.ground = true;
  a.root = 100;
  a.loadout.defense = "phase";
  expect(c.attempt(0, "JUMP")).toBe("ACTION_LOCKED");
  expect(c.attempt(0, "DEFENSE_SKILL")).toBe("ROOTED");
  expect(c.attempt(0, "NORMAL_ATTACK")).toBe("OK");
});
it("prepare interruption pays cost/cooldown and cancels warning only", () => {
  const c = new GameCore("PRACTICE");
  c.actors[0].loadout.attack = "bomb";
  expect(c.attempt(0, "ATTACK_SKILL")).toBe("OK");
  const a = c.actors[0];
  c.add(cast("fireball", 1), 0, a.x, 844, BY_ID.fireball.shape!, 0, 2);
  c.step();
  expect(a.cast).toBeNull();
  expect(a.qi).toBe(360);
  expect(a.cooldowns.bomb).toBe(360);
  expect(c.objects.some((o) => o.skill === "bomb")).toBe(false);
});
it("generated attack retains independent window through recovery hit", () => {
  const c = new GameCore("PRACTICE");
  const a = c.actors[0];
  a.loadout.attack = "bomb";
  c.attempt(0, "ATTACK_SKILL");
  run(c, 31);
  expect(c.objects.some((o) => o.skill === "bomb")).toBe(true);
  c.add(cast("fireball", 1, 31), 0, a.x, 844, BY_ID.fireball.shape!, 31, 33);
  c.step();
  expect(c.objects.some((o) => o.skill === "bomb")).toBe(true);
});
it("stun cannot refresh during existing stun or0.3s immunity", () => {
  const c = new GameCore("PRACTICE", undefined, { immortal: true });
  const a = c.actors[1];
  for (let t = 0; t < 31; t++) {
    c.add(
      { ...cast("ice"), id: t + 1 },
      0,
      a.x,
      844,
      BY_ID.ice.shape!,
      t,
      t + 1,
    );
    c.step();
    if (t === 0) expect(a.stun).toBe(12);
    if (t === 10 || t === 20) expect(a.stun).toBe(12);
    if (t === 30) expect(a.stun).toBe(42);
  }
});
it("strongest slow wins independently and ground field stops on jump", () => {
  const c = new GameCore("PRACTICE");
  const a = c.actors[1];
  a.slows = [
    { amount: 0.2, end: 100 },
    { amount: 0.4, end: 10 },
  ];
  expect(c.slow(a, 1)).toBe(0.4);
  c.tick = 10;
  c.step();
  expect(c.slow(a, 1)).toBe(0.2);
  c.add(cast("slowfield"), 0, a.x, 888, BY_ID.slowfield.shape!, 11, 190, {
    field: true,
  });
  expect(c.slow(a, 1)).toBe(0.3);
  a.ground = false;
  expect(c.slow(a, 1)).toBe(0.2);
  a.cleanse = 100;
  expect(c.slow(a, 1)).toBe(0);
});
it("root-force mutual exclusion and2s immunity after cleanse", () => {
  const c = new GameCore("PRACTICE");
  const a = c.actors[1];
  a.root = 36;
  c.add(cast("repulse"), 0, a.x, 790, BY_ID.repulse.shape!, 0, 2);
  c.step();
  expect(a.force).toBeNull();
  c.generate({ ...cast("cleanse", 1), generate: 1 });
  expect(a.root).toBe(0);
  expect(a.controlImmune).toBe(121);
});
it("mirror and wind wall never remove flame, area or ultimate", () => {
  const c = new GameCore("PRACTICE");
  const a = c.actors[1];
  a.x = 700;
  a.mirror = 100;
  c.add(cast("wall", 1), 0, 600, 750, BY_ID.wall.shape!, 0, 100, { uses: 3 });
  c.add(cast("flame"), 0, 590, 864, BY_ID.flame.shape!, 0, 90, { vx: 640 });
  run(c, 15);
  expect(a.hp).toBe(780);
  expect(a.mirror).toBe(100);
  expect(c.objects.find((o) => o.skill === "wall")?.uses).toBe(3);
});
it("wind wall earlier than role hit prevents damage, wall behind does not", () => {
  for (const [x, hp] of [
    [650, 1000],
    [760, 900],
  ]) {
    const c = new GameCore("PRACTICE");
    c.actors[1].x = 700;
    c.add(cast("wall", 1), 0, x, 750, BY_ID.wall.shape!, 0, 100, { uses: 3 });
    c.add(cast("fireball"), 0, 600, 844, BY_ID.fireball.shape!, 0, 84, {
      vx: 800,
    });
    run(c, 20);
    expect(c.actors[1].hp).toBe(hp);
  }
});
it("two airborne simultaneous landings preserve side and64px wall spacing", () => {
  const c = new GameCore("PRACTICE");
  for (const a of c.actors) {
    a.ground = false;
    a.y = 899;
    a.vy = 200;
    a.x = 1792;
  }
  c.step();
  expect(c.actors[1].x - c.actors[0].x).toBe(64);
  expect(c.actors[1].x).toBe(1792);
});
it("practice immortal logs actual computed health damage, min1", () => {
  const c = new GameCore("PRACTICE", undefined, { immortal: true });
  c.actors[1].hp = 10;
  c.add(cast("fireball"), 0, 1440, 844, BY_ID.fireball.shape!, 0, 2);
  c.step();
  expect(c.actors[1].hp).toBe(1);
  expect(c.hits[0].health).toBe(100);
  expect(c.result).toBeNull();
});
it("stars damage capped at200 for three initial intersections", () => {
  const c = new GameCore("PRACTICE");
  for (let i = 0; i < 3; i++)
    c.add(cast("stars"), i, 1440, 828, BY_ID.stars.shape!, 0, 48, { vx: 700 });
  c.step();
  expect(c.actors[1].hp).toBe(800);
  expect(c.objects).toHaveLength(0);
});
it("input state cannot expose hidden ultimate cooldown through public snapshot", () => {
  const c = new GameCore();
  c.actors[0].loadout.ultimate = "meteor";
  c.actors[0].cooldowns.meteor = 100;
  expect(JSON.stringify(c.publicState(null))).not.toContain("meteor");
  expect(JSON.stringify(c.publicState(0))).toContain("meteor");
});
