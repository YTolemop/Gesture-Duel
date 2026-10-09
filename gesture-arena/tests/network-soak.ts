import { io, Socket } from "socket.io-client";
import { mkdirSync, writeFileSync } from "node:fs";
import os from "node:os";
const url = process.argv[2] ?? "http://127.0.0.1:3101",
  minutes = Number(process.argv[3] ?? 30);
let bytes = 0,
  errors: any[] = [];
const recovery = process.argv.includes("--recovery");
let intentionalReconnects = 0;
const clients: {
  socket: Socket;
  auth: any;
  state: any;
  seq: number;
  name: string;
  reconnecting?: boolean;
}[] = [];
async function connect() {
  const s = io(url + "/arena", {
    transports: ["websocket"],
    reconnection: false,
  });
  await new Promise<void>((resolve, reject) => {
    s.once("connect", () => resolve());
    s.once("connect_error", reject);
  });
  return s;
}
async function call(socket: Socket, event: string, v: any = {}) {
  const ack: any = await socket
    .timeout(5000)
    .emitWithAck(event, { ...v, requestId: crypto.randomUUID() });
  if (!ack.ok) throw new Error(JSON.stringify(ack));
  return ack;
}
async function add(mode: string) {
  const socket = await connect(),
    auth = await call(socket, mode === "PVP" ? "room:create" : "solo:create", {
      nickname: mode,
      mode,
    });
  const entry = { socket, auth, state: null as any, seq: 0, name: mode };
  clients.push(entry);
  for (const event of ["room:state", "match:snapshot"]) socket.on(event, (s) => {
    entry.state = s;
    bytes += Buffer.byteLength(JSON.stringify(s));
  });
  await call(socket, "player:source", { source: "keyboard" });
  if (mode === "PVP") {
    const blue = await connect(),
      b = await call(blue, "room:join", {
        roomCode: auth.roomCode,
        nickname: "藍方",
      }),
      other = {
        socket: blue,
        auth: b,
        state: null as any,
        seq: 0,
        name: "blue",
      };
    clients.push(other);
    for (const event of ["room:state", "match:snapshot"]) blue.on(event, (s) => {
      other.state = s;
      bytes += Buffer.byteLength(JSON.stringify(s));
    });
    await call(blue, "player:source", { source: "keyboard" });
    for (const s of [socket, blue]) await call(s, "player:ready", { ready: true });
    for (let i = 0; i < 8; i++) {
      const deadline = Date.now() + 10000;
      while (entry.state?.phase !== "DRAFT" || entry.state?.draftIndex !== i) {
        if (Date.now() > deadline) throw new Error("Draft state timeout at pick " + i);
        await new Promise((r) => setTimeout(r, 10));
      }
      const state = entry.state,
        who = state.draftTurn === 0 ? socket : blue;
      const ids = [
        "beam",
        "beam",
        "fireball",
        "spear",
        "shield",
        "mirror",
        "ice",
        "bind",
      ];
      await call(who, "draft:pick", { skillId: ids[i] });
    }
  } else {
    await call(socket, "player:ready", { ready: true });
    if (mode === "PRACTICE")
      await call(socket, "solo:configure", {
        loadout: {
          attack: "stars",
          defense: "wall",
          control: "pull",
          ultimate: "meteor",
        },
        dummyX: 700,
        aids: {
          infiniteQi: true,
          noCooldown: true,
          unlock: true,
          immortal: true,
        },
      });
    await call(socket, mode === "PRACTICE" ? "practice:start" : "pve:start");
  }
  const spectator = await connect(),
    sp = await call(spectator, "room:join", {
      roomCode: auth.roomCode,
      role: "spectator",
    }),
    watch = {
      socket: spectator,
      auth: sp,
      state: null as any,
      seq: 0,
      name: "observer",
    };
  clients.push(watch);
  for (const event of ["room:state", "match:snapshot"]) spectator.on(event, (s) => {
    watch.state = s;
    bytes += Buffer.byteLength(JSON.stringify(s));
  });
}
await add("PVP");
await add("PRACTICE");
await add("PRACTICE");
await add("PVE");
let start = Date.now(),
  last = 0;
