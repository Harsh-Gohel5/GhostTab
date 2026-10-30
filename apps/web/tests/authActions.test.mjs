import assert from "node:assert/strict";
import test from "node:test";
import { startGoogleSignIn, submitAuth } from "../src/authActions.ts";

const values = {
  email: " demo@example.test ",
  password: "  password  ",
  confirmation: "  password  ",
  name: " Fictional User ",
};
const redirect = "http://127.0.0.1:5173/";

test("Google login requests identity scopes only with the application callback", async () => {
  let input;
  await startGoogleSignIn(
    {
      signInWithOAuth: async (value) => {
        input = value;
        return { error: null };
      },
    },
    redirect,
  );
  assert.deepEqual(input, {
    provider: "google",
    options: { redirectTo: redirect, scopes: "openid email profile" },
  });
});

test("signup carries the chosen profile name, exact password and fixed callback; confirmation is not treated as a session", async () => {
  const calls = [];
  const auth = {
    signUp: async (input) => {
      calls.push(input);
      return { data: { session: null }, error: null };
    },
  };
  const message = await submitAuth(auth, "signup", values, redirect);
  assert.deepEqual(calls[0], {
    email: "demo@example.test",
    password: "  password  ",
    options: {
      data: { full_name: "Fictional User" },
      emailRedirectTo: redirect,
    },
  });
  assert.match(message, /confirmation link/);
});

test("mismatched and short new passwords never reach the provider", async () => {
  await assert.rejects(
    submitAuth(
      {},
      "signup",
      { ...values, confirmation: "different" },
      redirect,
    ),
    /match/,
  );
  await assert.rejects(
    submitAuth(
      {},
      "update",
      { ...values, password: "short", confirmation: "short" },
      redirect,
    ),
    /8 characters/,
  );
});

test("recovery uses a fixed callback and does not disclose account existence", async () => {
  const calls = [];
  const message = await submitAuth(
    {
      resetPasswordForEmail: async (...args) => {
        calls.push(args);
        return { error: null };
      },
    },
    "forgot",
    values,
    redirect,
  );
  assert.deepEqual(calls[0], [
    "demo@example.test",
    { redirectTo: redirect + "?auth=recovery" },
  ]);
  assert.match(message, /If an account/);
});

test("sign-in does not trim passwords and provider failures do not expose raw details", async () => {
  let submitted;
  await assert.rejects(
    submitAuth(
      {
        signInWithPassword: async (input) => {
          submitted = input;
          return { error: { message: "private-provider-detail" } };
        },
      },
      "signin",
      values,
      redirect,
    ),
    /Sign-in failed/,
  );
  assert.equal(submitted.password, values.password);
});

test("password update submits only the new password", async () => {
  let submitted;
  const message = await submitAuth(
    {
      updateUser: async (input) => {
        submitted = input;
        return { error: null };
      },
    },
    "update",
    values,
    redirect,
  );
  assert.deepEqual(submitted, { password: values.password });
  assert.match(message, /Password updated/);
});
