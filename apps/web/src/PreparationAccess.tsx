import type { PreparationReadiness } from "./api";
import { preparationMessage } from "./preparationReadiness";

export function PreparationAccess({
  status,
  error,
  onCheck,
}: {
  status?: PreparationReadiness;
  error: unknown;
  onCheck: () => void;
}) {
  const info = status ? preparationMessage(status.state) : null;
  return (
    <section
      className={`notice ${status?.state === "ready" ? "" : "stale"}`}
      aria-label="Preparation availability"
    >
      <div role="status">
        <strong>
          {error
            ? "Preparation availability could not be checked"
            : (info?.title ?? "Checking preparation availability…")}
        </strong>
        <p>
          {error
            ? "The last service status may be outdated. Check the connection and retry. Saved content remains available."
            : info?.message}
        </p>
      </div>
      <button className="text-button" onClick={onCheck}>
        Check again
      </button>
    </section>
  );
}
