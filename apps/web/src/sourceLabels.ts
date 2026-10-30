const samples: Record<string, string> = {
  sample_google_docs: "GOOGLE DOCS",
  sample_gmail: "GMAIL",
  sample_slack: "SLACK",
  sample_jira: "JIRA",
  sample_teams: "TEAMS",
};

export function sourceLabel(origin: string): string {
  if (samples[origin])
    return `SYNTHETIC ${samples[origin]} SAMPLE · NOT CONNECTED`;
  if (origin === "google_calendar") return "GOOGLE CALENDAR · READ ONLY";
  if (origin === "google_docs") return "GOOGLE DOCS · READ ONLY";
  if (origin === "gmail") return "GMAIL · READ ONLY";
  if (origin === "slack") return "SLACK PUBLIC THREAD · READ ONLY";
  if (origin === "jira") return "JIRA CLOUD · READ ONLY";
  if (origin === "manual") return "MANUALLY ADDED NOTES";
  return "SOURCE IMPORT";
}
