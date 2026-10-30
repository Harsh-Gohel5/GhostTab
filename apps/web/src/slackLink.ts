export function slackSelection(link: string): {
  channel_id: string;
  thread_ts: string;
} {
  const error = new Error(
    "Copy a public-channel message link from the connected Slack workspace.",
  );
  let url: URL;
  try {
    url = new URL(link.trim());
  } catch {
    throw error;
  }
  if (
    url.protocol !== "https:" ||
    !/^[a-z0-9-]+\.slack\.com$/i.test(url.hostname) ||
    url.username ||
    url.password
  )
    throw error;
  const match = url.pathname.match(
    /^\/archives\/(C[A-Z0-9]{1,60})\/p([0-9]{16,22})\/?$/,
  );
  if (!match) throw error;
  const raw = match[2];
  const ts =
    url.searchParams.get("thread_ts") || raw.slice(0, -6) + "." + raw.slice(-6);
  if (!/^[0-9]{10,16}\.[0-9]{6}$/.test(ts)) throw error;
  return { channel_id: match[1], thread_ts: ts };
}
