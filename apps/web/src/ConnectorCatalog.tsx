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
  const [selected, setSelected] = useState<CatalogEntry | null>(null);
  const [trigger, setTrigger] = useState<HTMLButtonElement | null>(null);
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
        (filter === "all" ||
          (filter === "available"
            ? !!item.provider
            : availability(item) === filter)),
    )
    .sort((a, b) => Number(!!b.provider) - Number(!!a.provider));
  const clear = () => {
    setQuery("");
    setCategory("all");
    setFilter("all");
  };
  return (
    <section className="connector-catalog" aria-label="Integration catalog">
      <div className="catalog-heading">
        <p className="muted">
          Pick a tool to view its connection options. You’re always in control.
        </p>
        <span className="catalog-count">
          {connectorCatalog.length} tools · {connectorCategories.length}{" "}
          categories
        </span>
      </div>
      <div
        className="catalog-quick-filters"
        aria-label="Quick integration filters"
      >
        {[
          { value: "all", label: "All tools", count: connectorCatalog.length },
          {
            value: "available",
            label: "Connection options",
            count: connectorCatalog.filter((x) => x.provider).length,
          },
          {
            value: "Connected",
            label: "Connected",
            count: connectorCatalog.filter(
              (x) => availability(x) === "Connected",
            ).length,
          },
          {
            value: "Planned",
            label: "Planned",
            count: connectorCatalog.filter((x) => !x.provider).length,
          },
        ].map((item) => (
          <button
            key={item.value}
            className={`catalog-filter ${filter === item.value ? "is-active" : ""}`}
            aria-pressed={filter === item.value}
            onClick={() => setFilter(item.value)}
          >
            {item.label}
            <span>{item.count}</span>
          </button>
        ))}
      </div>
      <div className="catalog-filters">
        <label>
          Find a tool
          <input
            type="search"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
            }}
            placeholder="Search 49 tools…"
          />
        </label>
        <label>
          Category
          <select
            value={category}
            onChange={(event) => {
              setCategory(event.target.value);
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
            }}
          >
            <option value="all">All integrations</option>
            <option value="available">Connection options</option>
            {["Connected", "Ready to connect", "Setup required", "Planned"].map(
              (name) => (
                <option key={name}>{name}</option>
              ),
            )}
          </select>
        </label>
      </div>
      <p role="status" className="muted">
        {filtered.length} {filtered.length === 1 ? "tool" : "tools"} · Planned
        tools are previews only; they cannot connect or read accounts.
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
        {filtered.map((item) => (
          <ConnectorTile
            key={item.id}
            item={item}
            state={availability(item)}
            onOpen={(button) => {
              setTrigger(button);
              setSelected(item);
            }}
          />
        ))}
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
      {selected && (
        <ConnectorDetails
          key={selected.id}
          item={selected}
          state={availability(selected)}
          renderConnection={renderConnection}
          returnFocus={trigger}
          onClose={() => setSelected(null)}
        />
      )}
    </section>
  );
}

export function ConnectorTile({
  item,
  state,
  onOpen,
}: {
  item: CatalogEntry;
  state: Availability;
  onOpen: (button: HTMLButtonElement) => void;
}) {
  return (
    <button
      type="button"
      className="catalog-tile"
      aria-label={`${item.name} — ${state}`}
      aria-haspopup="dialog"
      onClick={(event) => onOpen(event.currentTarget)}
    >
      <span
        className={`catalog-dot ${state === "Connected" ? "is-connected" : item.provider ? "is-available" : ""}`}
        aria-hidden="true"
      />
      <span className="connector-logo">
        <img src={`/connectors/${item.id}.svg`} alt="" width="32" height="32" />
      </span>
      <span className="catalog-tile-name">{item.name}</span>
      <span className="catalog-tile-status">
        {state === "Planned"
          ? "Planned"
          : state === "Connected"
            ? "Connected"
            : "View options"}
      </span>
    </button>
  );
}

export function ConnectorDetails({
  item,
  state,
  renderConnection,
  onClose,
  returnFocus,
}: {
  item: CatalogEntry;
  state: Availability;
  renderConnection: (provider: LiveProvider) => ReactNode;
  onClose: () => void;
  returnFocus?: HTMLButtonElement | null;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const element = dialog.current!;
    const overflow = document.body.style.overflow;
    element.showModal();
    document.body.style.overflow = "hidden";
    return () => {
      element.close();
      document.body.style.overflow = overflow;
      returnFocus?.focus({ preventScroll: true });
    };
  }, [returnFocus]);
  return (
    <dialog
      ref={dialog}
      className="catalog-dialog"
      aria-labelledby="connector-detail-title"
      aria-describedby="connector-detail-summary"
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
    >
      <div className="catalog-dialog-heading">
        <span className="connector-logo">
          <img
            src={`/connectors/${item.id}.svg`}
            width="40"
            height="40"
            alt=""
          />
        </span>
        <div>
          <p className="eyebrow">
            {item.provider ? "YOUR CONNECTION" : "ON THE ROADMAP"}
          </p>
          <h2 id="connector-detail-title">{item.name}</h2>
        </div>
        <button
          type="button"
          className="catalog-close"
          aria-label={`Close ${item.name} details`}
          autoFocus
          onClick={onClose}
        >
          ✕
        </button>
      </div>
      <div className="catalog-dialog-meta">
        <span
          className={`catalog-status ${state === "Connected" ? "catalog-connected" : ""}`}
        >
          {state}
        </span>
        <span>{item.categories.join(" · ")}</span>
      </div>
      <p id="connector-detail-summary" className="muted">
        {item.context}
      </p>
      <div className="catalog-controls">
        {item.provider ? (
          renderConnection(item.provider)
        ) : (
          <div className="catalog-planned">
            <h3>A little further down the road.</h3>
            <p>
              We’re exploring how {item.name} can bring useful context into your
              workspace.
            </p>
            <p className="muted">
              This is a planned integration. Connection and import are not
              available yet, and this preview does not access your account.
            </p>
          </div>
        )}
      </div>
    </dialog>
  );
}
