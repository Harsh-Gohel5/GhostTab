import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { jiraKey } from "../src/jiraLink.ts";

describe("Jira selection", () => {
  it("normalizes keys and accepts only a selected site's canonical issue link", () => {
    assert.equal(jiraKey(" demo-42 ", "https://demo.atlassian.net"), "DEMO-42");
    assert.equal(
      jiraKey(
        "https://demo.atlassian.net/browse/DEMO-42",
        "https://demo.atlassian.net",
      ),
      "DEMO-42",
    );
    for (const link of [
      "https://other.atlassian.net/browse/DEMO-42",
      "https://user@demo.atlassian.net/browse/DEMO-42",
      "https://demo.atlassian.net/browse/DEMO-42?x=1",
      "https://demo.atlassian.net/browse/DEMO%2F42",
      "DEMO-42/else",
    ]) {
      assert.throws(() => jiraKey(link, "https://demo.atlassian.net"));
    }
  });
});
