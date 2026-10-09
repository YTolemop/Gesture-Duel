import { it, expect, afterEach } from "vitest";
import { RoomManager } from "../apps/server/rooms.js";
import {
  LeaderboardRepository,
  RunResult,
} from "../apps/server/leaderboard.js";
import { DEFAULT_LOADOUT } from "../packages/game-core/skills.js";
import { EventEmitter } from "node:events";
class FakeSocket extends EventEmitter {
  id = Math.random().toString();
  data: any = {};
  handshake = { address: "127.0.0.1" };
  volatile = this;
  connected = true;
  disconnect() {
    this.connected = false;
    this.emit("disconnect");
  }
}
const repos: LeaderboardRepository[] = [];
afterEach(() => {
  for (const r of repos.splice(0)) r.close();
});
const setup = () => {
  const repo = new LeaderboardRepository(":memory:");
  repos.push(repo);
  const m = new RoomManager({} as any, repo, true);
  let now = 100000;
  m.now = () => now;
  return {
    m,
    advance: (ms: number) => {
      now += ms;
    },
    socket: () => new FakeSocket() as any,
  };
};
const call = (s: any, event: string, v: any = {}) => {
  let ack: any;
  s.emit(
    event,
    { requestId: Math.random().toString(), ...v },
    (a: any) => (ack = a),
  );
  return ack;
};
it("solo selection requires readiness, locks each slot, preserves aids and starts only after four picks", () => {
  for (const mode of ["PRACTICE","PVE"]) {
    const {m,socket}=setup(), s=socket();m.attachArena(s);
    const a=call(s,"solo:create",{nickname:"單人",mode}), r=m.room(a.roomCode);
    expect(call(s,"solo:select").errorCode).toBe("PLAYERS_NOT_READY");
    call(s,"player:source",{source:"keyboard"});call(s,"player:ready",{ready:true});
    if(mode==="PRACTICE")call(s,"solo:configure",{loadout:DEFAULT_LOADOUT,aids:{infiniteQi:true},dummyX:700});
    expect(call(s,"solo:select").ok).toBe(true);expect(r.core).toBeNull();
    expect(call(s,"solo:pick",{skillId:"beam"}).ok).toBe(true);
    expect(call(s,"solo:pick",{skillId:"meteor"}).errorCode).toBe("SLOT_FILLED");
    for(const skillId of ["spear","shield"])call(s,"solo:pick",{skillId});
    expect(r.phase).toBe("SOLO_DRAFT");expect(r.run).toBeNull();
    call(s,"solo:pick",{skillId:"bind"});expect(r.phase).toBe("COUNTDOWN");expect(r.core).not.toBeNull();
    if(mode==="PRACTICE") {expect(r.config.aids.infiniteQi).toBe(true);expect(r.config.dummyX).toBe(700);}
    else {expect(r.run?.sourceHistory).toEqual(["keyboard"]);expect(call(s,"solo:select").ok).toBe(false);}
  }
});
it("solo timed picks restore after refresh and a lost player cancels selection", () => {
  const {m,socket,advance}=setup(), s=socket();m.attachArena(s);
  const a=call(s,"solo:create",{nickname:"玩家",mode:"PRACTICE"}),r=m.room(a.roomCode);
  call(s,"player:source",{source:"keyboard"});call(s,"player:ready",{ready:true});call(s,"solo:select");
  advance(29999);m.tick();expect(r.draftIndex).toBe(0);
  advance(1);m.tick();expect(r.draftIndex).toBe(1);
  const resumed=socket();m.attachArena(resumed);expect(call(resumed,"room:resume",{roomCode:a.roomCode,playerToken:a.playerToken}).ok).toBe(true);
  expect(r.draftIndex).toBe(1);expect(r.players[0]?.loadout.ultimate).toBeTruthy();
  for(let i=0;i<3;i++){advance(30000);m.tick();}expect(r.phase).toBe("COUNTDOWN");
  call(resumed,"match:pause",{hostToken:a.hostToken});call(resumed,"solo:select");resumed.disconnect();advance(5000);m.tick();expect(r.phase).toBe("CONFIG");expect(r.players[0]?.ready).toBe(false);
});
it("configured room capacity is enforced and invalid settings cannot remove the limit", () => {
  const repo = new LeaderboardRepository(":memory:"); repos.push(repo);
  for (const value of [NaN, Infinity, 0, -1, 1.5])
    expect(() => new RoomManager({} as any, repo, false, value)).toThrow("MAX_ROOMS");
  const m = new RoomManager({} as any, repo, false, 2);
  const sockets = [new FakeSocket(), new FakeSocket(), new FakeSocket()];
  for (const s of sockets) m.attachArena(s as any);
  expect(call(sockets[0], "room:create", { nickname: "一" }).ok).toBe(true);
  expect(call(sockets[1], "solo:create", { nickname: "二", mode: "PRACTICE" }).ok).toBe(true);
  expect(call(sockets[2], "room:create", { nickname: "三" }).errorCode).toBe("ROOM_CAPACITY");
});
it("independent solo sessions and room-free controller pairing never cross-route players",()=>{
  const {m,socket}=setup(), a=socket(),b=socket();m.attachArena(a);m.attachArena(b);
  const first=call(a,"solo:create",{nickname:"一",mode:"PRACTICE"}), second=call(b,"solo:create",{nickname:"二",mode:"PVE"});
  expect(first.roomCode).not.toBe(second.roomCode);expect(first.roomId).not.toBe(second.roomId);
  const codes=[call(a,"controller:code"),call(b,"controller:code")];expect(codes[0].pairCode).not.toBe(codes[1].pairCode);
  const controllers=[socket(),socket()];controllers.forEach(c=>m.attachController(c));
  for(let i=0;i<2;i++){
    const result=call(controllers[i],"controller:pair",{protocolVersion:1,pairCode:codes[i].pairCode,source:"simulated"});
    expect(result.roomCode).toBe([first,second][i].roomCode);expect(result.playerId).toBe([first,second][i].playerId);
  }
  call(a,"player:ready",{ready:true});call(a,"solo:configure",{loadout:DEFAULT_LOADOUT,dummyX:700,aids:{infiniteQi:true}});call(a,"practice:start");
  expect(m.room(first.roomCode).phase).toBe("COUNTDOWN");expect(m.room(second.roomCode).phase).toBe("CONFIG");expect(m.room(second.roomCode).run).toBeNull();
  const invalid=socket();m.attachController(invalid);
  expect(call(invalid,"controller:pair",{protocolVersion:1,pairCode:codes[0].pairCode,source:"simulated"}).errorCode).toBe("INVALID_PAIR_CODE");
});
it("authority, draft secrecy, source exclusivity and old match/seq rejection", () => {
  const { m, socket } = setup();
  const red = socket(),
    blue = socket(),
    watch = socket();
  m.attachArena(red);
  m.attachArena(blue);
  m.attachArena(watch);
  const a = call(red, "room:create", { nickname: "紅" }),
    b = call(blue, "room:join", { roomCode: a.roomCode, nickname: "藍" });
  call(watch, "room:join", { roomCode: a.roomCode, role: "spectator" });
  expect(call(watch, "match:pause", { roomCode: a.roomCode }).errorCode).toBe(
    "HOST_REQUIRED",
  );
  call(red, "draft:start", { hostToken: a.hostToken });
  const r = m.room(a.roomCode);
  for (let n = 0; n < 8; n++) {
    const sock = r.draftOrder[n] === 0 ? red : blue;
    const picked =
      n < 2
        ? "beam"
        : n === 2
          ? "fireball"
          : n === 3
            ? "spear"
            : n === 4
              ? "shield"
              : n === 5
                ? "mirror"
                : n === 6
                  ? "ice"
                  : "bind";
    expect(call(sock, "draft:pick", { skillId: picked }).ok).toBe(true);
  }
  expect(JSON.stringify(m.state(r, null))).not.toContain("beam");
  expect(m.state(r, 0).players[0]?.loadout.ultimate).toBe("beam");
  for (const s of [red, blue]) {
    call(s, "player:source", { source: "keyboard" });
    call(s, "player:ready", { ready: true });
  }
  expect(call(red, "match:start", { hostToken: a.hostToken }).ok).toBe(true);
  const p = r.players[0]!;
  let ack: any;
  red.emit(
    "input:state",
    {
      protocolVersion: 1,
      sessionId: p.session,
      generation: p.generation,
      matchId: "old",
      seq: 0,
      gesture: "NONE",
    },
    (v: any) => (ack = v),
  );
  expect(ack.errorCode).toBe("STALE_MATCH");
  const input = {
    protocolVersion: 1,
    sessionId: p.session,
    generation: p.generation,
    matchId: r.matchId,
    seq: 0,
    gesture: "NONE",
  };
  red.emit("input:state", input, (v: any) => (ack = v));
  expect(ack.ok).toBe(true);
  red.emit("input:state", input, (v: any) => (ack = v));
  expect(ack.errorCode).toBe("STALE_SEQ");
});
it("one spectator and one-time pairing, bad roles cannot take seats", () => {
  const { m, socket } = setup();
  const a = socket(),
    b = socket(),
    c = socket();
  for (const s of [a, b, c]) m.attachArena(s);
  const auth = call(a, "solo:create", { nickname: "玩家", mode: "PRACTICE" });
  expect(
    call(b, "room:join", { roomCode: auth.roomCode, role: "spectator" }).ok,
  ).toBe(true);
  expect(
    call(c, "room:join", { roomCode: auth.roomCode, role: "spectator" })
      .errorCode,
  ).toBe("SPECTATOR_FULL");
  const pair = call(a, "controller:code"),
    ctrl = socket(),
    other = socket();
  m.attachController(ctrl);
  m.attachController(other);
  const v = {
    protocolVersion: 1,
    roomCode: auth.roomCode,
    pairCode: pair.pairCode,
    source: "simulated",
  };
  expect(call(ctrl, "controller:pair", v).ok).toBe(true);
  expect(call(other, "controller:pair", v).errorCode).toBe("INVALID_PAIR_CODE");
});
it("PVE reward exactly once, capped, cooldown retained and time frozen", () => {
  const { m, socket, advance } = setup();
  const s = socket();
  m.attachArena(s);
  const a = call(s, "solo:create", { nickname: "玩家", mode: "PVE" });
  call(s, "player:source", { source: "keyboard" });
  call(s, "player:ready", { ready: true });
  call(s, "pve:start");
  const r = m.room(a.roomCode);
  r.core!.actors[0].hp = 500;
  r.core!.actors[0].qi = 120;
  r.core!.actors[0].imbalance = 999;
  r.core!.actors[0].cooldowns.fireball = 180;
  r.core!.tick = 60;
  r.core!.elapsed[0] = 60;
  r.core!.actors[1].hp = 0;
  r.core!.result = { winner: 0, reason: "defeat" };
  const oldMatch = r.matchId;
  m.advanceRound(r);
  m.advanceRound(r);
  expect(r.core!.actors[0].hp).toBe(750);
  expect(r.core!.actors[0].qi).toBe(480);
  expect(r.core!.actors[0].imbalance).toBe(0);
  expect(r.core!.actors[0].cooldowns.fireball).toBe(120);
  expect(r.matchId).not.toBe(oldMatch);
  m.tick();
  expect(r.core!.tick).toBe(0);
  expect(r.core!.actors[0].qi).toBe(480);
  m.finishRun(r, "quit");
  m.finishRun(r, "death");
  expect(r.run!.result?.reason).toBe("quit");
  expect(m.repo.all()).toHaveLength(1);
  expect(m.repo.all()[0].eligible).toBe(false);
});
it("leaderboard unique, sorting, version grouping and conflict rejection", () => {
  const repo = new LeaderboardRepository(":memory:");
  repos.push(repo);
  const result: RunResult = {
    runId: "b",
    playerId: "x",
    nickname: "<img src=x>",
    defeated: 1,
    reason: "death",
    ticks: 600,
    hp: 0,
    rulesVersion: "v",
    aiVersion: "a",
    sourceHistory: ["recognizer"],
    eligible: true,
    internal: false,
    completedAt: "2026-10-09T00:00:00Z",
    seed: 1,
  };
  repo.save(result);
  repo.save(result);
  repo.save({ ...result, runId: "a", ticks: 500 });
  repo.save({ ...result, runId: "other", rulesVersion: "v2", defeated: 99 });
  expect(repo.list("v", "a").map((r) => r.runId)).toEqual(["a", "b"]);
  expect(() => repo.save({ ...result, defeated: 99 })).toThrow(
    "RESULT_CONFLICT",
  );
});

