// Opt-in: start auth_browser_fixture.py first. Never targets real Supabase.
import assert from "node:assert/strict";
import test from "node:test";
import { createClient } from "@supabase/supabase-js";
import { signOutAccount } from "../src/accountSession.ts";

const base = "http://127.0.0.1:8011";
async function scenario(body = {}) {
  const response = await globalThis.fetch(`${base}/synthetic/scenario`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: globalThis.AbortSignal.timeout(5000),
  });
  assert.equal(response.status, 200);
}

test(
  "actual SDK handles valid/expired sessions and partial logout",
  { timeout: 15000 },
  async () => {
    const saved = new Map();
    const storage = {
      getItem: (k) => saved.get(k) ?? null,
      setItem: (k, v) => saved.set(k, v),
      removeItem: (k) => saved.delete(k),
    };
    const client = createClient(base, "synthetic-public-key", {
      auth: {
        autoRefreshToken: false,
        persistSession: true,
        storage,
        storageKey: "ghosttab-fixture-integration",
        detectSessionInUrl: false,
      },
    });
    try {
      await scenario();
      const { data, error } = await client.auth.signInWithPassword({
        email: "demo@example.test",
        password: "demo-password",
      });
      assert.equal(error, null);
      assert.equal(data.user.id, "synthetic-auth-owner");
      await scenario({ refresh_failure: "rejected" });
      const refreshed = await client.auth.refreshSession();
      assert.ok(refreshed.error);
      assert.equal(
        (await client.auth.getSession()).data.session?.user.id,
        "synthetic-auth-owner",
      );
      // Only test-owned memory is altered: emulate an expired saved session.
      const expired = JSON.parse(saved.get("ghosttab-fixture-integration"));
      expired.expires_at = 1;
      const expiredStore = new Map([
        ["ghosttab-expired-integration", JSON.stringify(expired)],
      ]);
      const expiredClient = createClient(base, "synthetic-public-key", {
        auth: {
          autoRefreshToken: false,
          persistSession: true,
          detectSessionInUrl: false,
          storageKey: "ghosttab-expired-integration",
          storage: {
            getItem: (k) => expiredStore.get(k) ?? null,
            setItem: (k, v) => expiredStore.set(k, v),
            removeItem: (k) => expiredStore.delete(k),
          },
        },
      });
      try {
        assert.equal(
          (await expiredClient.auth.getSession()).data.session === null,
          true,
        );
      } finally {
        await expiredClient.auth.stopAutoRefresh();
      }

      await scenario();
      assert.equal(
        (
          await client.auth.signInWithPassword({
            email: "other@example.test",
            password: "demo-password",
          })
        ).error,
        null,
      );
      await scenario({ logout_failure: true });
      assert.match(
        await signOutAccount(client.auth),
        /Signed out on this browser/,
      );
      assert.equal((await client.auth.getSession()).data.session, null);
    } finally {
      await scenario();
      await client.auth.stopAutoRefresh();
    }
  },
);
