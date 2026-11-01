import assert from "node:assert/strict";
import { before, after, test } from "node:test";
import { fileURLToPath, URL } from "node:url";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

let server;
let SourceChanges;
before(async () => {
  server = await createServer({
    root: fileURLToPath(new URL("../", import.meta.url)),
    cacheDir: "node_modules/.vite-source-changes-tests",
    server: { middlewareMode: true, hmr: false },
    appType: "custom",
  });
  ({ SourceChanges } = await server.ssrLoadModule("/src/SourceChanges.tsx"));
});
after(async () => {
  await server?.close();
});

function render(changes, disabled = false) {
  return renderToStaticMarkup(
    createElement(SourceChanges, {
      changes,
      disabled,
      busy: false,
      onUpdate() {
        throw new Error("Rendering must not prepare");
      },
    }),
  );
}

const current = {
  id: "doc",
  version_id: "new",
  title: "Launch doc",
  content: "Nina owns review.",
  url: "",
  origin: "google_docs",
  observed_at: 2,
};
test("comparison shows saved baselines and cited claims, escapes source text and disables update", () => {
  const html = render(
    [
      {
        kind: "updated",
        current: { ...current, title: "<script>untrusted</script>" },
        previous: {
          ...current,
          version_id: "old",
          content: "Owner is unknown.",
          observed_at: 1,
        },
        changed_fields: ["title", "content"],
        claims_to_review: [
          {
            section: "fact",
            text: "Review owner is unknown.",
            quotes: ["Owner is unknown."],
          },
        ],
      },
    ],
    true,
  );
  assert.match(html, /Used in the previous brief/);
  assert.match(html, /Current saved source/);
  assert.match(html, /Review owner is unknown\./);
  assert.match(html, /&lt;script&gt;untrusted&lt;\/script&gt;/);
  assert.doesNotMatch(html, /<script>/);
  assert.match(html, /disabled=""/);
  assert.match(html, /A source update does not prove/);
});

test("added source has no invented previous version or cited claims; current context hides panel", () => {
  assert.equal(render([]), "");
  const html = render([
    {
      kind: "added",
      current,
      previous: null,
      changed_fields: ["content"],
      claims_to_review: [],
    },
  ]);
  assert.match(html, /Added since preparation/);
  assert.match(html, /not included in the saved brief/);
  assert.match(html, /not individually citation-linked/);
  assert.doesNotMatch(html, /Used in the previous brief/);
  assert.doesNotMatch(html, /disabled=""/);
});
