/** Server-owned deterministic test fixture. No fixture routes exist in product. */
import { createServer } from "node:http";
import { Server } from "socket.io";
import { RoomManager } from "../apps/server/rooms.js";
import { LeaderboardRepository } from "../apps/server/leaderboard.js";
import { spawn } from "node:child_process";
import { resolve } from "node:path";
const http = createServer(),
  io = new Server(http),
  repo = new LeaderboardRepository(":memory:"),
  manager = new RoomManager(io, repo, true);
io.of("/arena").on("connection", (s) => manager.attachArena(s));
io.of("/controller").on("connection", (s) => manager.attachController(s));
let prepared = false;
const timer = setInterval(() => {
  for (const r of manager.rooms.values())
    if (
      r.mode === "PVE" &&
      r.phase === "PLAYING" &&
      r.core!.tick >= 6 &&
      !prepared
    ) {
      prepared = true;
      r.core!.actors[0].hp = 400;
      r.core!.actors[0].qi = 180;
      r.core!.actors[0].imbalance = r.core!.tick + 180;
      r.core!.actors[1].hp = 70;
      r.core!.actors[1].x = 600;
      r.ai = { step: (c: any) => c.input(1, "NONE") } as any;
    }
  manager.tick();
}, 1000 / 60);
http.listen(3104, "127.0.0.1", () => {
  const player = resolve("../gesture-player");
  const child = spawn(
    resolve(player, ".venv/Scripts/python.exe"),
    ["tests/integration_pve_round.py"],
    { cwd: player, env: { ...process.env, PYTHONUTF8: "1" }, stdio: "inherit" },
  );
  child.on("exit", (code) => {
    clearInterval(timer);
    io.close();
    http.close();
    repo.close();
    process.exit(code ?? 1);
  });
});
