import { it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { LABELS, validInput } from "../packages/protocol/index.js";
it("independent bundled protocol fixtures and every file SHA match", () => {
  const manifest = JSON.parse(readFileSync("protocol/manifest.json", "utf8"));
  for (const [path, hash] of Object.entries(manifest.fileHashes))
    expect(
      createHash("sha256")
        .update(readFileSync("protocol/" + path))
        .digest("hex"),
    ).toBe(hash);
  const fixtures = JSON.parse(
    readFileSync("protocol/fixtures/inputs.json", "utf8"),
  );
  expect(fixtures.valid.map((v: any) => v.gesture)).toEqual([...LABELS]);
  for (const v of fixtures.valid) expect(validInput(v)).toBe(true);
  for (const v of fixtures.invalid) expect(validInput(v)).toBe(false);
});