const metrics: any[] = [];
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
const loop = setInterval(() => {
  for (const c of clients) {
    if (c.reconnecting) continue;
    if (!c.socket.connected) {
      errors.push({ client: c.name, error: "DISCONNECTED" });
      continue;
    }
    c.socket.emit("client:heartbeat");
    if (c.auth.seat === "spectator" || !c.state) continue;
    const state = c.state,
      p = state.players[c.auth.seat === "red" ? 0 : 1];
    const index = Math.floor((Date.now() - start) / 200) % gestures.length;
    c.socket.volatile.emit("input:state", {
      protocolVersion: 1,
      sessionId: c.auth.sessionId,
      matchId: state.matchId,
      generation: p.generation,
      seq: c.seq++,
      gesture: gestures[index],
    });
    if (state.phase === "RESULT" && c.auth.hostToken) {
      c.state = { ...state, phase: "RESTARTING" };
      call(
        c.socket,
        state.mode === "PVP"
          ? "match:rematch"
          : state.mode === "PVE"
            ? "pve:start"
            : "practice:reset",
        { hostToken: c.auth.hostToken },
      ).catch((e) => errors.push(String(e)));
    }
  }
}, 100);
// Optional 8-hour rehearsal includes an actual selected player disconnect/resume.
const recoveryTimer = recovery ? setInterval(async () => {
  const c = clients.find((entry) => entry.name === "PRACTICE");
  if (!c || c.reconnecting || c.state?.phase !== "PLAYING") return;
  c.reconnecting = true;
  try {
    c.socket.disconnect();
    await new Promise((r) => setTimeout(r, 500));
    const socket = await connect();
    const resumed = await call(socket, "room:resume", {
      roomCode: c.auth.roomCode, playerToken: c.auth.playerToken,
    });
    c.socket = socket; c.auth = { ...c.auth, ...resumed }; c.seq = 0;
    for (const event of ["room:state", "match:snapshot"]) socket.on(event, (s) => {
      c.state = s; bytes += Buffer.byteLength(JSON.stringify(s));
    });
    await call(socket, "player:ready", { ready: true });
    await call(socket, "practice:resume", { hostToken: c.auth.hostToken });
    intentionalReconnects++;
  } catch (e) { errors.push(String(e)); }
  finally { c.reconnecting = false; }
}, 300000) : undefined;
const monitor = setInterval(async () => {
  try {
    const h: any = await fetch(url + "/health").then((r) => r.json());
    metrics.push({
      seconds: (Date.now() - start) / 1000,
      ...h.metrics,
      receivedSnapshotBytes: bytes,
      clients: clients.length,
      rooms: h.rooms,
    });
    console.log(JSON.stringify(metrics.at(-1)));
  } catch (e) {
    errors.push(String(e));
  }
}, 60000);
await new Promise((r) => setTimeout(r, minutes * 60000));
clearInterval(loop);
clearInterval(monitor);
if (recoveryTimer) clearInterval(recoveryTimer);
const final: any = await fetch(url + "/health").then((r) => r.json());
for (const c of clients) c.socket.disconnect();
const result = {
  date: new Date().toISOString(),
  durationSeconds: (Date.now() - start) / 1000,
  transport: "real Socket.IO websocket clients to Node HTTP server",
  mix: "1 PVP + 2 practice + 1 PVE, each with observer",
  hardware: { cpu: os.cpus()[0], release: os.release(), memory: os.totalmem() },
  metrics,
  final: final.metrics,
  receivedSnapshotBytes: bytes,
  errors,
  recovery, intentionalReconnects,
  pass: errors.length === 0 && final.metrics.p95StepMs < 16.67,
};
mkdirSync("evidence", { recursive: true });
writeFileSync(
  `evidence/network-soak-${minutes}min.json`,
  JSON.stringify(result, null, 2),
);
console.log(JSON.stringify(result));
if (!result.pass) process.exitCode = 1;
