import { useState } from "react";
import type { FormEvent } from "react";
import { GhostMark } from "./GhostMark";
import { ThemeToggle } from "./ThemeToggle";
import {
  finishPasswordRecovery,
  startGoogleSignIn,
  submitAuth,
} from "./authActions";
import type { AuthMethods, AuthMode } from "./authActions";

export function AuthPanel({
  auth,
  recovery,
  initialError,
  initialNotice = "",
  onRecovered,
  synthetic,
  googleState,
  onCheckGoogle,
  checkingGoogle,
}: {
  auth: AuthMethods;
  recovery: boolean;
  initialError: string;
  initialNotice?: string;
  onRecovered: () => void;
  synthetic: boolean;
  googleState: "checking" | "enabled" | "disabled" | "unavailable";
  onCheckGoogle: () => void;
  checkingGoogle: boolean;
}) {
  const [mode, setMode] = useState<AuthMode>("signin");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState(initialError);
  const [updated, setUpdated] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const effectiveMode = recovery ? "update" : mode;
  const go = (next: AuthMode) => {
    setMode(next);
    setError("");
    setMessage("");
    setShowPassword(false);
  };
  const redirect = location.origin + location.pathname;
  async function googleSignIn() {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await startGoogleSignIn(auth, redirect);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Google sign-in failed. Please retry.",
      );
    } finally {
      setBusy(false);
    }
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = new FormData(form);
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const result = await submitAuth(
        auth,
        effectiveMode,
        {
          email: String(values.get("email") ?? ""),
          password: String(values.get("password") ?? ""),
          confirmation: String(values.get("confirmation") ?? ""),
          name: String(values.get("name") ?? ""),
        },
        redirect,
      );
      setMessage(result);
      form.reset();
      if (effectiveMode === "update") {
        setUpdated(true);
        await finishPasswordRecovery(auth);
        onRecovered();
      }
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Request could not finish. Please retry.",
      );
    } finally {
      setBusy(false);
    }
  }
  async function resend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const email = String(
      new FormData(event.currentTarget).get("email") ?? "",
    ).trim();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const { error } = await auth.resend({
        type: "signup",
        email,
        options: { emailRedirectTo: redirect },
      });
      if (error)
        throw new Error(
          "Confirmation could not be requested. Wait a moment and retry.",
        );
      setMessage(
        "If confirmation is available for this address, a new link has been requested.",
      );
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Confirmation request failed.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="auth-page">
      <div className="auth-theme">
        <ThemeToggle />
      </div>
      <section className="auth-card" aria-label="Account access">
        {synthetic && (
          <p className="notice">
            Synthetic authentication test · Fictional credentials only · No real
            accounts or email delivery.
          </p>
        )}
        <span className="brand-mark auth-ghost">
          <GhostMark />
        </span>
        <p className="eyebrow">YOUR NEXT TASK, IN CONTEXT</p>
        <h1>
          {effectiveMode === "signup"
            ? "Make yourself some space."
            : effectiveMode === "forgot"
              ? "Let’s get you back in."
              : effectiveMode === "update"
                ? "Choose a new password."
                : "Welcome to GhostTab."}
        </h1>
        <p className="muted">
          {effectiveMode === "signup"
            ? "Create an account to keep your workspaces together."
            : effectiveMode === "forgot"
              ? "Request a recovery link for your account."
              : effectiveMode === "update"
                ? "Use a password you haven’t used before."
                : "Sign in to pick up where you left off."}
        </p>
        {!recovery && (
          <>
            <button
              className="secondary google-signin"
              disabled={busy || googleState !== "enabled"}
              onClick={() => void googleSignIn()}
            >
              <span aria-hidden="true">G</span> Continue with Google
            </button>
            <p className="muted auth-provider-note">
              Sign in to GhostTab. Connect your work tools separately.
            </p>
            {googleState !== "enabled" && (
              <div className="auth-provider-note" role="status">
                <p>
                  {googleState === "checking"
                    ? "Checking Google sign-in…"
                    : googleState === "disabled"
                      ? "Google sign-in is not available yet. You can use email sign-in."
                      : "Google sign-in availability could not be checked. You can use email or retry."}
                </p>
                {googleState !== "checking" && (
                  <button
                    type="button"
                    className="text-button"
                    disabled={busy || checkingGoogle}
                    onClick={onCheckGoogle}
                  >
                    {checkingGoogle
                      ? "Checking…"
                      : "Check Google sign-in again"}
                  </button>
                )}
              </div>
            )}
          </>
        )}
        {!recovery && (
          <div
            className="readiness-filters"
            role="group"
            aria-label="Account options"
          >
            <button
              disabled={busy}
              aria-pressed={mode === "signin"}
              onClick={() => go("signin")}
            >
              Sign in
            </button>
            <button
              disabled={busy}
              aria-pressed={mode === "signup"}
              onClick={() => go("signup")}
            >
              Create account
            </button>
          </div>
        )}
        {!updated && (
          <form key={effectiveMode} onSubmit={submit}>
            <fieldset disabled={busy}>
              {effectiveMode === "signup" && (
                <label>
                  Your name
                  <input
                    name="name"
                    autoComplete="name"
                    maxLength={80}
                    required
                  />
                </label>
              )}
              {effectiveMode !== "update" && (
                <label>
                  Email
                  <input
                    name="email"
                    type="email"
                    autoComplete="email"
                    maxLength={254}
                    required
                  />
                </label>
              )}
              {effectiveMode !== "forgot" && (
                <>
                  <label>
                    {effectiveMode === "update" ? "New password" : "Password"}
                    <input
                      name="password"
                      type={showPassword ? "text" : "password"}
                      autoComplete={
                        effectiveMode === "signin"
                          ? "current-password"
                          : "new-password"
                      }
                      minLength={effectiveMode === "signin" ? undefined : 8}
                      maxLength={256}
                      required
                    />
                  </label>
                  {(effectiveMode === "signup" ||
                    effectiveMode === "update") && (
                    <label>
                      Confirm password
                      <input
                        name="confirmation"
                        type={showPassword ? "text" : "password"}
                        autoComplete="new-password"
                        minLength={8}
                        maxLength={256}
                        required
                      />
                    </label>
                  )}
                  <button
                    className="text-button"
                    type="button"
                    aria-pressed={showPassword}
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? "Hide password" : "Show password"}
                  </button>
                </>
              )}
              <button className="primary auth-submit" type="submit">
                {busy
                  ? "Please wait…"
                  : effectiveMode === "signup"
                    ? "Create account"
                    : effectiveMode === "forgot"
                      ? "Send recovery link"
                      : effectiveMode === "update"
                        ? "Update password"
                        : "Sign in"}
              </button>
            </fieldset>
          </form>
        )}
        {!recovery && (
          <button
            className="text-button"
            disabled={busy}
            onClick={() => go(mode === "forgot" ? "signin" : "forgot")}
          >
            {mode === "forgot" ? "Back to sign in" : "Forgot password?"}
          </button>
        )}
        {!recovery && (
          <details className="auth-confirmation">
            <summary>Need another confirmation link?</summary>
            <form onSubmit={resend}>
              <label>
                Confirmation email
                <input
                  name="email"
                  type="email"
                  maxLength={254}
                  autoComplete="email"
                  required
                  disabled={busy}
                />
              </label>
              <button className="secondary" disabled={busy}>
                Resend confirmation
              </button>
            </form>
          </details>
        )}
        {(message || initialNotice) && (
          <p className="notice" role="status">
            {message || initialNotice}
          </p>
        )}
        {error && (
          <p className="notice error" role="alert">
            {error}
          </p>
        )}
        {updated && (
          <button
            className="primary"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              setError("");
              try {
                await finishPasswordRecovery(auth);
                onRecovered();
              } catch (reason) {
                setError(
                  reason instanceof Error
                    ? reason.message
                    : "Sign out could not finish. Retry returning to sign in.",
                );
              } finally {
                setBusy(false);
              }
            }}
          >
            {busy ? "Returning to sign in…" : "Retry return to sign in"}
          </button>
        )}
      </section>
    </main>
  );
}
