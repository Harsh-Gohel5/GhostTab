import assert from "node:assert/strict";
import test, { before, after } from "node:test";
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath, URL } from "node:url";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createServer } from "vite";
import { connectorCatalog, matchesConnector } from "../src/catalogData.ts";

let server, components;
before(async () => {
  server = await createServer({
    root: fileURLToPath(new URL("../", import.meta.url)),
    cacheDir: "node_modules/.vite-catalog-tests",
    server: { middlewareMode: true, hmr: false },
    appType: "custom",
  });
  components = await server.ssrLoadModule("/src/ConnectorCatalog.tsx");
});
after(async () => {
  await server?.close();
});

test("all 49 products have locally bundled SVG marks with provenance and no active content", () => {
  assert.equal(connectorCatalog.length, 49);
  const sources = JSON.parse(
    readFileSync(
      new URL("../public/connectors/SOURCES.json", import.meta.url),
      "utf8",
    ),
  );
  for (const item of connectorCatalog) {
    const file = new URL(
      `../public/connectors/${item.id}.svg`,
      import.meta.url,
    );
    assert.ok(existsSync(file), item.id);
    const svg = readFileSync(file, "utf8");
    assert.match(svg, /<svg\b/);
    assert.doesNotMatch(
      svg,
      /<script|<foreignObject|\bon\w+\s*=|(?:href|src)=["'](?:https?:|\/\/|javascript:)/i,
    );
    assert.match(sources[item.id].source, /^https:\/\//);
  }
});

test("gallery starts with 25 logo tiles, two pages, and deferred connection controls", () => {
  const client = new QueryClient();
  const html = renderToStaticMarkup(
    createElement(
      QueryClientProvider,
      { client },
      createElement(components.ConnectorCatalog, {
        api: {},
        owner: "synthetic",
        calendarStatus: { connected: true, configured: true },
        renderConnection: () =>
          assert.fail("Initial gallery must not mount provider controls"),
        onRetryCalendar: () => {},
      }),
    ),
  );
  assert.equal((html.match(/class="catalog-tile"/g) ?? []).length, 25);
  assert.equal((html.match(/aria-haspopup="dialog"/g) ?? []).length, 25);
  assert.doesNotMatch(html, /Show more integrations/);
  assert.match(html, /Google Calendar — Connected/);
  assert.match(html, /Slack — Checking status/);
  assert.match(html, /1–25 of 49 tools/);
  assert.match(html, /Page 1 of 2/);
  assert.match(html, /aria-label="Page 2"/);
  assert.equal(
    (html.match(/class="catalog-tile-status">View options/g) ?? []).length,
    25,
  );
  client.clear();
});

test("details reuse real provider controls and unavailable tools expose an honest connection action", () => {
  const selected = connectorCatalog.find((item) => item.provider === "slack");
  const html = renderToStaticMarkup(
    createElement(components.ConnectorDetails, {
      item: selected,
      state: "Setup required",
      onClose: () => {},
      renderConnection: (provider) => {
        assert.equal(provider, "slack");
        return createElement("button", null, "Existing Slack controls");
      },
    }),
  );
  assert.match(html, /<dialog/);
  assert.match(html, /Setup required/);
  assert.match(html, /Existing Slack controls/);
  assert.match(html, /Close Slack details/);
  const preview = renderToStaticMarkup(
    createElement(components.ConnectorDetails, {
      item: {
        ...connectorCatalog.find((item) => item.id === "notion"),
        context: "<script>untrusted</script>",
      },
      state: "Planned",
      onClose: () => {},
      renderConnection: () =>
        assert.fail("Planned tools must not mount provider controls"),
    }),
  );
  assert.match(preview, /Connect to Notion/);
  assert.match(preview, /This connection is not available in this release/);
  assert.match(preview, /No account access or import is enabled/);
  assert.match(preview, /&lt;script&gt;untrusted&lt;\/script&gt;/);
});

test("every unavailable product has its own connect action without mounting a provider flow", () => {
  for (const item of connectorCatalog.filter((item) => !item.provider)) {
    const html = renderToStaticMarkup(
      createElement(components.ConnectorDetails, {
        item,
        state: "Planned",
        onClose: () => {},
        renderConnection: () =>
          assert.fail(`${item.name} must not mount OAuth controls`),
      }),
    );
    assert.ok(html.includes(`Connect to ${item.name}`), item.name);
    assert.match(html, /aria-describedby="connector-availability"/);
    assert.match(html, /Not available yet/);
  }
});

test("catalog category and text search combine and preserve a single Teams entry", () => {
  assert.equal(
    connectorCatalog.filter((item) =>
      matchesConnector(item, "teams", "Meetings"),
    ).length,
    1,
  );
  assert.equal(
    connectorCatalog.filter((item) =>
      matchesConnector(item, "teams", "Team messaging"),
    ).length,
    1,
  );
  assert.equal(
    connectorCatalog
      .filter((item) =>
        matchesConnector(item, "  GOOGLE   DOCUMENT  ", "Google documents"),
      )
      .some((item) => item.name === "Google Docs"),
    true,
  );
  assert.equal(
    connectorCatalog.filter((item) =>
      matchesConnector(item, "gmail", "Development"),
    ).length,
    0,
  );
});

test("planned previews never map to connection providers and supported providers are unique", () => {
  const planned = connectorCatalog.filter((item) => !item.provider);
  assert.ok(planned.some((item) => item.name === "Salesforce"));
  assert.ok(planned.some((item) => item.name === "Google Sheets"));
  assert.equal(
    new Set(connectorCatalog.map((item) => item.id)).size,
    connectorCatalog.length,
  );
  assert.deepEqual(
    connectorCatalog
      .filter((item) => item.provider)
      .map((item) => item.provider)
      .sort(),
    ["gmail", "google_calendar", "google_docs", "jira", "slack", "teams"],
  );
});
