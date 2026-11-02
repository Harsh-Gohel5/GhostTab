import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { Api, GoogleProvider } from "./api";

const providers = [
  {
    id: "google_docs",
    name: "Google Docs",
    description:
      "Import a document you choose by its link. No document edits or Drive browsing.",
  },
  {
    id: "gmail",
    name: "Gmail",
    description:
      "Search up to five messages at a time and import only the message you choose. No sending or attachment downloads.",
  },
] as const;

function SourceError({ error }: { error: unknown }) {
  return error ? (
    <p className="notice error" role="alert">
      {error instanceof Error
        ? error.message
        : "Source request failed. Please retry."}
    </p>
  ) : null;
}

export function GoogleConnection({
  api,
  owner,
  provider,
}: {
  api: Api;
  owner: string;
  provider: GoogleProvider;
}) {
  const cache = useQueryClient();
  const info = providers.find((item) => item.id === provider)!;
  const status = useQuery({
    queryKey: ["source-connection", owner, provider],
    queryFn: () => api.sourceConnection(provider),
  });
  const [confirmDisconnect, setConfirmDisconnect] = useState(false);
  const connect = useMutation({
    mutationFn: () => api.connectSource(provider),
    onSuccess: ({ url }) => window.location.assign(url),
  });
  const disconnect = useMutation({
    mutationFn: () => api.disconnectSource(provider),
    onSuccess: () => {
      setConfirmDisconnect(false);
      cache.removeQueries({ queryKey: ["workspace", owner] });
      cache.removeQueries({ queryKey: ["mail-search", owner] });
      void cache.invalidateQueries({ queryKey: ["tasks", owner] });
      void status.refetch();
    },
  });
  return (
    <section className="form-panel" aria-label={`${info.name} connection`}>
      <h2>{info.name}</h2>
      <p>{info.description}</p>
      <p className="muted">
        {status.isPending
          ? "Checking connection…"
          : status.data?.connected
            ? "Connected · read only"
            : "Not connected · authorization can be completed later"}
      </p>
      <p className="muted">
        Google grants account-level read access for this service. GhostTab reads
        content only when you search, import, or check a source. Imported
        content may be sent to Meta when you request preparation.
      </p>
      {status.isError ? (
        <button className="secondary" onClick={() => void status.refetch()}>
          Retry connection status
        </button>
      ) : status.data?.connected ? (
        <>
          {!confirmDisconnect ? (
            <button
              className="secondary"
              onClick={() => setConfirmDisconnect(true)}
            >
              Disconnect {info.name}
            </button>
          ) : (
            <div role="group" aria-label={`Confirm disconnect ${info.name}`}>
              <p>
                Disconnecting removes stored credentials and blocks this
                service’s imported sources and dependent briefs. Google account
                permissions can also be removed in your Google account.
              </p>
              <button
                className="secondary"
                disabled={disconnect.isPending}
                onClick={() => disconnect.mutate()}
              >
                {disconnect.isPending ? "Disconnecting…" : "Confirm disconnect"}
              </button>{" "}
              <button
                className="text-button"
                disabled={disconnect.isPending}
                onClick={() => setConfirmDisconnect(false)}
              >
                Cancel
              </button>
            </div>
          )}
        </>
      ) : (
        <button
          className="secondary"
          disabled={!status.data?.configured || connect.isPending}
          onClick={() => connect.mutate()}
        >
          {connect.isPending ? "Opening Google…" : `Connect to ${info.name}`}
        </button>
      )}
      {status.data && !status.data.configured && (
        <p className="muted">
          Server setup is pending. See docs/google-sources.md.
        </p>
      )}
      <SourceError error={status.error || connect.error || disconnect.error} />
    </section>
  );
}

