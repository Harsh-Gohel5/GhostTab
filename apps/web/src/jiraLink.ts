export function jiraKey(value: string, site: string): string {
  let key = value.trim();
  if (!/^[A-Za-z][A-Za-z0-9_]*-[0-9]+$/.test(key)) {
    let url: URL;
    try {
      url = new URL(key);
    } catch {
      throw new Error("Enter an issue key such as DEMO-42 or its Jira link.");
    }
    if (
      url.origin !== site ||
      url.username ||
      url.password ||
      url.search ||
      url.hash ||
      !/^\/browse\/[^/]+$/.test(url.pathname)
    ) {
      throw new Error(
        "Choose a link from the selected Jira site, without query parameters.",
      );
    }
    key = url.pathname.slice(8);
  }
  key = key.toUpperCase();
  if (key.length > 128 || !/^[A-Z][A-Z0-9_]*-[0-9]+$/.test(key))
    throw new Error("Enter a valid Jira issue key.");
  return key;
}
