export function teamsChat(value: string): { chat_id: string } {
  let id = value.trim();
  if (!id.startsWith("19:")) {
    try {
      const url = new URL(id);
      if (
        url.protocol !== "https:" ||
        !["teams.microsoft.com", "teams.cloud.microsoft"].includes(
          url.hostname,
        ) ||
        url.port ||
        url.username ||
        url.password ||
        url.hash
      )
        throw new Error();
      const match = /^\/l\/chat\/([^/]+)\/conversations\/?$/.exec(url.pathname);
      if (!match) throw new Error();
      id = decodeURIComponent(match[1]);
      // Context query parameters never enter the API request.
    } catch {
      throw new Error(
        "Enter an existing Teams chat ID or its /l/chat/…/conversations link.",
      );
    }
  }
  if (id.length > 256 || !/^19:[A-Za-z0-9_.@-]+$/.test(id))
    throw new Error(
      "Choose a valid Teams chat ID. Channel links and new-chat links are not supported.",
    );
  return { chat_id: id };
}
