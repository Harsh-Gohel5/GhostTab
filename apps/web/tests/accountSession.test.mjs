import assert from "node:assert/strict";
import test from "node:test";
import { setImmediate, setTimeout } from "node:timers";
import {
  watchSession,
  accountToken,
  signOutAccount,
} from "../src/accountSession.ts";

const session = (id) => ({ user: { id }, access_token: `token-${id}` });
function fixture() {
  let resolve, reject, event;
  let unsubscribed = false;
  const restored = new Promise((yes, no) => {
    resolve = yes;
    reject = no;
  });
  const auth = {
    getSession: () => restored,
    onAuthStateChange: (callback) => {
      event = callback;
      return {
        data: {
          subscription: {
            unsubscribe: () => {
              unsubscribed = true;
            },
          },
        },
      };
    },
  };
  return {
    auth,
    resolve,
    reject,
    emit: (...args) => event(...args),
    unsubscribed: () => unsubscribed,
  };
}
const tick = () => new Promise((resolve) => setImmediate(resolve));

test("restoration cannot undo sign-out or a newer account event", async () => {
  for (const value of [null, session("B")]) {
    const f = fixture(),
      seen = [];
    const stop = watchSession(
      f.auth,
      (s) => seen.push(s),
      () => assert.fail("unexpected error"),
    );
    f.emit(value ? "SIGNED_IN" : "SIGNED_OUT", value);
    f.resolve({ data: { session: session("A") }, error: null });
    await tick();
    assert.deepEqual(seen, [value]);
    stop();
    assert.equal(f.unsubscribed(), true);
  }
});
test("restoration succeeds and rejection/timeout permit sign-in without publishing stale data", async () => {
  const f = fixture(),
    seen = [];
  const stop = watchSession(
    f.auth,
    (s) => seen.push(s),
    () => seen.push("error"),
    10,
  );
  await new Promise((resolve) => setTimeout(resolve, 25));
  f.resolve({ data: { session: session("A") }, error: null });
  await tick();
  assert.deepEqual(seen, ["error"]);
  f.emit("SIGNED_IN", session("B"));
  assert.equal(seen[1].user.id, "B");
  stop();
  for (const failed of [false, true]) {
    const f = fixture(),
      results = [];
    const stop = watchSession(
      f.auth,
      (s) => results.push(s),
      () => results.push("error"),
    );
    if (failed) f.reject(new Error("private provider failure"));
    else f.resolve({ data: { session: session("A") }, error: null });
    await tick();
    assert.deepEqual(results, [failed ? "error" : session("A")]);
    stop();
  }
});
test("unmount suppresses pending restoration and auth events", async () => {
  const f = fixture();
  const stop = watchSession(
    f.auth,
    () => assert.fail(),
    () => assert.fail(),
  );
  stop();
  f.emit("SIGNED_IN", session("A"));
  f.resolve({ data: { session: session("A") }, error: null });
  await tick();
});
test("a request bound to A never receives B's credentials", async () => {
  for (const value of [null, session("B")])
    await assert.rejects(
      accountToken(
        { getSession: async () => ({ data: { session: value } }) },
        "A",
      ),
      /changed or expired/,
    );
  assert.equal(
    await accountToken(
      { getSession: async () => ({ data: { session: session("A") } }) },
      "A",
    ),
    "token-A",
  );
});
test("sign-out distinguishes cleared local state from a retryable retained session", async () => {
  const auth = {
    signOut: async () => ({ error: new Error("private detail") }),
    getSession: async () => ({ data: { session: null }, error: null }),
  };
  assert.match(await signOutAccount(auth), /Signed out on this browser/);
  await assert.rejects(
    signOutAccount({
      ...auth,
      getSession: async () => ({
        data: { session: session("A") },
        error: null,
      }),
    }),
    /Please retry/,
  );
  assert.equal(
    await signOutAccount({ ...auth, signOut: async () => ({ error: null }) }),
    "",
  );
});
