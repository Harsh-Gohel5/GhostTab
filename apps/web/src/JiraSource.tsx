import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { Api } from "./api";
import { jiraKey } from "./jiraLink";

function Failure({ error }: { error: unknown }) {
  return error ? (
    <p role="alert" className="notice error">
      {error instanceof Error
        ? error.message
        : "Jira request could not finish. Please retry."}
    </p>
  ) : null;
}

function useJira(api: Api, owner: string) {
  return useQuery({
    queryKey: ["source-connection", owner, "jira"],
    queryFn: () => api.jiraConnection(),
  });
}

export function JiraConnection({ api, owner }: { api: Api; owner: string }) {
  const status = useJira(api, owner);
  const cache = useQueryClient();
  const [confirm, setConfirm] = useState(false);
  const connect = useMutation({
    mutationFn: () => api.connectJira(),
    onSuccess: ({ url }) => window.location.assign(url),
  });
  const disconnect = useMutation({
    mutationFn: () => api.disconnectJira(),
    onSuccess: () => {
      setConfirm(false);
      cache.removeQueries({ queryKey: ["workspace", owner] });
      cache.removeQueries({ queryKey: ["jira-sites", owner] });
      void cache.invalidateQueries({ queryKey: ["tasks", owner] });
      void status.refetch();
    },
  });
  return (
    <section className="form-panel" aria-label="Jira connection">
      <h2>Jira</h2>
      <p>
        Bring a selected Jira Cloud issue into your workspace. Editing issues,
        comments and attachments are excluded.
      </p>
      <p className="muted">
        {status.isPending
          ? "Checking connection…"
          : status.data?.connected
            ? "Connected · selected issues · read only"
            : "Not connected · authorize when you’re ready"}
      </p>
      <p className="muted">
        Jira grants read access within authorized sites and your account
        permissions. GhostTab reads only issues you select when importing or
        checking them. Selected text may be sent to Meta when you request
        preparation.
      </p>
      {status.isError ? (
        <button className="secondary" onClick={() => void status.refetch()}>
          Retry Jira status
        </button>
      ) : status.data?.connected ? (
        <>
          {!confirm ? (
            <button className="secondary" onClick={() => setConfirm(true)}>
              Disconnect Jira
            </button>
          ) : (
            <div role="group" aria-label="Confirm disconnect Jira">
              <p>
                Disconnecting removes stored Jira credentials and blocks
                imported Jira sources and dependent briefs.
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
          {connect.isPending ? "Opening Jira…" : "Connect Jira"}
        </button>
      )}
      {status.data && !status.data.configured && (
        <p className="muted">Jira setup is pending. See docs/jira-source.md.</p>
      )}
      <Failure error={status.error || connect.error || disconnect.error} />
    </section>
  );
}

export function JiraImport({
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
  const status = useJira(api, owner);
  const [siteId, setSiteId] = useState("");
  const [link, setLink] = useState("");
  const [feedback, setFeedback] = useState("");
  const sites = useQuery({
    queryKey: ["jira-sites", owner],
    queryFn: () => api.jiraSites(),
    enabled: false,
  });
  const importing = useMutation({
    mutationFn: () => {
      const site = sites.data?.sites.find((item) => item.id === siteId);
      if (!site)
        throw new Error("Load and choose an authorized Jira site first.");
      return api.importJira(task, {
        cloud_id: site.id,
        issue_key: jiraKey(link, site.url),
      });
    },
    onSuccess: () => {
      setLink("");
      setFeedback(
        "Jira issue saved. Review its context before preparing or updating the brief.",
      );
      onImported();
    },
  });
  return (
    <details className="form-panel">
      <summary>Add a Jira issue</summary>
      <p className="muted">
        Load your authorized sites, then choose one issue. GhostTab reads its
        title, description and status. Selected text may enter Meta preparation.
      </p>
      {status.data?.connected ? (
        <>
          <button
            className="secondary"
            disabled={sites.isFetching || importing.isPending}
            onClick={() => {
              setSiteId("");
              void sites.refetch().then(() => onImported());
            }}
          >
            {sites.isFetching ? "Loading sites…" : "Load authorized Jira sites"}
          </button>
          {sites.data && (
            <form
              onSubmit={(event) => {
                event.preventDefault();
                setFeedback("");
                importing.mutate();
              }}
            >
              <label>
                Jira site
                <select
                  value={siteId}
                  onChange={(event) => setSiteId(event.target.value)}
                  required
                >
                  <option value="">Choose an authorized site</option>
                  {sites.data.sites.map((site) => (
                    <option key={site.id} value={site.id}>
                      {site.name} · {site.url}
                    </option>
                  ))}
                </select>
              </label>
              {sites.data.sites.length === 0 && (
                <p>
                  No readable sites remain. Reconnect Jira to authorize a site.
                </p>
              )}
              {sites.data.has_more && (
                <p>Showing the first 50 authorized sites.</p>
              )}
              <label>
                Jira issue key or link
                <input
                  value={link}
                  onChange={(event) => setLink(event.target.value)}
                  maxLength={2048}
                  placeholder="DEMO-42"
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
                disabled={
                  blocked ||
                  sites.isFetching ||
                  sites.isError ||
                  !siteId ||
                  importing.isPending
                }
              >
                {importing.isPending ? "Importing…" : "Import Jira issue"}
              </button>
            </form>
          )}
        </>
      ) : (
        <p>
          {status.isPending
            ? "Checking Jira connection…"
            : "Connect Jira in Connections when you’re ready."}
        </p>
      )}
      {feedback && <p role="status">{feedback}</p>}
      <Failure error={status.error || sites.error || importing.error} />
    </details>
  );
}
