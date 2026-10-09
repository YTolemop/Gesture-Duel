import { it, expect } from "vitest";
import { GameCore } from "../packages/game-core/core.js";
import { BY_ID } from "../packages/game-core/skills.js";
const expected: Record<string, number> = {
  normal: 70,
  fireball: 100,
  spear: 240,
  flame: 220,
  stars: 200,
  bomb: 360,
  ice: 80,
  bind: 180,
  repulse: 80,
  pull: 190,
  beam: 600,
  meteor: 660,
  nova: 600,
  gravity: 480,
  frost: 510,
  storm: 540,
};
for (const [id, total] of Object.entries(expected))
  it(`${id}: actual complete cast deals independently specified total ${total}`, () => {
    const c = new GameCore("PRACTICE");
    c.actors[1].x = 600;
    c.elapsed[0] = 1200;
    const s = BY_ID[id];
    if (s.slot !== "normal") c.actors[0].loadout[s.slot] = id;
    const label: any =
      s.slot === "normal"
        ? "NORMAL_ATTACK"
        : (
            {
              attack: "ATTACK_SKILL",
              defense: "DEFENSE_SKILL",
              control: "CONTROL_SKILL",
              ultimate: "ULTIMATE",
            } as any
          )[s.slot];
    expect(c.attempt(0, label)).toBe("OK");
    for (let n = 0; n < 200; n++) c.step();
    expect(1000 - c.actors[1].hp).toBe(total);
    expect(c.hits.reduce((n, h) => n + h.raw, 0)).toBe(total);
  });
it("432 independent damage oracle combinations: block/resolve cap/shield order", () => {
  let count = 0;
  for (const id of [
    "normal",
    "ice",
    "fireball",
    "pull",
    "spear",
    "bomb",
    "frost",
    "storm",
    "beam",
  ])
    for (const budget of [0, 40, 540])
      for (const shield of [0, 15, 120, 600])
        for (const blocked of [false, true])
          for (const qi of [60, 720]) {
            const c = new GameCore("PRACTICE"),
              a = c.actors[1],
              raw = expected[id];
            a.shield = shield;
            a.shieldEnd = 100;
            a.budget = budget;
            a.resolve = 100;
            a.qi = qi;
            a.input.label = blocked ? "BLOCK" : "NONE";
            a.input.needsNone = false;
            const cast: any = {
              id: 1,
              owner: 0,
              skill: id,
              start: 0,
              generate: 0,
              x: 480,
              target: 1440,
              dir: 1,
            };
            c.add(cast, 0, a.x, 844, BY_ID[id].shape!, 0, 2);
            c.damage(c.objects[0], 1);
            const reduction = blocked ? raw * 0.8 : Math.min(raw * 0.6, budget);
            const received = raw - reduction,
              absorbed = Math.min(shield, received);
            expect(a.hp).toBeCloseTo(1000 - (received - absorbed));
            expect(a.shield).toBeCloseTo(shield - absorbed);
            expect(a.budget).toBeCloseTo(
              blocked ? budget : Math.max(0, budget - reduction),
            );
            count++;
          }
  expect(count).toBe(432);
});
it("reflection uses full step travel and hits adjacent original caster in same step", () => {
  const c = new GameCore("PRACTICE");
  c.actors[1].x = 544;
  c.actors[1].mirror = 100;
  const cast: any = {
    id: 1,
    owner: 0,
    skill: "fireball",
    start: 0,
    generate: 0,
    x: 480,
    target: 544,
    dir: 1,
  };
  c.add(cast, 0, 544, 844, BY_ID.fireball.shape!, 0, 84, { vx: 800 });
  c.step();
  expect(c.actors[0].hp).toBe(900);
  expect(c.actors[1].hp).toBe(1000);
});
it("projectile crossing floor before target cannot hit behind ground contact", () => {
  const c = new GameCore("PRACTICE");
  c.actors[1].x = 700;
  const cast: any = {
    id: 1,
    owner: 0,
    skill: "stars",
    start: 0,
    generate: 0,
    x: 480,
    target: 700,
    dir: 1,
  };
  c.add(cast, 0, 600, 880, BY_ID.stars.shape!, 0, 48, { vx: 6000, vy: 6000 });
  c.step();
  expect(c.actors[1].hp).toBe(1000);
  expect(c.objects).toHaveLength(0);
});