export function GoogleSourceImport({
  api,
  owner,
  task,
  blocked,
  onImported,
}: {
  api: Api;
  owner: string;
  task: string;
  blocked: boolean;
  onImported: () => void;
}) {
  const docs = useQuery({
    queryKey: ["source-connection", owner, "google_docs"],
    queryFn: () => api.sourceConnection("google_docs"),
  });
  const gmail = useQuery({
    queryKey: ["source-connection", owner, "gmail"],
    queryFn: () => api.sourceConnection("gmail"),
  });
  const [document, setDocument] = useState("");
  const [query, setQuery] = useState("");
  const [selectionError, setSelectionError] = useState("");
  const [feedback, setFeedback] = useState("");
  const search = useMutation({
    mutationFn: (value: string) => api.searchMail(value),
  });
  const importing = useMutation({
    mutationFn: ({ provider, id }: { provider: GoogleProvider; id: string }) =>
      api.importSource(task, provider, id),
    onSuccess: () => {
      setFeedback(
        "Source saved. Review its context before preparing or updating the brief.",
      );
      setDocument("");
      search.reset();
      onImported();
    },
  });
  const busy = blocked || importing.isPending;
  const importDocument = () => {
    setSelectionError("");
    setFeedback("");
    let id = document.trim();
    if (id.startsWith("https://")) {
      try {
        const url = new URL(id);
        id =
          url.origin === "https://docs.google.com"
            ? (url.pathname.match(
                /^\/document\/d\/([A-Za-z0-9_-]+)(?:\/|$)/,
              )?.[1] ?? "")
            : "";
      } catch {
        id = "";
      }
    }
    if (!/^[A-Za-z0-9_-]{1,256}$/.test(id)) {
      setSelectionError("Paste a Google Docs document link or document ID.");
      return;
    }
    importing.mutate({ provider: "google_docs", id });
  };
  return (
    <details className="form-panel">
      <summary>Add Google Docs or Gmail context</summary>
      <p className="muted">
        Connect these services in Connections when you’re ready. Only selected
        items become workspace sources. Preparation may send imported text to
        Meta; use permitted test content.
      </p>
      {blocked && (
        <p role="status">
          Save or discard draft edits before importing context.
        </p>
      )}
      <h3>Google Docs</h3>
      {docs.data?.connected ? (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            importDocument();
          }}
        >
          <label>
            Document link or ID
            <input
              value={document}
              onChange={(event) => setDocument(event.target.value)}
              maxLength={2048}
              placeholder="https://docs.google.com/document/d/…"
              required
            />
          </label>
          <button className="secondary" disabled={busy}>
            Import document
          </button>
        </form>
      ) : (
        <p>
          Google Docs is{" "}
          {docs.isPending
            ? "checking its connection…"
            : "not connected. Authorize it later in Connections."}
        </p>
      )}
      <h3>Gmail</h3>
      {gmail.data?.connected ? (
        <>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              setFeedback("");
              search.mutate(query.trim());
            }}
          >
            <label>
              Search Gmail
              <input
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                  search.reset();
                }}
                maxLength={200}
                required
                placeholder="Subject, sender, or Gmail search terms"
              />
            </label>
            <button
              className="secondary"
              disabled={busy || search.isPending || !query.trim()}
            >
              {search.isPending ? "Searching…" : "Find messages"}
            </button>
          </form>
          {search.data && (
            <div aria-live="polite">
              <p>
                {search.data.messages.length} messages found.
                {search.data.has_more &&
                  " More results exist; narrow your search."}
              </p>
              {search.data.messages.map((message) => (
                <p key={message.id}>
                  <strong>{message.title}</strong>{" "}
                  <button
                    className="text-button"
                    disabled={busy}
                    onClick={() => {
                      setFeedback("");
                      importing.mutate({ provider: "gmail", id: message.id });
                    }}
                  >
                    Import this message
                  </button>
                </p>
              ))}
            </div>
          )}
        </>
      ) : (
        <p>
          Gmail is{" "}
          {gmail.isPending
            ? "checking its connection…"
            : "not connected. Authorize it later in Connections."}
        </p>
      )}
      {importing.isPending && <p role="status">Importing selected source…</p>}
      {selectionError && (
        <p className="notice error" role="alert">
          {selectionError}
        </p>
      )}
      {feedback && <p role="status">{feedback}</p>}
      <SourceError
        error={docs.error || gmail.error || search.error || importing.error}
      />
    </details>
  );
}
