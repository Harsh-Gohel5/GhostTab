import type { SupabaseClient } from "@supabase/supabase-js";

export type AuthMethods = Pick<
  SupabaseClient["auth"],
  | "signInWithPassword"
  | "signUp"
  | "resetPasswordForEmail"
  | "resend"
  | "updateUser"
  | "signInWithOAuth"
>;

export async function startGoogleSignIn(auth: AuthMethods, redirect: string) {
  const { error } = await auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo: redirect, scopes: "openid email profile" },
  });
  if (error)
    throw new Error(
      "Google sign-in could not start. Please retry or use email sign-in.",
    );
}
export type AuthMode = "signin" | "signup" | "forgot" | "update";
export type AuthValues = {
  email: string;
  password: string;
  confirmation: string;
  name: string;
};

export async function submitAuth(
  auth: AuthMethods,
  mode: AuthMode,
  values: AuthValues,
  redirect: string,
) {
  const email = values.email.trim();
  if (
    (mode === "signup" || mode === "update") &&
    (values.password.length < 8 || values.password !== values.confirmation)
  )
    throw new Error("Use at least 8 characters and make both passwords match.");
  if (mode === "signin") {
    const { error } = await auth.signInWithPassword({
      email,
      password: values.password,
    });
    if (error)
      throw new Error(
        "Sign-in failed. Check your details and confirm your email, or reset your password.",
      );
    return "Signed in. Opening your workspace…";
  }
  if (mode === "signup") {
    const { data, error } = await auth.signUp({
      email,
      password: values.password,
      options: {
        data: { full_name: values.name.trim().slice(0, 80) },
        emailRedirectTo: redirect,
      },
    });
    if (error)
      throw new Error(
        "Account creation could not finish. Check your details, wait a moment, or try signing in.",
      );
    return data.session
      ? "Signed in. Opening your workspace…"
      : "Check your inbox for a confirmation link. If you already have an account, sign in or reset your password.";
  }
  if (mode === "forgot") {
    const { error } = await auth.resetPasswordForEmail(email, {
      redirectTo: redirect + "?auth=recovery",
    });
    if (error)
      throw new Error(
        "Recovery could not be requested. Wait a moment and try again.",
      );
    return "If an account can receive recovery email, a link has been requested. Check your inbox and spam folder.";
  }
  const { error } = await auth.updateUser({ password: values.password });
  if (error)
    throw new Error(
      "Password could not be updated. Open a fresh recovery link and try again.",
    );
  return "Password updated. Continue to your workspace.";
}