it("vacating blue revokes credentials; a red player leaving preserves other members", () => {
  const { m, socket } = setup();
  const red = socket(), blue = socket(), watch = socket();
  for (const s of [red, blue, watch]) m.attachArena(s);
  const a = call(red, "room:create", { nickname: "紅" });
  const b = call(blue, "room:join", { roomCode: a.roomCode, nickname: "藍" });
  call(watch, "room:join", { roomCode: a.roomCode, role: "spectator" });
  expect(call(watch, "room:assign", { seat: "blue", action: "vacate" }).errorCode).toBe("HOST_REQUIRED");
  expect(call(red, "room:assign", { hostToken: a.hostToken, seat: "blue", action: "vacate" }).ok).toBe(true);
  const restored = socket(); m.attachArena(restored);
  expect(call(restored, "room:resume", { roomCode: a.roomCode, playerToken: b.playerToken }).errorCode).toBe("INVALID_TOKEN");
  expect(call(restored, "room:join", { roomCode: a.roomCode, nickname: "新藍" }).ok).toBe(true);
  expect(call(red, "room:leave").ok).toBe(true);
  expect(m.rooms.has(a.roomCode)).toBe(true);
  expect(m.room(a.roomCode).players[0]).toBeNull();
  expect(watch.connected).toBe(true);
});

