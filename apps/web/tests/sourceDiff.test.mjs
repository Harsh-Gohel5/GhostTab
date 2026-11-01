import assert from "node:assert/strict";
import test from "node:test";
import { sourceDiff } from "../src/sourceDiff.ts";

test("a changed deadline keeps surrounding evidence and marks old and new lines", () => {
  assert.deepEqual(
    sourceDiff(
      "Maya owns launch.\nApprove Thursday.\nSupport unassigned.",
      "Maya owns launch.\nApprove Friday.\nSupport unassigned.",
    ),
    [
      { kind: "unchanged", text: "Maya owns launch." },
      { kind: "removed", text: "Approve Thursday." },
      { kind: "added", text: "Approve Friday." },
      { kind: "unchanged", text: "Support unassigned." },
    ],
  );
});

test("insertions, deletions and repeated lines reconstruct both exact input versions", () => {
  for (const [before, after] of [
    ["", "Nina owns review."],
    ["Keep\nRemove", "Keep"],
    ["A\nA\nB", "A\nB\nB"],
    ["A\r\nB", "A\nB\n"],
    ["same", "same"],
  ]) {
    const diff = sourceDiff(before, after);
    assert.equal(
      diff
        .filter((x) => x.kind !== "added")
        .map((x) => x.text)
        .join("\n"),
      before,
    );
    assert.equal(
      diff
        .filter((x) => x.kind !== "removed")
        .map((x) => x.text)
        .join("\n"),
      after,
    );
  }
});

test("large sources use bounded whole-version comparison without losing content", () => {
  const before = Array.from({ length: 201 }, (_, i) => String(i)).join("\n");
  const after = before + "\nNina owns review.";
  assert.deepEqual(sourceDiff(before, after), [
    { kind: "removed", text: before },
    { kind: "added", text: after },
  ]);
});
