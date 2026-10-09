import { writeFileSync, mkdirSync } from "node:fs";
import { SKILLS, RULES_VERSION } from "../packages/game-core/skills.js";
mkdirSync("evidence", { recursive: true });
writeFileSync(
  "evidence/registry.json",
  JSON.stringify({ rulesVersion: RULES_VERSION, skills: SKILLS }, null, 2),
);
