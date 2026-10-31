import assert from "node:assert/strict";
import test from "node:test";
import { connectorCatalog, matchesConnector } from "../src/catalogData.ts";

test("catalog category and text search combine and preserve a single Teams entry", () => {
  assert.equal(
    connectorCatalog.filter((item) =>
      matchesConnector(item, "teams", "Meetings"),
    ).length,
    1,
  );
  assert.equal(
    connectorCatalog.filter((item) =>
      matchesConnector(item, "teams", "Team messaging"),
    ).length,
    1,
  );
  assert.equal(
    connectorCatalog
      .filter((item) =>
        matchesConnector(item, "  GOOGLE   DOCUMENT  ", "Google documents"),
      )
      .some((item) => item.name === "Google Docs"),
    true,
  );
  assert.equal(
    connectorCatalog.filter((item) =>
      matchesConnector(item, "gmail", "Development"),
    ).length,
    0,
  );
});

test("planned previews never map to connection providers and supported providers are unique", () => {
  const planned = connectorCatalog.filter((item) => !item.provider);
  assert.ok(planned.some((item) => item.name === "Salesforce"));
  assert.ok(planned.some((item) => item.name === "Google Sheets"));
  assert.equal(
    new Set(connectorCatalog.map((item) => item.id)).size,
    connectorCatalog.length,
  );
  assert.deepEqual(
    connectorCatalog
      .filter((item) => item.provider)
      .map((item) => item.provider)
      .sort(),
    ["gmail", "google_calendar", "google_docs", "jira", "slack", "teams"],
  );
});