it("an empty unstarted solo room terminates at 30s then recycles at 10min", () => {
  const { m, socket, advance } = setup();
  const s = socket(); m.attachArena(s);
  const a = call(s, "solo:create", { nickname: "玩家", mode: "PRACTICE" });
  s.disconnect(); advance(29999); m.tick();
  expect(m.room(a.roomCode).phase).toBe("CONFIG");
  advance(1); m.tick(); expect(m.room(a.roomCode).phase).toBe("RESULT");
  advance(600001); m.tick(); expect(m.rooms.has(a.roomCode)).toBe(false);
});

it("source generation invalidates old inputs and an unselected controller disconnect does not pause", () => {
  const { m, socket, advance } = setup();
  const s = socket(); m.attachArena(s);
  const a = call(s, "solo:create", { nickname: "玩家", mode: "PRACTICE" });
  const pair = call(s, "controller:code");
  const controller = socket(); m.attachController(controller);
  expect(call(controller, "controller:pair", { protocolVersion: 1, roomCode: a.roomCode, pairCode: pair.pairCode, source: "simulated" }).ok).toBe(true);
  const r = m.room(a.roomCode), oldGeneration = r.players[0]!.generation;
  call(s, "player:source", { source: "keyboard" });
  let ack: any;
  s.emit("input:state", { protocolVersion: 1, sessionId: r.players[0]!.session, matchId: r.matchId, generation: oldGeneration, seq: 0, gesture: "NORMAL_ATTACK" }, (v: any) => ack = v);
  expect(ack.errorCode).toBe("STALE_GENERATION");
  call(s, "player:ready", { ready: true }); call(s, "practice:start");
  advance(3001); s.emit("client:heartbeat"); m.tick();
  expect(r.phase).toBe("PLAYING");
  controller.disconnect(); expect(r.phase).toBe("PLAYING");
});

