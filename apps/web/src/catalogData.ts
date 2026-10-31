export type LiveProvider =
  "google_calendar" | "google_docs" | "gmail" | "slack" | "jira" | "teams";
export type CatalogEntry = {
  id: string;
  name: string;
  categories: string[];
  context: string;
  provider?: LiveProvider;
};

const entry = (
  id: string,
  name: string,
  categories: string[],
  context: string,
  provider?: LiveProvider,
): CatalogEntry => ({ id, name, categories, context, provider });

export const connectorCatalog: CatalogEntry[] = [
  entry(
    "gmail",
    "Gmail",
    ["Email"],
    "Selected messages, requests and decisions.",
    "gmail",
  ),
  entry(
    "outlook",
    "Outlook Mail",
    ["Email"],
    "Email requests, commitments and conversation context.",
  ),
  entry(
    "slack",
    "Slack",
    ["Team messaging"],
    "Selected public-channel threads and shared decisions.",
    "slack",
  ),
  entry(
    "teams",
    "Microsoft Teams",
    ["Team messaging", "Meetings"],
    "Selected work or school chat excerpts.",
    "teams",
  ),
  entry(
    "google-chat",
    "Google Chat",
    ["Team messaging"],
    "Discussions, mentions and shared links.",
  ),
  entry(
    "discord",
    "Discord",
    ["Team messaging"],
    "Community discussions, questions and shared context.",
  ),
  entry(
    "google-calendar",
    "Google Calendar",
    ["Calendars"],
    "Selected meetings, timing, locations and descriptions.",
    "google_calendar",
  ),
  entry(
    "outlook-calendar",
    "Outlook Calendar",
    ["Calendars"],
    "Upcoming meetings, schedules and event context.",
  ),
  entry(
    "google-drive",
    "Google Drive",
    ["Google documents"],
    "Shared files and discovery of relevant working documents.",
  ),
  entry(
    "google-docs",
    "Google Docs",
    ["Google documents"],
    "Selected document text and source revisions.",
    "google_docs",
  ),
  entry(
    "google-sheets",
    "Google Sheets",
    ["Google documents"],
    "Project trackers, tabular plans and supporting figures.",
  ),
  entry(
    "google-slides",
    "Google Slides",
    ["Google documents"],
    "Presentation text, plans and review context.",
  ),
  entry(
    "onedrive",
    "OneDrive",
    ["Microsoft documents"],
    "Working files and shared project material.",
  ),
  entry(
    "sharepoint",
    "SharePoint",
    ["Microsoft documents"],
    "Team sites, shared knowledge and documents.",
  ),
  entry(
    "word",
    "Microsoft Word",
    ["Microsoft documents"],
    "Written briefs, specifications and review material.",
  ),
  entry(
    "excel",
    "Microsoft Excel",
    ["Microsoft documents"],
    "Workbooks, trackers and operational plans.",
  ),
  entry(
    "powerpoint",
    "Microsoft PowerPoint",
    ["Microsoft documents"],
    "Presentation material and project updates.",
  ),
  entry(
    "notion",
    "Notion",
    ["Knowledge & storage"],
    "Project pages, knowledge and working notes.",
  ),
  entry(
    "confluence",
    "Confluence",
    ["Knowledge & storage"],
    "Team documentation, decisions and specifications.",
  ),
  entry(
    "dropbox",
    "Dropbox",
    ["Knowledge & storage"],
    "Shared files and supporting documents.",
  ),
  entry(
    "box",
    "Box",
    ["Knowledge & storage"],
    "Team content and project reference files.",
  ),
  entry(
    "jira",
    "Jira",
    ["Project management"],
    "Selected issue descriptions, status and manual updates.",
    "jira",
  ),
  entry(
    "asana",
    "Asana",
    ["Project management"],
    "Assignments, dependencies and project updates.",
  ),
  entry(
    "trello",
    "Trello",
    ["Project management"],
    "Cards, checklists and board context.",
  ),
  entry(
    "linear",
    "Linear",
    ["Project management"],
    "Issues, project milestones and status changes.",
  ),
  entry(
    "clickup",
    "ClickUp",
    ["Project management"],
    "Tasks, dependencies and team plans.",
  ),
  entry(
    "monday",
    "monday.com",
    ["Project management"],
    "Board updates, assignments and delivery plans.",
  ),
  entry(
    "planner",
    "Microsoft Planner",
    ["Project management"],
    "Team tasks, assignments and progress.",
  ),
  entry(
    "todo",
    "Microsoft To Do",
    ["Personal tasks"],
    "Personal commitments, reminders and task lists.",
  ),
  entry(
    "todoist",
    "Todoist",
    ["Personal tasks"],
    "Personal tasks, deadlines and priorities.",
  ),
  entry(
    "github",
    "GitHub",
    ["Development"],
    "Issues, pull requests, reviews and build results.",
  ),
  entry(
    "gitlab",
    "GitLab",
    ["Development"],
    "Merge requests, issues and pipeline context.",
  ),
  entry(
    "bitbucket",
    "Bitbucket",
    ["Development"],
    "Pull requests, reviews and repository activity.",
  ),
  entry(
    "azure-devops",
    "Azure DevOps",
    ["Development"],
    "Work items, pull requests and delivery pipelines.",
  ),
  entry(
    "zoom",
    "Zoom",
    ["Meetings"],
    "Meeting references and available shared meeting notes.",
  ),
  entry(
    "google-meet",
    "Google Meet",
    ["Meetings"],
    "Meeting links and available supporting meeting material.",
  ),
  entry(
    "figma",
    "Figma",
    ["Design & collaboration"],
    "Design references, review requests and feedback.",
  ),
  entry(
    "figjam",
    "FigJam",
    ["Design & collaboration"],
    "Workshop notes, planning boards and decisions.",
  ),
  entry(
    "miro",
    "Miro",
    ["Design & collaboration"],
    "Collaborative boards, plans and workshop context.",
  ),
  entry(
    "canva",
    "Canva",
    ["Design & collaboration"],
    "Creative material and collaborative review context.",
  ),
  entry(
    "salesforce",
    "Salesforce",
    ["Sales & customers"],
    "Customer records, opportunities and follow-up context.",
  ),
  entry(
    "hubspot",
    "HubSpot",
    ["Sales & customers"],
    "Customer activity, opportunities and follow-up tasks.",
  ),
  entry(
    "zendesk",
    "Zendesk",
    ["Customer support"],
    "Tickets, customer conversations and escalations.",
  ),
  entry(
    "intercom",
    "Intercom",
    ["Customer support"],
    "Customer conversations and support context.",
  ),
  entry(
    "freshdesk",
    "Freshdesk",
    ["Customer support"],
    "Support tickets, requests and resolutions.",
  ),
  entry(
    "servicenow",
    "ServiceNow",
    ["Operations & incidents"],
    "Service requests, incidents and investigation context.",
  ),
  entry(
    "pagerduty",
    "PagerDuty",
    ["Operations & incidents"],
    "Incident activity, ownership and response context.",
  ),
  entry(
    "sentry",
    "Sentry",
    ["Operations & incidents"],
    "Application issues, error reports and investigation context.",
  ),
  entry(
    "datadog",
    "Datadog",
    ["Operations & incidents"],
    "Alerts, incidents and operational investigation context.",
  ),
];

export const connectorCategories = [
  ...new Set(connectorCatalog.flatMap((item) => item.categories)),
];
export function matchesConnector(
  item: CatalogEntry,
  query: string,
  category: string,
) {
  const text =
    `${item.name} ${item.categories.join(" ")} ${item.context}`.toLowerCase();
  return (
    (category === "all" || item.categories.includes(category)) &&
    query
      .trim()
      .toLowerCase()
      .split(/\s+/)
      .every((word) => text.includes(word))
  );
}
