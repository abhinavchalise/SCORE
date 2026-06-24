import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const STYLES_DIR = join(process.cwd(), "src", "styles");

function cssFiles(dir: string): string[] {
  return readdirSync(dir)
    .filter((name) => name.endsWith(".css"))
    .map((name) => join(dir, name));
}

describe("css sizing uses rem", () => {
  for (const file of cssFiles(STYLES_DIR)) {
    it(`${file} has no px except 1px borders`, () => {
      const content = readFileSync(file, "utf8");
      const offenders = content.match(/\d+px/g)?.filter((token) => token !== "1px") ?? [];
      expect(offenders).toEqual([]);
    });
  }
});
