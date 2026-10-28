export type PreparationState =
  "ready" | "offline" | "disabled" | "unconfigured" | "budget_exhausted";

export function preparationMessage(state: PreparationState) {
  switch (state) {
    case "ready":
      return {
        title: "Preparation service available",
        message:
          "The service reported recently. This does not verify Meta access or guarantee a successful preparation.",
      };
    case "offline":
      return {
        title: "Preparation service has not reported recently",
        message:
          "New preparation is paused here. Existing requests stay saved and resume when the service returns. You can still review briefs and edit drafts.",
      };
    case "disabled":
      return {
        title: "AI preparation is paused",
        message:
          "Preparation is disabled in server settings. Saved notes, briefs and drafts remain available.",
      };
    case "unconfigured":
      return {
        title: "Preparation needs server configuration",
        message:
          "Ask the workspace owner to check the server's Meta setup. No credentials belong in this interface.",
      };
    case "budget_exhausted":
      return {
        title: "Application preparation budget reached",
        message:
          "Ask the workspace owner to review estimated usage and credit controls. Saved content remains available; retrying will not restore budget.",
      };
  }
}