it("three-person lobby swaps all roles atomically and revokes old sessions", () => {
  const {m,socket}=setup();const red=socket(),blue=socket(),watch=socket(),fourth=socket();
  for(const s of [red,blue,watch,fourth])m.attachArena(s);
  const a=call(red,"room:create",{nickname:"A"});
  call(blue,"room:join",{roomCode:a.roomCode,nickname:"B"});
  const c=call(watch,"room:join",{roomCode:a.roomCode,nickname:"C"});expect(c.seat).toBe("spectator");
  expect(call(fourth,"room:join",{roomCode:a.roomCode,nickname:"D"}).errorCode).toBe("SPECTATOR_FULL");
  const r=m.room(a.roomCode),oldSession=r.players[0]!.session;
  expect(call(watch,"room:seat",{seat:"red"}).seat).toBe("red");
  expect(r.players[0]!.nickname).toBe("C");expect(r.spectator!.nickname).toBe("A");
  expect(call(red,"room:seat",{seat:"blue"}).seat).toBe("blue");
  expect(r.players[1]!.nickname).toBe("A");expect(r.spectator!.nickname).toBe("B");
  expect(r.players[1]!.session).not.toBe(oldSession);
  expect(new Set([...r.players,r.spectator].map(p=>p!.id)).size).toBe(3);
  expect(r.players.every(p=>!p!.ready)).toBe(true);
});

