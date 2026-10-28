export type DraftRevision = { snapshotId: string; text: string };
export type DraftState = DraftRevision & { base: string };
export type DraftAction =
  | { type: "edit"; text: string }
  | { type: "receive" | "use-latest" | "keep-edits"; remote: DraftRevision }
  | { type: "saved"; remote: DraftRevision; expectedDraft: string };

export const initialDraft = (remote: DraftRevision): DraftState => ({
  ...remote,
  base: remote.text,
});
export const isDraftDirty = (state: DraftState) => state.text !== state.base;
export const hasDraftConflict = (state: DraftState, remote: DraftRevision) =>
  state.snapshotId !== remote.snapshotId || state.base !== remote.text;

export function draftReducer(
  state: DraftState,
  action: DraftAction,
): DraftState {
  switch (action.type) {
    case "edit":
      return { ...state, text: action.text };
    case "receive":
      // Refetches and new briefs may replace clean text, never unsaved edits.
      if (
        isDraftDirty(state) &&
        !(
          state.snapshotId === action.remote.snapshotId &&
          state.text === action.remote.text
        )
      )
        return state;
      if (!hasDraftConflict(state, action.remote)) return state;
      return initialDraft(action.remote);
    case "saved":
      // A response acknowledges the submitted text, including edits made in flight.
      if (
        state.snapshotId !== action.remote.snapshotId ||
        state.base !== action.expectedDraft
      )
        return state;
      return { ...state, base: action.remote.text };
    case "use-latest":
      return initialDraft(action.remote);
    case "keep-edits":
      return { ...initialDraft(action.remote), text: state.text };
  }
}
