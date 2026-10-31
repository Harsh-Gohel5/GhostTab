import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { useQueries } from "@tanstack/react-query";
import type { Api } from "./api";
import {
  connectorCatalog,
  connectorCategories,
  matchesConnector,
} from "./catalogData";
import type { CatalogEntry, LiveProvider } from "./catalogData";

const liveSources = ["google_docs", "gmail", "slack", "jira", "teams"] as const;
type Availability =
  | "Connected"
  | "Ready to connect"
  | "Setup required"
  | "Planned"
  | "Checking status"
  | "Status unavailable";

export function ConnectorCatalog({
  api,
  owner,
  calendarStatus,
  renderConnection,
  onRetryCalendar,
}: {
  api: Api;
  owner: string;
  calendarStatus?: { connected: boolean; configured: boolean } | null;
  renderConnection: (provider: LiveProvider) => ReactNode;
  onRetryCalendar: () => void;
}) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");
  const [filter, setFilter] = useState("all");
  const [limit, setLimit] = useState(12);
  const [selected, setSelected] = useState<CatalogEntry | null>(null);
  const detail = useRef<HTMLElement>(null);
  const trigger = useRef<HTMLButtonElement | null>(null);
  const sources = useQueries({
    queries: liveSources.map((provider) => ({
      queryKey: ["source-connection", owner, provider],
      queryFn: () =>
        provider === "google_docs" || provider === "gmail"
          ? api.sourceConnection(provider)
          : provider === "slack"
            ? api.slackConnection()
            : provider === "jira"
              ? api.jiraConnection()
              : api.teamsConnection(),
    })),
  });
  useEffect(() => {
    if (selected) {
      detail.current?.focus({ preventScroll: true });
      detail.current?.scrollIntoView({ block: "nearest" });
    }
  }, [selected]);
  function availability(item: CatalogEntry): Availability {
    if (!item.provider) return "Planned";
    if (item.provider === "google_calendar" && calendarStatus === null)
      return "Status unavailable";
    const index = liveSources.findIndex((source) => source === item.provider);
    if (item.provider !== "google_calendar" && sources[index]?.isError)
      return "Status unavailable";
    const value =
      item.provider === "google_calendar"
        ? calendarStatus
        : sources[index]?.data;
    if (!value) return "Checking status";
    return value.connected
      ? "Connected"
      : value.configured
        ? "Ready to connect"
        : "Setup required";
  }
  const filtered = connectorCatalog
    .filter(
      (item) =>
        matchesConnector(item, query, category) &&
        (filter === "all" || availability(item) === filter),
    )
    .sort((a, b) => Number(!!b.provider) - Number(!!a.provider));
  const clear = () => {
    setQuery("");
    setCategory("all");
    setFilter("all");
    setLimit(12);
  };
  return (
    <section className="connector-catalog" aria-label="Integration catalog">
      <div className="catalog-heading">
        <div>
          <h2>One place for your working context.</h2>
          <p className="muted">
            Explore {connectorCatalog.length} tools across{" "}
            {connectorCategories.length} categories. Connect the tools available
            today, or explore the roadmap.
          </p>
        </div>
        <span className="badge">
          {connectorCatalog.filter((item) => item.provider).length} connection
          options · {connectorCatalog.filter((item) => !item.provider).length}{" "}
          planned
        </span>
      </div>
      <p className="catalog-disclosure">
        Planned integrations are previews only. They cannot connect, read
        accounts or import data yet.
      </p>
      <div className="catalog-filters">
        <label>
          Find a tool
          <input
            type="search"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setLimit(12);
            }}
            placeholder="Search tools or context…"
          />
        </label>
        <label>
          Category
          <select
            value={category}
            onChange={(event) => {
              setCategory(event.target.value);
              setLimit(12);
            }}
          >
            <option value="all">All categories</option>
            {connectorCategories.map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </label>
        <label>
          Availability
          <select
            value={filter}
            onChange={(event) => {
              setFilter(event.target.value);
              setLimit(12);
            }}
          >
            <option value="all">All integrations</option>
            {["Connected", "Ready to connect", "Setup required", "Planned"].map(
              (name) => (
                <option key={name}>{name}</option>
              ),
            )}
          </select>
        </label>
      </div>
      <p role="status" className="muted">
        Showing {Math.min(limit, filtered.length)} of {filtered.length} matching
        integrations.
      </p>
      {(calendarStatus === null ||
        sources.some((source) => source.isError)) && (
        <p className="notice" role="status">
          Some connection statuses could not be checked.{" "}
          <button
            className="text-button"
            onClick={() => {
              onRetryCalendar();
              sources.forEach((source) => {
                void source.refetch();
              });
            }}
          >
            Retry connection statuses
          </button>
        </p>
      )}
      <div className="catalog-grid">
        {filtered.slice(0, limit).map((item) => {
          const state = availability(item);
          return (
            <article
              key={item.id}
              className={`catalog-card ${item.provider ? "catalog-supported" : ""}`}
            >
              <div className="catalog-card-heading">
                <span className="connector-avatar" aria-hidden="true">
                  {item.name
                    .split(" ")
                    .map((word) => word[0])
                    .join("")
                    .slice(0, 2)}
                </span>
                <span
                  className={`catalog-status ${state === "Connected" ? "catalog-connected" : ""}`}
                >
                  {state}
                </span>
              </div>
              <h3>{item.name}</h3>
              <p>{item.context}</p>
              <span className="catalog-category">
                {item.categories.join(" · ")}
              </span>
              <button
                className="text-button"
                aria-expanded={selected?.id === item.id}
                aria-controls="connector-detail"
                onClick={(event) => {
                  trigger.current = event.currentTarget;
                  setSelected({ ...item });
                }}
              >
                {item.provider ? `Manage ${item.name}` : `Preview ${item.name}`}
              </button>
            </article>
          );
        })}
      </div>
      {!filtered.length && (
        <div className="form-panel">
          <h3>No matching tools</h3>
          <p>Try another tool, category or availability.</p>
          <button className="secondary" onClick={clear}>
            Clear filters
          </button>
        </div>
      )}
      {limit < filtered.length && (
        <button
          className="secondary catalog-more"
          onClick={() => setLimit((value) => value + 12)}
        >
          Show more integrations ({filtered.length - limit} remaining)
        </button>
      )}
      {selected && (
        <section
          className="catalog-detail"
          id="connector-detail"
          tabIndex={-1}
          ref={detail}
          aria-label={`${selected.name} integration details`}
        >
          <div className="catalog-detail-heading">
            <h2>{selected.name}</h2>
            <button
              className="text-button"
              onClick={() => {
                setSelected(null);
                trigger.current?.focus();
              }}
            >
              Close details
            </button>
          </div>
          {selected.provider ? (
            renderConnection(selected.provider)
          ) : (
            <div className="form-panel">
              <span className="catalog-status">Planned · preview only</span>
              <h3>Context we’re designing toward</h3>
              <p>{selected.context}</p>
              <p className="muted">
                This integration is on the roadmap. Connection and import are
                not available yet, and this preview does not access your
                account.
              </p>
            </div>
          )}
        </section>
      )}
    </section>
  );
}
