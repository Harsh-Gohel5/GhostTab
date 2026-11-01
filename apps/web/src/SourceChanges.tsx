import type { SourceChange } from "./api";
import { readableCalendar, readableDates } from "./dates";
import { sourceDiff } from "./sourceDiff";

const sections = { summary: "Brief", fact: "Fact", next_step: "Next step" };

export function SourceChanges({
  changes,
  onUpdate,
  disabled,
  busy,
}: {
  changes: SourceChange[];
  onUpdate: () => void;
  disabled: boolean;
  busy: boolean;
}) {
  if (!changes.length) return null;
  return (
    <section
      className="source-changes form-panel"
      aria-label="Source changes since the brief"
    >
      <div className="section-heading">
        <h2>What changed since this brief</h2>
        <span className="badge">
          {changes.length} {changes.length === 1 ? "source" : "sources"}
        </span>
      </div>
      <p>
        Compare the saved versions and review the claims that cite them. Changes
        are detected when you check a source or edit saved context.
      </p>
      <p className="muted">
        A source update does not prove that every cited claim changed meaning.
        The previous brief and its quotes remain available until you update it.
      </p>
      {changes.map((change) => {
        const { current, previous } = change;
        const readable = (text: string) =>
          current.origin === "google_calendar" ? readableCalendar(text) : text;
        return (
          <details className="source-change" key={current.id}>
            <summary>
              {current.title} ·{" "}
              {change.kind === "added" ? "Added since preparation" : "Updated"}{" "}
              · {change.claims_to_review.length} cited{" "}
              {change.claims_to_review.length === 1 ? "claim" : "claims"} to
              review
            </summary>
            <p className="muted small">
              Changed:{" "}
              {change.changed_fields
                .map((field) =>
                  field === "url"
                    ? "source link"
                    : field === "content"
                      ? "text"
                      : field,
                )
                .join(", ")}
            </p>
            {previous ? (
              <>
                <div className="source-version-grid">
                  <section>
                    <h3>Used in the previous brief</h3>
                    <strong>{previous.title}</strong>
                    {previous.url && (
                      <p className="source-link-text">{previous.url}</p>
                    )}
                    <pre>{readable(previous.content)}</pre>
                  </section>
                  <section>
                    <h3>Current saved source</h3>
                    <strong>{current.title}</strong>
                    {current.url && (
                      <p className="source-link-text">{current.url}</p>
                    )}
                    <pre>{readable(current.content)}</pre>
                  </section>
                </div>
                {change.changed_fields.includes("content") && (
                  <details>
                    <summary>Show text changes</summary>
                    <p className="muted small">
                      − Previous text · + Current text. Long documents may show
                      whole versions instead of individual lines.
                    </p>
                    <pre className="source-diff">
                      {sourceDiff(
                        readable(previous.content),
                        readable(current.content),
                      ).map((line, index) => (
                        <span className={`diff-${line.kind}`} key={index}>
                          {line.kind === "removed"
                            ? "− "
                            : line.kind === "added"
                              ? "+ "
                              : "  "}
                          {line.text}
                          {"\n"}
                        </span>
                      ))}
                    </pre>
                  </details>
                )}
              </>
            ) : (
              <p>
                This source was not included in the saved brief. Update the
                brief to consider it with the other sources.
              </p>
            )}
            <h3>Claims to review</h3>
            {change.claims_to_review.length ? (
              <ul className="changed-claims">
                {change.claims_to_review.map((claim, index) => (
                  <li key={index}>
                    <span className="badge">{sections[claim.section]}</span>
                    <p>{readableDates(claim.text)}</p>
                    <details>
                      <summary>Exact quotes used previously</summary>
                      {claim.quotes.map((quote, i) => (
                        <blockquote key={i}>{quote}</blockquote>
                      ))}
                    </details>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted">
                No saved summary, fact or next-step citation points to this
                source. The draft and open questions are not individually
                citation-linked; review them after updating.
              </p>
            )}
          </details>
        );
      })}
      <p className="muted small">
        Updating uses the existing Meta preparation workflow. Save or discard
        draft edits first. The action stays unavailable while preparation is
        busy or the service cannot accept it.
      </p>
      <button className="primary" disabled={disabled} onClick={onUpdate}>
        {busy ? "Preparing…" : "Update brief with current context"}
      </button>
    </section>
  );
}
