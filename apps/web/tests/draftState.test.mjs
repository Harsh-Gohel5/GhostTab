import assert from "node:assert/strict";
import test from "node:test";
import {
  draftReducer,
  initialDraft,
  isDraftDirty,
  hasDraftConflict,
} from "../src/draftState.ts";

const original = { snapshotId: "first", text: "Generated draft" };
const edited = () =>
  draftReducer(initialDraft(original), { type: "edit", text: "My edits" });

test("refetches preserve dirty text; a new brief requires an explicit choice", () => {
  const state = edited();
  assert.equal(
    draftReducer(state, { type: "receive", remote: original }),
    state,
  );
  const newer = { snapshotId: "second", text: "Updated generated draft" };
  const retained = draftReducer(state, { type: "receive", remote: newer });
  assert.equal(retained.text, "My edits");
  assert.ok(hasDraftConflict(retained, newer));
  assert.deepEqual(
    draftReducer(retained, { type: "use-latest", remote: newer }),
    initialDraft(newer),
  );
  const kept = draftReducer(retained, { type: "keep-edits", remote: newer });
  assert.equal(kept.text, "My edits");
  assert.equal(kept.snapshotId, "second");
  assert.ok(isDraftDirty(kept));
  assert.equal(hasDraftConflict(kept, newer), false);
});

test("another tab's save is adopted only while clean", () => {
  const newer = { ...original, text: "Another tab's draft" };
  assert.deepEqual(
    draftReducer(initialDraft(original), { type: "receive", remote: newer }),
    initialDraft(newer),
  );
  const state = draftReducer(edited(), { type: "receive", remote: newer });
  assert.equal(state.text, "My edits");
  assert.ok(hasDraftConflict(state, newer));
});

test("typing during a save remains dirty after the submitted text is acknowledged", () => {
  const submitted = edited();
  const typed = draftReducer(submitted, {
    type: "edit",
    text: "More edits during save",
  });
  const saved = draftReducer(typed, {
    type: "saved",
    expectedDraft: submitted.base,
    remote: { snapshotId: submitted.snapshotId, text: submitted.text },
  });
  assert.equal(saved.base, "My edits");
  assert.equal(saved.text, "More edits during save");
  assert.ok(isDraftDirty(saved));
});

test("late acknowledgements cannot corrupt a newer loaded revision", () => {
  const newer = { snapshotId: "second", text: "New brief draft" };
  const state = initialDraft(newer);
  assert.equal(
    draftReducer(state, {
      type: "saved",
      expectedDraft: original.text,
      remote: { ...original, text: "My edits" },
    }),
    state,
  );
  const otherTab = initialDraft({
    ...original,
    text: "Another tab's saved changes",
  });
  assert.equal(
    draftReducer(otherTab, {
      type: "saved",
      expectedDraft: original.text,
      remote: { ...original, text: "My edits" },
    }),
    otherTab,
  );
});

test("a refetch can confirm a save whose network response was lost", () => {
  const state = edited();
  const saved = draftReducer(state, {
    type: "receive",
    remote: { ...original, text: state.text },
  });
  assert.equal(saved.text, "My edits");
  assert.equal(isDraftDirty(saved), false);
});

test("empty drafts and whitespace edits are tracked exactly", () => {
  const empty = draftReducer(initialDraft(original), {
    type: "edit",
    text: "",
  });
  assert.ok(isDraftDirty(empty));
  const spaced = draftReducer(initialDraft(original), {
    type: "edit",
    text: original.text + "\n",
  });
  assert.ok(isDraftDirty(spaced));
  assert.equal(
    isDraftDirty(draftReducer(spaced, { type: "edit", text: original.text })),
    false,
  );
});
