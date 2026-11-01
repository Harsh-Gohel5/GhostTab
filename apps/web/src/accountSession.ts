import type { SupabaseClient } from "@supabase/supabase-js";

type SessionAuth = Pick<
  SupabaseClient["auth"],
  "getSession" | "onAuthStateChange"
>;
type Session = Awaited<
  ReturnType<SessionAuth["getSession"]>
>["data"]["session"];

// Keep restoration subordinate to newer events, including after unmount.
export function watchSession(
  auth: SessionAuth,
  onSession: (session: Session, event?: string) => void,
  onError: () => void,
  timeoutMs = 10000,
) {
  let active = true;
  let observed = false;
  const timer = setTimeout(() => {
    if (active && !observed) {
      observed = true;
      onError();
    }
  }, timeoutMs);
  const { data } = auth.onAuthStateChange((event, session) => {
    if (!active) return;
    observed = true;
    clearTimeout(timer);
    onSession(session, event);
  });
  void auth
    .getSession()
    .then(({ data, error }) => {
      if (!active || observed) return;
      clearTimeout(timer);
      if (error) onError();
      else onSession(data.session);
    })
    .catch(() => {
      if (active && !observed) {
        clearTimeout(timer);
        onError();
      }
    });
  return () => {
    active = false;
    clearTimeout(timer);
    data.subscription.unsubscribe();
  };
}

export async function accountToken(
  auth: Pick<SessionAuth, "getSession">,
  owner: string,
) {
  const { data, error } = await auth.getSession();
  if (error || !data.session || data.session.user.id !== owner)
    throw new Error("Your account changed or expired. Please sign in again.");
  return data.session.access_token;
}

export async function signOutAccount(
  auth: Pick<SupabaseClient["auth"], "signOut" | "getSession">,
) {
  try {
    const { error } = await auth.signOut();
    if (!error) return "";
  } catch {
    // The SDK may already have cleared this browser before reporting failure.
  }
  try {
    const { data, error } = await auth.getSession();
    if (!error && !data.session)
      return "Signed out on this browser. Other sessions may still be active.";
  } catch {
    /* Preserve the session and offer a retry when state is unknown. */
  }
  throw new Error("Sign out could not finish. Please retry.");
}
