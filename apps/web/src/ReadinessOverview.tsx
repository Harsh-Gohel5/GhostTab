import { useState } from "react";
import type { Task } from "./api";
import { readiness } from "./readiness";

export function ReadinessOverview({
  tasks,
  onOpen,
  onViewAll,
}: {
  tasks: Task[];
  onOpen: (task: Task) => void;
  onViewAll: () => void;
}) {
  const [filter, setFilter] = useState("attention");
  const attention = tasks.filter(
    (task) => !["ready", "preparing"].includes(readiness(task).kind),
  );
  const ready = tasks.filter((task) => readiness(task).kind === "ready");
  const visible =
    filter === "attention" ? attention : filter === "ready" ? ready : tasks;
  return (
    <section className="readiness-overview" aria-labelledby="readiness-title">
      <div className="section-heading">
        <h2 id="readiness-title">What needs your attention</h2>
        <button className="text-button" onClick={onViewAll}>
          All workspaces →
        </button>
      </div>
      <p className="readiness-explanation">
        Based on saved context. Use Check Calendar inside a meeting workspace to
        check for newer event details.
      </p>
      <div
        className="readiness-filters"
        role="group"
        aria-label="Filter workspace readiness"
      >
        {[
          {
            id: "attention",
            label: "Needs attention",
            count: attention.length,
          },
          { id: "ready", label: "Ready to review", count: ready.length },
          { id: "all", label: "All", count: tasks.length },
        ].map((item) => (
          <button
            key={item.id}
            aria-pressed={filter === item.id}
            onClick={() => setFilter(item.id)}
          >
            {item.label}
            <span>{item.count}</span>
          </button>
        ))}
      </div>
      <div className="readiness-results" aria-live="polite">
        {visible.length ? (
          <div className="task-list">
            {visible.slice(0, 5).map((task) => {
              const status = readiness(task);
              return (
                <button
                  className="readiness-row"
                  key={task.id}
                  onClick={() => onOpen(task)}
                >
                  <span className="task-copy">
                    <strong>{task.title}</strong>
                    <span>{status.hint}</span>
                  </span>
                  <span className={`badge ${status.tone}`}>{status.label}</span>
                  <span className="readiness-action">{status.action} →</span>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="readiness-empty">
            <h3>
              {filter === "attention"
                ? "A little breathing room."
                : filter === "ready"
                  ? "Your next brief starts with context."
                  : "Start with your next meeting or task."}
            </h3>
            <p>
              {filter === "attention"
                ? "No saved workspaces need attention right now. Check All for any preparations in progress."
                : filter === "ready"
                  ? "No current briefs are ready to review yet. Choose a workspace under Needs attention to get started."
                  : "Choose a Calendar event below, or create a workspace and add notes."}
            </p>
          </div>
        )}
        {visible.length > 5 && (
          <button className="text-button" onClick={onViewAll}>
            View all workspaces →
          </button>
        )}
      </div>
    </section>
  );
}
