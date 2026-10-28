import assert from "node:assert/strict";
import test from "node:test";
import { preparationMessage } from "../src/preparationReadiness.ts";

test("offline recovery distinguishes a saved request from lost work", () => {
  const result = preparationMessage("offline");
  assert.match(result.message, /requests stay saved/);
  assert.match(result.message, /resume/);
  assert.match(result.message, /review briefs and edit drafts/);
});
test("configuration and budget guidance do not promise provider health or automatic budget increases", () => {
  assert.match(
    preparationMessage("ready").message,
    /does not verify Meta access/,
  );
  assert.match(
    preparationMessage("budget_exhausted").message,
    /retrying will not restore budget/,
  );
  assert.match(preparationMessage("disabled").message, /server settings/);
  assert.match(preparationMessage("unconfigured").message, /workspace owner/);
});
