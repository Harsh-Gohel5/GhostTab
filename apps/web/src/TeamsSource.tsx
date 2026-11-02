import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { Api } from "./api";
import { teamsChat } from "./teamsLink";

function Failure({ error }: { error: unknown }) {
  return error ? (
    <p role="alert" className="notice error">
      {error instanceof Error
        ? error.message
        : "Teams request could not finish. Please retry."}
    </p>
  ) : null;
}

function useTeams(api: Api, owner: string) {
  return useQuery({
    queryKey: ["source-connection", owner, "teams"],
    queryFn: () => api.teamsConnection(),
  });
}

export function TeamsConnection({ api, owner }: { api: Api; owner: string }) {
  const status = useTeams(api, owner);
  const cache = useQueryClient();
  const [confirm, setConfirm] = useState(false);
  const connect = useMutation({
    mutationFn: () => api.connectTeams(),
    onSuccess: ({ url }) => window.location.assign(url),
  });
  const disconnect = useMutation({
    mutationFn: () => api.disconnectTeams(),
    onSuccess: () => {
      setConfirm(false);
      cache.removeQueries({ queryKey: ["workspace", owner] });
      void cache.invalidateQueries({ queryKey: ["tasks", owner] });
      void status.refetch();
    },
  });
  return (
    <section className="form-panel" aria-label="Teams connection">
      <h2>Teams</h2>
      <p>
        Bring one selected work or school chat into your workspace. Channels,
        files and sending are excluded.
      </p>
      <p className="muted">
        {status.isPending
          ? "Checking connection…"
          : status.data?.connected
            ? "Connected · selected chats · read only"
            : "Not connected · authorize when you’re ready"}
      </p>
      <p className="muted">
        Teams grants read access to chats you belong to. GhostTab reads only the
        chat you select when importing or checking it. Selected text may be sent
        to Meta when you request preparation.
      </p>
      {status.isError ? (
        <button className="secondary" onClick={() => void status.refetch()}>
          Retry Teams status
        </button>
      ) : status.data?.connected ? (
        <>
          {!confirm ? (
            <button className="secondary" onClick={() => setConfirm(true)}>
              Disconnect Teams
            </button>
          ) : (
            <div role="group" aria-label="Confirm disconnect Teams">
              <p>
                Disconnecting removes stored Teams credentials and blocks
                imported Teams sources and dependent briefs.
              </p>
              <button
                className="secondary"
                disabled={disconnect.isPending}
                onClick={() => disconnect.mutate()}
              >
                Confirm disconnect
              </button>{" "}
              <button
                className="text-button"
                disabled={disconnect.isPending}
                onClick={() => setConfirm(false)}
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
          {connect.isPending ? "Opening Teams…" : "Connect to Microsoft Teams"}
        </button>
      )}
      {status.data && !status.data.configured && (
        <p className="muted">
          Teams setup is pending. See docs/teams-source.md.
        </p>
      )}
      <Failure error={status.error || connect.error || disconnect.error} />
    </section>
  );
}

export function TeamsImport({
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
  const status = useTeams(api, owner);
  const [link, setLink] = useState("");
  const [feedback, setFeedback] = useState("");
  const importing = useMutation({
    mutationFn: () => api.importTeams(task, teamsChat(link)),
    onSuccess: () => {
      setLink("");
      setFeedback(
        "Teams chat saved. Review its context before preparing or updating the brief.",
      );
      onImported();
    },
  });
  return (
    <details className="form-panel">
      <summary>Add a Teams chat</summary>
      <p className="muted">
        Choose a chat from the connected work or school account. Only its latest
        50 messages are read; larger chats are labeled incomplete. Selected
        content may enter Meta preparation.
      </p>
      {status.data?.connected ? (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            setFeedback("");
            importing.mutate();
          }}
        >
          <label>
            Teams chat link or ID
            <input
              type="text"
              value={link}
              onChange={(event) => setLink(event.target.value)}
              placeholder="19:your-chat@thread.v2"
              maxLength={2048}
              required
            />
          </label>
          {blocked && (
            <p role="status">
              Save or discard draft edits before importing context.
            </p>
          )}
          <button
            className="secondary"
            disabled={blocked || importing.isPending}
          >
            {importing.isPending ? "Importing…" : "Import Teams chat"}
          </button>
        </form>
      ) : (
        <p>
          {status.isPending
            ? "Checking Teams connection…"
            : "Connect Teams in Connections when you’re ready."}
        </p>
      )}
      {feedback && <p role="status">{feedback}</p>}
      <Failure error={status.error || importing.error} />
    </details>
  );
}
