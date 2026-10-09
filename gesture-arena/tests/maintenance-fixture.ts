/** Isolated real SQLite/CLI acceptance. Never opens the user's leaderboard. */
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve, join } from "node:path";
import { spawnSync } from "node:child_process";
import { strict as assert } from "node:assert";
import { LeaderboardRepository, RunResult } from "../apps/server/leaderboard.js";
const base = resolve("evidence", "排行榜 維護驗證", crypto.randomUUID());
mkdirSync(base, { recursive: true });
const first = join(base, "原始"), second = join(base, "恢復");
const row: RunResult = {
  runId: "fixture-unique", playerId: "fixture-player", nickname: '測試,"暱稱"',
  defeated: 3, reason: "death", ticks: 1600, hp: 0,
  rulesVersion: "fixture-v1", aiVersion: "fixture-ai", sourceHistory: ["recognizer"],
  eligible: true, internal: false, completedAt: "2026-10-09T00:00:00Z", seed: 1,
};
let repo = new LeaderboardRepository(join(first, "leaderboard.sqlite"));
repo.save(row); repo.close();
repo = new LeaderboardRepository(join(first, "leaderboard.sqlite"));
assert.deepEqual(repo.all(), [row]); repo.close();
const backup = join(base, "備份.json"), csv = join(base, "備份.csv");
const logs: any[] = [];
function cli(dataDir: string, args: string[], expected = 0) {
  const p = spawnSync(process.execPath, ["--import", "tsx", "apps/server/maintenance.ts", ...args], {
    env: { ...process.env, ARENA_DATA_DIR: dataDir }, encoding: "utf8",
  });
  logs.push({ args, exitCode: p.status, stdout: p.stdout, stderr: p.stderr });
  assert.equal(p.status, expected, JSON.stringify(logs.at(-1)));
}
cli(first, ["backup", backup]); cli(first, ["export", csv]);
assert.ok(readFileSync(csv, "utf8").includes('"測試,""暱稱"""'));
cli(second, ["import", backup]); cli(second, ["import", backup]);
repo = new LeaderboardRepository(join(second, "leaderboard.sqlite"));
assert.deepEqual(repo.all(), [row]); repo.close();
const conflict = join(base, "衝突.json");
writeFileSync(conflict, JSON.stringify([{ ...row, runId: "must-rollback" }, { ...row, defeated: 99 }]));
cli(second, ["import", conflict], 1);
repo = new LeaderboardRepository(join(second, "leaderboard.sqlite"));
assert.deepEqual(repo.all(), [row]); repo.close();
cli(second, ["clear", "fixture-v1", "fixture-ai"], 1);
cli(second, ["clear", "fixture-v1", "fixture-ai", "--confirm"]);
repo = new LeaderboardRepository(join(second, "leaderboard.sqlite"));
assert.equal(repo.all().length, 0); repo.close();
writeFileSync("evidence/maintenance.json", JSON.stringify({ pass: true, base, checks: ["restart persistence", "JSON backup/restore", "CSV quoting", "idempotent import", "conflict rollback", "clear confirmation"], logs }, null, 2));
console.log("Real SQLite + maintenance CLI: 6 checks PASS");
