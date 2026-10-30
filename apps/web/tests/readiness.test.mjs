import assert from "node:assert/strict";
import test from "node:test";
import { readiness } from "../src/readiness.ts";

const base = {
  source_count: 1,
  generation: 2,
  job: null,
  freshness: "current",
  lifecycle: "active",
  review_current: false,
  changed_since_completion: false,
};

test("a generated brief requires a human review decision", () => {
  assert.equal(readiness(base).kind, "ready");
  assert.equal(readiness({ ...base, review_current: true }).kind, "reviewed");
});

test("stale and removed source context override a previous review", () => {
  assert.equal(
    readiness({ ...base, review_current: true, freshness: "stale" }).kind,
    "stale",
  );
  assert.equal(
    readiness({ ...base, review_current: true, source_count: 0 }).kind,
    "context",
  );
});

test("completion persists independently of new context or preparation failures", () => {
  const completed = {
    ...base,
    lifecycle: "completed",
    source_count: 0,
    freshness: "stale",
    changed_since_completion: true,
  };
  assert.equal(readiness(completed).kind, "completed");
  assert.match(readiness(completed).label, /context changed/);
  assert.equal(
    readiness({ ...completed, lifecycle: "active" }).kind,
    "context",
  );
});

test("only a current-generation job changes preparation readiness", () => {
  assert.equal(
    readiness({ ...base, job: { generation: 1, status: "failed" } }).kind,
    "ready",
  );
  assert.equal(
    readiness({ ...base, job: { generation: 2, status: "running" } }).kind,
    "preparing",
  );
});
