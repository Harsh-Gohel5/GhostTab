import assert from "node:assert/strict";
import test from "node:test";
import { briefMarkdown } from "../src/briefExport.ts";

function workspace() {
  const point = {
    text: "Approval is pending.",
    citations: [
      {
        evidence_id: "source",
        quote: "Original revision: approval is pending.",
      },
    ],
  };
  return {
    task: {
      title: "Campaign planning",
      goal: "Prepare a handoff.",
      freshness: "stale",
    },
    evidence: [
      {
        id: "source",
        content: "New private source content must not replace an old citation.",
      },
    ],
    snapshot: {
      created_at: 1793116800,
      draft: "Saved old draft",
      brief: { summary: point, facts: [point], next_steps: [], unknowns: [] },
      citations: [
        {
          id: "source",
          title: "Original notes",
          content: "Full source content is intentionally excluded.",
          url: "https://example.com/notes",
        },
      ],
    },
  };
}

test("stale export preserves cited revision, warns and includes current unsaved draft", () => {
  const data = workspace();
  data.snapshot.citations.push({
    id: "unused",
    title: "Uncited private source",
    content: "Not needed",
    url: "https://example.com/unused-private-link",
  });
  const markdown = briefMarkdown(data, "My edited, unsaved message");
  assert.match(markdown, /STATUS: OUTDATED/);
  assert.match(markdown, /Original revision: approval is pending\./);
  assert.match(markdown, /My edited, unsaved message/);
  assert.doesNotMatch(
    markdown,
    /Saved old draft|New private source content|Full source content|Uncited private source|unused-private-link/,
  );
  assert.match(markdown, /Source 1/);
});

test("untrusted Markdown cannot close the draft block or embed source-title media", () => {
  const data = workspace();
  data.task.title = "![image](https://example.com/pixel)";
  data.snapshot.citations[0].title = "<img src=https://example.com/pixel>";
  data.snapshot.brief.unknowns = ["<script>not executable</script>"];
  const draft = "```\n![image](https://example.com/pixel)\n```";
  const markdown = briefMarkdown(data, draft);
  assert.ok(markdown.startsWith("# \\!\\[image\\]\\("));
  assert.ok(markdown.includes("````text\n" + draft + "\n````"));
  assert.ok(markdown.includes("\\<img src="));
  assert.doesNotMatch(markdown, /(?<!\\)<(?:script|img)/);
});

test("a workspace without a saved brief cannot be exported", () => {
  assert.throws(
    () => briefMarkdown({ ...workspace(), snapshot: null }, "Draft"),
    /Prepare a brief/,
  );
});
