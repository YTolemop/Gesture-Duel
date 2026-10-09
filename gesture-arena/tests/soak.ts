import { RoomManager } from "../apps/server/rooms.js";
import { LeaderboardRepository } from "../apps/server/leaderboard.js";
import { DEFAULT_LOADOUT } from "../packages/game-core/skills.js";
import { performance } from "node:perf_hooks";
import { EventEmitter } from "node:events";
import { writeFileSync, mkdirSync } from "node:fs";
import os from "node:os";
class Client extends EventEmitter {
  data: any = {};
  id = Math.random().toString();
  handshake = { address: "127.0.0.1" };
  volatile = this;
  disconnect() {}
}
const minutes = Number(process.argv[2] ?? 480);
const repo = new LeaderboardRepository(":memory:"),
  manager = new RoomManager({} as any, repo, true);
const clients: any[] = [];
let bytes = 0;
const call = (s: any, e: string, v: any) => {
  let out: any;
  s.emit(
    e,
    { ...v, requestId: Math.random().toString() },
    (ack: any) => (out = ack),
  );
  if (!out?.ok) throw new Error(JSON.stringify(out));
  return out;
};
for (const mode of ["PVP", "PRACTICE", "PRACTICE", "PVE"]) {
  const s = new Client();
  clients.push(s);
  manager.attachArena(s as any);
  for (const event of ["room:state", "match:snapshot"])
    s.on(event, (v) => (bytes += Buffer.byteLength(JSON.stringify(v))));
  const auth = call(s, mode === "PVP" ? "room:create" : "solo:create", {
    nickname: mode,
    mode,
  });
  const r = manager.room(auth.roomCode);
  call(s, "player:source", { source: "keyboard" });
  r.players[0]!.loadout = { ...DEFAULT_LOADOUT };
  r.players[0]!.ready = true;
  if (mode === "PVP") {
    const blue = new Client();
    clients.push(blue);
    manager.attachArena(blue as any);
    call(blue, "room:join", { roomCode: auth.roomCode, nickname: "blue" });
    call(blue, "player:source", { source: "keyboard" });
    r.players[1]!.loadout = {
      attack: "spear",
      defense: "mirror",
      control: "bind",
      ultimate: "meteor",
    };
    r.players[1]!.ready = true;
    r.phase = "READY";
    call(s, "match:start", { hostToken: auth.hostToken });
  } else if (mode === "PVE") call(s, "pve:start", {});
  else {
    r.config.aids = {
      infiniteQi: true,
      noCooldown: true,
      unlock: true,
      immortal: true,
    };
    call(s, "practice:start", {});
  }
  const spectator = new Client();
  clients.push(spectator);
  manager.attachArena(spectator as any);
  for (const event of ["room:state", "match:snapshot"])
    spectator.on(event, (v) => (bytes += Buffer.byteLength(JSON.stringify(v))));
  call(spectator, "room:join", { roomCode: auth.roomCode, role: "spectator" });
}
const times: number[] = [];
let behind = 0,
  steps = 0,
  acc = 0,
  last = performance.now(),
  start = last,
  lastLog = last;
const history: any[] = [];
mkdirSync("evidence", { recursive: true });
const timer = setInterval(() => {
  const now = performance.now();
  acc += now - last;
  last = now;
  for (const s of clients) s.emit("client:heartbeat");
  let count = 0;
  while (acc >= 1000 / 60 && count < 10) {
    const begin = performance.now();
    for (const r of manager.rooms.values()) {
      if (r.phase === "RESULT") {
        if (r.mode === "PVE") {
          r.run = null;
          call(r.players[0]!.socket, "pve:start", {});
        } else {
          manager.newCore(r);
          r.phase = "PLAYING";
        }
      }
      if (r.core?.tick && r.core.tick % 6 === 0) {
        for (let i = 0; i < 2; i++)
          if (r.players[i]) {
            const p = r.players[i]!;
            const gestures = [
              "NONE",
              "MOVE_RIGHT",
              "NONE",
              "ATTACK_SKILL",
              "NONE",
              "DEFENSE_SKILL",
              "NONE",
              "CONTROL_SKILL",
              "NONE",
              "ULTIMATE",
              "NONE",
              "MOVE_LEFT",
            ];
            const input = {
              protocolVersion: 1,
              sessionId: p.session,
              matchId: r.matchId,
              generation: p.generation,
              seq: ++p.seq,
              gesture: gestures[Math.floor(r.core.tick / 6) % gestures.length],
            };
            p.seq--;
            p.socket!.emit("input:state", input);
          }
      }
    }
    manager.tick();
    times.push(performance.now() - begin);
    acc -= 1000 / 60;
    count++;
    steps++;
  }
  if (acc >= 1000 / 60) behind++;
  if (now - lastLog >= 60000) {
    history.push({
      seconds: (now - start) / 1000,
      rss: process.memoryUsage().rss,
      rooms: manager.rooms.size,
      bytes,
      behind,
      steps,
    });
    console.log(JSON.stringify(history.at(-1)));
    lastLog = now;
  }
  if (now - start >= minutes * 60000) {
    clearInterval(timer);
    times.sort((a, b) => a - b);
    const result = {
      date: new Date().toISOString(),
      durationSeconds: (now - start) / 1000,
      hardware: {
        platform: os.platform(),
        release: os.release(),
        cpus: os.cpus()[0],
        memory: os.totalmem(),
      },
      p95StepMs: times[Math.floor(times.length * 0.95)],
      behind,
      steps,
      bytes,
      rss: process.memoryUsage().rss,
      history,
      roomMix: "1PVP+2PRACTICE+1PVE, 4 observers",
      transport: "in-process sockets; full manager/core/payload construction",
      pass: times[Math.floor(times.length * 0.95)] < 16.67,
    };
    writeFileSync(
      `evidence/soak-${minutes}min.json`,
      JSON.stringify(result, null, 2),
    );
    console.log(JSON.stringify(result));
    repo.close();
  }
}, 4);
