import type { Workspace } from "./api";

// Export source text as text, never as executable HTML or embedded Markdown media.
const plain = (value: string) =>
  value.replace(/([\\`*_{}[\]<>()#+.!|>-])/g, "\\$1");
const block = (value: string) => {
  const fence = "`".repeat(
    Math.max(
      3,
      ...Array.from(value.matchAll(/`+/g), (match) => match[0].length + 1),
    ),
  );
  return `${fence}text\n${value}\n${fence}`;
};

export function briefMarkdown(data: Workspace, draft: string): string {
  const snapshot = data.snapshot;
  if (!snapshot) throw new Error("Prepare a brief before downloading it.");
  const { brief, citations } = snapshot;
  const points = [brief.summary, ...brief.facts, ...brief.next_steps];
  const usedSources = citations.filter((source) =>
    points.some((item) =>
      item.citations.some((ref) => ref.evidence_id === source.id),
    ),
  );
  const sourceNumber = new Map(
    usedSources.map((source, i) => [source.id, i + 1]),
  );
  const point = (item: typeof brief.summary) =>
    `${plain(item.text)} ${Array.from(
      new Set(item.citations.map((ref) => sourceNumber.get(ref.evidence_id))),
    )
      .map((number) => `(Source ${number ?? "unavailable"})`)
      .join(" ")}`;
  return (
    [
      `# ${plain(data.task.title.replace(/\s+/g, " "))}`,
      "Exported from GhostTab. Review against the sources before using it.",
      data.task.freshness === "stale"
        ? "STATUS: OUTDATED — source context changed. This brief and its quotes use earlier revisions."
        : "Status: matches the saved source revisions. Calendar may have changed since the last manual check.",
      `Prepared: ${new Date(snapshot.created_at * 1000).toISOString()}`,
      "## Goal",
      plain(data.task.goal),
      "## Brief",
      point(brief.summary),
      "## What we know",
      brief.facts.length
        ? brief.facts.map((item) => `- ${point(item)}`).join("\n")
        : "No additional facts were established.",
      "## Suggested next steps",
      brief.next_steps.length
        ? brief.next_steps.map((item) => `- ${point(item)}`).join("\n")
        : "No supported next steps were listed.",
      "## Still to clarify",
      brief.unknowns.length
        ? brief.unknowns.map((item) => `- ${plain(item)}`).join("\n")
        : "No questions were listed. Check the sources before treating the context as complete.",
      "## Draft — unsent",
      "This is the text currently in the draft editor. Downloading does not send it or save edits to GhostTab.",
      block(draft),
      "## Supporting source quotes",
      ...usedSources.flatMap((source, i) => {
        const quotes = Array.from(
          new Set(
            points.flatMap((item) =>
              item.citations
                .filter((ref) => ref.evidence_id === source.id)
                .map((ref) => ref.quote),
            ),
          ),
        );
        return [
          `### Source ${i + 1}: ${plain(source.title.replace(/\s+/g, " "))}`,
          ...(source.url ? ["Original link:", block(source.url)] : []),
          ...quotes.map((quote) => block(quote)),
        ];
      }),
    ].join("\n\n") + "\n"
  );
}

export function downloadBrief(data: Workspace, draft: string) {
  const url = URL.createObjectURL(
    new Blob([briefMarkdown(data, draft)], {
      type: "text/markdown;charset=utf-8",
    }),
  );
  const link = document.createElement("a");
  const name = data.task.title
    .normalize("NFKD")
    .replace(/[^\p{L}\p{N}]+/gu, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 80);
  link.href = url;
  link.download = `ghosttab-${name || "brief"}.md`;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
