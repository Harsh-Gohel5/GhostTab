import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { Api, Workspace } from "./api";
import { preparedDate } from "./dates";

export function TaskLifecycle({
  api,
  owner,
  workspace,
  blocked,
  onChanged,
}: {
  api: Api;
  owner: string;
  workspace: Workspace;
  blocked: boolean;
  onChanged: () => void;
}) {
  const cache = useQueryClient();
  const { task } = workspace;
  const change = useMutation({
    mutationFn: (action: "review" | "complete" | "reopen") =>
      api.changeLifecycle(workspace, action),
    onSuccess: (updated) => {
      cache.setQueryData<Workspace>(["workspace", owner, task.id], (saved) =>
        saved ? { ...saved, task: updated } : saved,
      );
      onChanged();
    },
    onError: onChanged,
  });
  return (
    <section className="panel" aria-label="Task progress">
      <div className="section-heading">
        <h2>Your progress</h2>
        <span
          className={`badge ${task.lifecycle === "completed" || task.review_current ? "ready" : ""}`}
        >
          {task.lifecycle === "completed"
            ? "Completed"
            : task.review_current
              ? "Reviewed"
              : "Active"}
        </span>
      </div>
      <p>
        {task.lifecycle === "completed"
          ? `Marked complete ${preparedDate(task.completed_at!)}. Reopen whenever you need to continue.`
          : task.review_current
            ? `Brief and saved draft marked reviewed ${preparedDate(task.reviewed_at!)}.`
            : task.reviewed_at !== null
              ? "Your previous review applies to an older brief or source context. Review the current version again."
              : "Review the brief and draft, then mark this task complete when your work is finished. Drafts stay unsent."}
      </p>
      {task.changed_since_completion && (
        <p className="notice" role="status">
          Source context changed after completion. Reopen this workspace if it
          needs more work.
        </p>
      )}
      {blocked && (
        <p role="status">
          Save or discard draft edits before changing task progress.
        </p>
      )}
      <div className="draft-actions">
        <button
          className="secondary"
          disabled={
            blocked ||
            change.isPending ||
            task.review_current ||
            !workspace.snapshot ||
            task.freshness !== "current"
          }
          onClick={() => change.mutate("review")}
        >
          {task.review_current ? "Brief reviewed" : "Mark brief reviewed"}
        </button>
        <button
          className="secondary"
          disabled={blocked || change.isPending}
          onClick={() =>
            change.mutate(
              task.lifecycle === "completed" ? "reopen" : "complete",
            )
          }
        >
          {task.lifecycle === "completed"
            ? "Reopen workspace"
            : "Mark complete"}
        </button>
      </div>
      {change.isPending && <p role="status">Saving progress…</p>}
      {change.error && (
        <p className="notice error" role="alert">
          {change.error instanceof Error
            ? change.error.message
            : "Progress could not be saved. Please retry."}
        </p>
      )}
    </section>
  );
}
