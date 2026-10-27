import type { Task } from "./api";

export function readiness(task: Task) {
  const job = task.job?.generation === task.generation ? task.job : null;
  if (!task.source_count)
    return {
      kind: "context",
      label: "Needs context",
      action: "Add context",
      hint: "Add the notes or meeting details this brief should use.",
      tone: "stale",
    };
  if (job?.status === "queued" || job?.status === "running")
    return {
      kind: "preparing",
      label: "Preparing",
      action: "View progress",
      hint: "Your requested preparation is in progress.",
      tone: "working",
    };
  if (job?.status === "failed")
    return {
      kind: "failed",
      label: "Needs attention",
      action: "Review issue",
      hint: "Preparation could not finish. Open the workspace for recovery steps.",
      tone: "stale",
    };
  if (task.freshness === "stale")
    return {
      kind: "stale",
      label: "Update needed",
      action: "Update brief",
      hint: "Saved source context changed after this brief was prepared.",
      tone: "stale",
    };
  if (task.freshness === "current")
    return {
      kind: "ready",
      label: "Ready to review",
      action: "Review brief",
      hint: "A brief and an editable draft are waiting for your review.",
      tone: "ready",
    };
  return {
    kind: "unprepared",
    label: "Ready to prepare",
    action: "Prepare brief",
    hint: "Source context is saved. Open the workspace to request a brief.",
    tone: "",
  };
}
