import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { Api } from "./api";
import { slackSelection } from "./slackLink";

function Failure({ error }: { error: unknown }) {
  return error ? (
    <p role="alert" className="notice error">
      {error instanceof Error
        ? error.message
        : "Slack request could not finish. Please retry."}
    </p>
  ) : null;
}

function useSlack(api: Api, owner: string) {
  return useQuery({
    queryKey: ["source-connection", owner, "slack"],
    queryFn: () => api.slackConnection(),
  });
}

export function SlackConnection({ api, owner }: { api: Api; owner: string }) {
  const status = useSlack(api, owner);
  const cache = useQueryClient();
  const [confirm, setConfirm] = useState(false);
  const connect = useMutation({
    mutationFn: () => api.connectSlack(),
    onSuccess: ({ url }) => window.location.assign(url),
  });
  const disconnect = useMutation({
    mutationFn: () => api.disconnectSlack(),
    onSuccess: () => {
      setConfirm(false);
      cache.removeQueries({ queryKey: ["workspace", owner] });
      void cache.invalidateQueries({ queryKey: ["tasks", owner] });
      void status.refetch();
    },
  });
  return (
    <section className="form-panel" aria-label="Slack connection">
      <h2>Slack</h2>
      <p>
        Bring a selected public-channel thread into your workspace. Private
        channels, DMs, files and sending are excluded.
      </p>
      <p className="muted">
        {status.isPending
          ? "Checking connection…"
          : status.data?.connected
            ? "Connected · public threads · read only"
            : "Not connected · authorize when you’re ready"}
      </p>
      <p className="muted">
        Slack grants public-channel read access. GhostTab reads only the thread
        you select when importing or checking it. Selected text may be sent to
        Meta when you request preparation.
      </p>
      {status.isError ? (
        <button className="secondary" onClick={() => void status.refetch()}>
          Retry Slack status
        </button>
      ) : status.data?.connected ? (
        <>
          {!confirm ? (
            <button className="secondary" onClick={() => setConfirm(true)}>
              Disconnect Slack
            </button>
          ) : (
            <div role="group" aria-label="Confirm disconnect Slack">
              <p>
                Disconnecting removes stored Slack credentials and blocks
                imported Slack sources and dependent briefs.
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
          {connect.isPending ? "Opening Slack…" : "Connect Slack"}
        </button>
      )}
      {status.data && !status.data.configured && (
        <p className="muted">
          Slack setup is pending. See docs/slack-source.md.
        </p>
      )}
      <Failure error={status.error || connect.error || disconnect.error} />
    </section>
  );
}

export function SlackImport({
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
  const status = useSlack(api, owner);
  const [link, setLink] = useState("");
  const [feedback, setFeedback] = useState("");
  const importing = useMutation({
    mutationFn: () => api.importSlack(task, slackSelection(link)),
    onSuccess: () => {
      setLink("");
      setFeedback(
        "Slack thread saved. Review its context before preparing or updating the brief.",
      );
      onImported();
    },
  });
  return (
    <details className="form-panel">
      <summary>Add a Slack thread</summary>
      <p className="muted">
        Choose a public-channel thread from the connected workspace. Only its
        first 15 messages are read; larger threads are labeled incomplete.
        Selected content may enter Meta preparation.
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
            Slack message link
            <input
              type="url"
              value={link}
              onChange={(event) => setLink(event.target.value)}
              placeholder="https://your-workspace.slack.com/archives/…"
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
            {importing.isPending ? "Importing…" : "Import Slack thread"}
          </button>
        </form>
      ) : (
        <p>
          {status.isPending
            ? "Checking Slack connection…"
            : "Connect Slack in Connections when you’re ready."}
        </p>
      )}
      {feedback && <p role="status">{feedback}</p>}
      <Failure error={status.error || importing.error} />
    </details>
  );
}
