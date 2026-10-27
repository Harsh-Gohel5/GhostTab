import type { Task } from "./api";

const failures: Record<string, string> = {
  budget_exhausted:
    "The preparation budget has been reached. Check preparation access before trying again.",
  model_access_denied:
    "Meta could not authorize this request. Check preparation access in Connections.",
  model_requests_disabled:
    "AI preparation is paused. Your saved context is still available.",
  model_not_configured:
    "AI preparation needs to be set up in Connections first.",
  model_connection_failed:
    "GhostTab could not reach Meta. Check the connection, then try again.",
  model_temporarily_unavailable:
    "Meta is temporarily unavailable. Wait a moment before trying again.",
  model_request_rejected:
    "Meta could not accept this request. Check preparation access before trying again.",
  context_too_large:
    "There is too much context for one brief. Shorten your notes or remove a source before trying again.",
  evidence_required: "Add some source notes before preparing a brief.",
  invalid_citation:
    "The response could not be matched to your sources, so it was not saved as a brief. You can try again.",
  invalid_model_output:
    "The response could not be checked, so it was not saved as a brief. You can try again.",
  model_output_incomplete:
    "The response ended before the brief was complete. You can try again.",
  model_response_invalid:
    "Meta returned a response GhostTab could not read. You can try again.",
};

export function PreparationStatus({
  task,
  hasBrief,
  sourceCount,
  enabled,
  starting,
  onRetry,
  onReview,
}: {
  task: Task;
  hasBrief: boolean;
  sourceCount: number;
  enabled: boolean;
  starting: boolean;
  onRetry: () => void;
  onReview: () => void;
}) {
  const job = task.job?.generation === task.generation ? task.job : null;
  const busy =
    starting || job?.status === "queued" || job?.status === "running";
  const failed = !busy && job?.status === "failed";
  const stale = task.freshness === "stale";
  const exhausted = failed && job.attempts >= 3;
  let heading = sourceCount
    ? "Your context is ready to prepare"
    : "Start with a little context";
  let message = sourceCount
    ? "Prepare a brief to turn these sources into key facts, open questions, and a draft you can review."
    : "Add notes or choose a Calendar meeting, then prepare your brief.";
  let tone = "idle";
  if (hasBrief) {
    heading = "Brief ready for review";
    message =
      "This brief uses the saved source revisions shown here. Review its supporting quotes and make the draft your own.";
    tone = "ready";
  }
  if (stale) {
    heading = "Your brief needs an update";
    message =
      "Your source context changed. The brief and draft below still use earlier notes. Update the brief before relying on them.";
    tone = "stale";
  }
  if (busy) {
    heading = starting
      ? "Starting preparation"
      : job?.status === "running"
        ? "Preparing your brief"
        : job && job.attempts > 0
          ? "Waiting to try again"
          : "Waiting to prepare";
    message = starting
      ? "Sending a preparation request using your saved context."
      : job?.status === "queued"
        ? "Your request is waiting to be processed. You can leave this workspace and return later."
        : "Reading your saved context and checking the response against its sources. You can leave this workspace and return later.";
    if (stale) message += " The previous brief below still needs an update.";
    tone = "working";
  }
  if (failed) {
    heading = "Preparation did not finish";
    message = exhausted
      ? "The three-attempt limit for this source revision has been reached. Review preparation access and your source context before preparing a revised version."
      : (failures[job.error_code ?? ""] ??
        "Something interrupted preparation. Check your connection and try again.");
    if (hasBrief)
      message += stale
        ? " Your previous brief is still available, but uses earlier context."
        : " Your previous brief is still available.";
    tone = "failed";
  }
  const retryable =
    failed &&
    !exhausted &&
    ![
      "budget_exhausted",
      "model_access_denied",
      "model_requests_disabled",
      "model_not_configured",
      "model_request_rejected",
      "context_too_large",
      "evidence_required",
    ].includes(job.error_code ?? "");
  return (
    <section
      className={`preparation-status ${tone}`}
      aria-label="Brief preparation"
    >
      <div
        className="preparation-message"
        role={failed ? "alert" : "status"}
        aria-atomic="true"
      >
        <span className="preparation-symbol" aria-hidden="true">
          {busy ? "◷" : stale || failed ? "!" : hasBrief ? "✓" : "✧"}
        </span>
        <div>
          <h2>{heading}</h2>
          <p>{message}</p>
        </div>
      </div>
      <ol className="preparation-steps" aria-label="Preparation steps">
        <li className={sourceCount ? "complete" : ""}>
          <span aria-hidden="true">1</span>Save context
          {sourceCount > 0 && (
            <small>
              {sourceCount} {sourceCount === 1 ? "source" : "sources"}
            </small>
          )}
        </li>
        <li
          className={busy ? "active" : hasBrief && !stale ? "complete" : ""}
          aria-current={busy ? "step" : undefined}
        >
          <span aria-hidden="true">2</span>Prepare brief
          <small>
            {busy
              ? "In progress"
              : stale
                ? "Update needed"
                : hasBrief
                  ? "Prepared"
                  : "When you’re ready"}
          </small>
        </li>
        <li className={hasBrief && !stale && !busy ? "active" : ""}>
          <span aria-hidden="true">3</span>
          {hasBrief ? (
            <button className="text-button" onClick={onReview}>
              {stale ? "Review previous brief ↓" : "Review & edit ↓"}
            </button>
          ) : (
            "Review & edit"
          )}
          <small>You decide what to use</small>
        </li>
      </ol>
      {retryable && enabled && sourceCount > 0 && (
        <button className="secondary" onClick={onRetry}>
          Try preparation again
        </button>
      )}
      {!enabled && !busy && (
        <p className="preparation-paused">
          AI preparation is currently paused. You can still save notes, inspect
          sources, and edit a saved draft.
        </p>
      )}
    </section>
  );
}
