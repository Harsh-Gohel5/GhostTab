import { useEffect, useReducer, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Api, ApiError } from "./api";
import type { Workspace } from "./api";
import { downloadBrief } from "./briefExport";
import { ConfirmDialog } from "./ConfirmDialog";
import { readableDates } from "./dates";
import {
  draftReducer,
  hasDraftConflict,
  initialDraft,
  isDraftDirty,
} from "./draftState";

export function DraftEditor({
  api,
  data,
  owner,
  onUnsavedChange,
}: {
  api: Api;
  data: Workspace & { snapshot: NonNullable<Workspace["snapshot"]> };
  owner: string;
  onUnsavedChange: (unsaved: boolean) => void;
}) {
  const queryClient = useQueryClient();
  const snapshot = data.snapshot;
  const remote = { snapshotId: snapshot.id, text: snapshot.draft };
  const [state, dispatch] = useReducer(draftReducer, remote, initialDraft);
  const [feedback, setFeedback] = useState("");
  const [discarding, setDiscarding] = useState(false);
  const dirty = isDraftDirty(state);
  const conflict = hasDraftConflict(state, remote);
  const queryKey = ["workspace", owner, data.task.id];
  useEffect(() => {
    dispatch({
      type: "receive",
      remote: { snapshotId: snapshot.id, text: snapshot.draft },
    });
  }, [snapshot.id, snapshot.draft]);

  const save = useMutation({
    mutationFn: (submitted: typeof state) =>
      api.saveDraft(
        data.task.id,
        submitted.snapshotId,
        submitted.text,
        submitted.base,
      ),
    onSuccess: (_result, submitted) => {
      dispatch({
        type: "saved",
        remote: { snapshotId: submitted.snapshotId, text: submitted.text },
        expectedDraft: submitted.base,
      });
      queryClient.setQueryData<Workspace>(queryKey, (saved) => {
        if (
          !saved?.snapshot ||
          saved.snapshot.id !== submitted.snapshotId ||
          saved.snapshot.draft !== submitted.base
        )
          return saved;
        return {
          ...saved,
          snapshot: { ...saved.snapshot, draft: submitted.text },
        };
      });
      void queryClient.invalidateQueries({ queryKey });
    },
    onError: (error) => {
      if (error instanceof ApiError && error.status === 409)
        void queryClient.invalidateQueries({ queryKey });
    },
  });
  const unsaved = dirty || save.isPending;
  useEffect(() => {
    onUnsavedChange(unsaved);
    return () => onUnsavedChange(false);
  }, [onUnsavedChange, unsaved]);
  useEffect(() => {
    if (!unsaved) return;
    const warn = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [unsaved]);

  const resetFeedback = () => {
    save.reset();
    setFeedback("");
  };
  const copyDraft = async () => {
    try {
      await navigator.clipboard.writeText(state.text);
      setFeedback("Draft copied · nothing sent");
    } catch {
      setFeedback(
        "Could not copy automatically. Select the draft text and copy it manually.",
      );
    }
  };
  return (
    <section className="panel" aria-labelledby="draft-title">
      <h2 id="draft-title">A draft to make your own</h2>
      {discarding && (
        <ConfirmDialog
          message="Replace your unsaved edits with the latest saved draft?"
          confirmLabel="Discard edits"
          onCancel={() => setDiscarding(false)}
          onConfirm={() => {
            dispatch({ type: "use-latest", remote });
            resetFeedback();
            setDiscarding(false);
          }}
        />
      )}
      <p className="muted">
        Review and edit before using it. This message stays unsent.
      </p>
      {conflict && (
        <div className="notice stale draft-conflict" role="alert">
          <p>
            A newer brief or saved draft is available. Your edits are still
            here. Compare before saving.
          </p>
          <details>
            <summary>Compare with the latest saved draft</summary>
            <p className="source-content">
              {snapshot.draft || "The latest saved draft is empty."}
            </p>
          </details>
          <div className="button-group">
            <button
              className="secondary"
              disabled={save.isPending}
              onClick={() => {
                dispatch({ type: "keep-edits", remote });
                resetFeedback();
              }}
            >
              Keep my edits for this brief
            </button>
            <button
              className="text-button"
              disabled={save.isPending}
              onClick={() => {
                if (dirty) {
                  setDiscarding(true);
                  return;
                }
                dispatch({ type: "use-latest", remote });
                resetFeedback();
              }}
            >
              Use latest saved draft
            </button>
          </div>
        </div>
      )}
      <label className="sr-only" htmlFor="draft">
        Editable draft
      </label>
      <textarea
        id="draft"
        rows={7}
        maxLength={6000}
        value={state.text}
        onChange={(event) => {
          dispatch({ type: "edit", text: event.target.value });
          // Keep the pending mutation alive when typing during a save.
          if (!save.isPending) save.reset();
          setFeedback("");
        }}
      />
      <div className="draft-actions">
        {readableDates(state.text) !== state.text && (
          <button
            className="text-button"
            disabled={save.isPending}
            onClick={() => {
              dispatch({ type: "edit", text: readableDates(state.text) });
              resetFeedback();
            }}
          >
            Make dates readable
          </button>
        )}
        <button
          className="secondary"
          disabled={save.isPending || !dirty || conflict}
          onClick={() => {
            setFeedback("");
            save.mutate(state);
          }}
        >
          {save.isPending ? "Saving…" : "Save draft"}
        </button>
        <button
          className="secondary"
          disabled={!state.text.trim()}
          onClick={() => void copyDraft()}
        >
          Copy draft
        </button>
        <button
          className="secondary"
          disabled={conflict}
          onClick={() => {
            try {
              downloadBrief(data, state.text);
              setFeedback("Brief download requested · nothing sent");
            } catch {
              setFeedback(
                "The brief could not be downloaded. Please try again.",
              );
            }
          }}
        >
          Download brief
        </button>
        {dirty && !conflict && (
          <button
            className="text-button"
            disabled={save.isPending}
            onClick={() => setDiscarding(true)}
          >
            Discard edits
          </button>
        )}
        <span role="status">
          {feedback ||
            (save.isPending
              ? "Saving draft…"
              : dirty
                ? "Unsaved draft edits"
                : save.isSuccess
                  ? "Draft saved · unsent"
                  : "For your review")}
        </span>
      </div>
      <p className="muted small">
        Copy uses the current editor text. Download includes the brief and its
        supporting quotes. Save draft to keep edits in GhostTab. Unsaved edits
        are kept only while this workspace stays open.
      </p>
      {save.error && (
        <p className="notice error" role="alert">
          {save.error.message}
        </p>
      )}
    </section>
  );
}