it("two players need no observer: five-second ready countdown, red first, 30-second automatic legal picks", () => {
  const {m,socket,advance}=setup();const a=socket(),b=socket();m.attachArena(a);m.attachArena(b);
  const auth=call(a,"room:create",{nickname:"紅"});call(b,"room:join",{roomCode:auth.roomCode,nickname:"藍"});
  for(const s of [a,b])call(s,"player:source",{source:"keyboard"});
  call(a,"player:ready",{ready:true});const r=m.room(auth.roomCode);expect(r.phase).toBe("LOBBY");
  call(b,"player:ready",{ready:true});expect(r.phase).toBe("DRAFT_COUNTDOWN");
  advance(4999);m.tick();expect(r.phase).toBe("DRAFT_COUNTDOWN");advance(1);m.tick();expect(r.phase).toBe("DRAFT");
  expect(r.draftOrder).toEqual([0,1,1,0,0,1,1,0]);expect(r.spectator).toBeNull();
  for(let n=0;n<8;n++){advance(30000);m.tick();expect(r.draftIndex).toBe(n+1);}
  expect(r.phase).toBe("COUNTDOWN");expect(r.core).not.toBeNull();
  const ordinary=r.players.flatMap(p=>[p!.loadout.attack,p!.loadout.defense,p!.loadout.control]);
  expect(new Set(ordinary).size).toBe(6);
  advance(5000);m.tick();expect(r.phase).toBe("PLAYING");
  b.disconnect();expect(r.phase).toBe("PAUSED");expect(r.core!.actors[1].input.label).toBe("NONE");
});

it("changing readiness or seats during the five-second lobby countdown cancels it",()=>{
  const {m,socket}=setup();const a=socket(),b=socket();m.attachArena(a);m.attachArena(b);
  const auth=call(a,"room:create",{nickname:"A"});call(b,"room:join",{roomCode:auth.roomCode,nickname:"B"});
  for(const s of [a,b]){call(s,"player:source",{source:"keyboard"});call(s,"player:ready",{ready:true});}
  const r=m.room(auth.roomCode);expect(r.phase).toBe("DRAFT_COUNTDOWN");
  call(a,"player:ready",{ready:false});m.tick();expect(r.phase).toBe("LOBBY");
  call(a,"player:ready",{ready:true});expect(r.phase).toBe("DRAFT_COUNTDOWN");
  call(b,"room:seat",{seat:"red"});expect(r.phase).toBe("LOBBY");expect(r.players.every(p=>!p!.ready)).toBe(true);
});
