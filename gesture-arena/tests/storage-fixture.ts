/** Generate isolated valid results to exercise the 1MB minimum warning threshold. */
import { LeaderboardRepository } from "../apps/server/leaderboard.js";
import { resolve } from "node:path";
const repo = new LeaderboardRepository(resolve("../evidence/storage-warning-data/leaderboard.sqlite"));
for (let i = 0; i < 6000; i++) repo.save({
  runId: `storage-fixture-${i}`, playerId: "fixture", nickname: "容量測試",
  defeated: 0, reason: "death", ticks: 1, hp: 0,
  rulesVersion: "fixture", aiVersion: "fixture", sourceHistory: ["keyboard"],
  eligible: false, internal: true, completedAt: "2026-10-09T00:00:00Z", seed: 1,
});
repo.close(); console.log("Isolated storage fixture ready");
