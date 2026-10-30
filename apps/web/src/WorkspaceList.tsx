import { useState } from "react";
import type { Task } from "./api";
import { readiness } from "./readiness";

const filters = [
  { id: "active", label: "Active" },
  { id: "all", label: "All" },
  { id: "context", label: "Needs context" },
  { id: "unprepared", label: "Ready to prepare" },
  { id: "preparing", label: "Preparing" },
  { id: "ready", label: "Ready to review" },
  { id: "reviewed", label: "Reviewed" },
  { id: "completed", label: "Completed" },
  { id: "stale", label: "Update needed" },
  { id: "failed", label: "Needs attention" },
] as const;

export function WorkspaceList({
  tasks,
  onOpen,
}: {
  tasks: Task[];
  onOpen: (task: Task) => void;
}) {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<string>("active");
  const terms = search.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  const matches = tasks.filter((task) => {
    const text = `${task.title} ${task.goal}`.toLocaleLowerCase();
    return terms.every((term) => text.includes(term));
  });
  const visible = matches.filter(
    (task) =>
      filter === "all" ||
      (filter === "active"
        ? task.lifecycle === "active"
        : readiness(task).kind === filter),
  );
  const clear = () => {
    setSearch("");
    setFilter("all");
  };
  return (
    <section aria-label="Saved workspaces">
      <label>
        Search workspaces
        <input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search by title or goal"
          maxLength={200}
        />
      </label>
      <div
        className="readiness-filters"
        role="group"
        aria-label="Filter saved workspaces"
      >
        {filters.map((item) => (
          <button
            key={item.id}
            aria-pressed={filter === item.id}
            onClick={() => setFilter(item.id)}
          >
            {item.label}
            <span>
              {item.id === "all"
                ? matches.length
                : item.id === "active"
                  ? matches.filter((task) => task.lifecycle === "active").length
                  : matches.filter((task) => readiness(task).kind === item.id)
                      .length}
            </span>
          </button>
        ))}
      </div>
      <p className="muted" role="status">
        Showing {visible.length} of {tasks.length} loaded workspaces. Search
        covers titles and goals.
        {tasks.length >= 100 && " Only the latest 100 workspaces are loaded."}
      </p>
      {visible.length ? (
        <div className="task-list">
          {visible.map((task) => {
            const status = readiness(task);
            return (
              <button
                className="task-row"
                key={task.id}
                onClick={() => onOpen(task)}
              >
                <span className="event-symbol" aria-hidden="true">
                  {task.from_calendar ? "◷" : "✧"}
                </span>
                <span className="task-copy">
                  <strong>{task.title}</strong>
                  <span>{task.goal}</span>
                </span>
                <span className={`badge ${status.tone}`}>{status.label}</span>
                <span aria-hidden="true">↗</span>
              </button>
            );
          })}
        </div>
      ) : (
        <div className="empty-state">
          <h2>No matching workspaces.</h2>
          <p>Try different words or choose another readiness filter.</p>
          <button className="secondary" onClick={clear}>
            Clear search and filters
          </button>
        </div>
      )}
    </section>
  );
}
