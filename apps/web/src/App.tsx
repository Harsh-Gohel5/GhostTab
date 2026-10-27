import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { createClient } from "@supabase/supabase-js";
import type { Session } from "@supabase/supabase-js";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Api, configSchema } from "./api";
import { PreparationStatus } from "./PreparationStatus";
import type {
  Config,
  Evidence,
  Point,
  SourceInput,
  Task,
  Workspace,
} from "./api";

function GhostMark() {
  return (
    <svg viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <path
        d="M7 26V14a9 9 0 0 1 18 0v12l-4-3-5 3-5-3-4 3Z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      />
      <circle cx="12.5" cy="14" r="1.5" fill="currentColor" />
      <circle cx="19.5" cy="14" r="1.5" fill="currentColor" />
    </svg>
  );
}
function ErrorNotice({ error }: { error: unknown }) {
  return error ? (
    <p className="notice error" role="alert">
      {error instanceof Error
        ? error.message
        : "Something went wrong. Please retry."}
    </p>
  ) : null;
}
function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="panel">
      <h2>{title}</h2>
      {children}
    </section>
  );
}

export default function App() {
  const config = useQuery({
    queryKey: ["config"],
    queryFn: () => new Api().request("/config", configSchema),
    retry: 1,
  });
  if (!config.data)
    return (
      <main className="startup">
        <span className="brand-mark">
          <GhostMark />
        </span>
        <h1>Make room for the work.</h1>
        {config.isError ? (
          <>
            <ErrorNotice error={config.error} />
            <button onClick={() => void config.refetch()}>
              Retry connection
            </button>
          </>
        ) : (
          <p role="status">Opening your workspace…</p>
        )}
      </main>
    );
  return <SessionGate config={config.data} />;
}

function SessionGate({ config }: { config: Config }) {
  const client = useMemo(
    () =>
      config.auth_mode === "supabase"
        ? createClient(config.supabase_url, config.supabase_publishable_key)
        : null,
    [config],
  );
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(!client);
  const [authError, setAuthError] = useState("");
  const queryClient = useQueryClient();
  useEffect(() => {
    if (!client) return;
    let active = true;
    let previousUser: string | undefined;
    void client.auth.getSession().then(({ data, error }) => {
      if (active) {
        setSession(data.session);
        setReady(true);
        if (error) setAuthError(error.message);
      }
    });
    const { data } = client.auth.onAuthStateChange((_event, value) => {
      if (previousUser !== value?.user.id) {
        queryClient.removeQueries({
          predicate: (query) => query.queryKey[0] !== "config",
        });
        previousUser = value?.user.id;
      }
      setSession(value);
      setReady(true);
    });
    return () => {
      active = false;
      data.subscription.unsubscribe();
    };
  }, [client, queryClient]);
  const api = useMemo(
    () =>
      new Api(
        client
          ? async () => {
              const { data, error } = await client.auth.getSession();
              if (error || !data.session)
                throw new Error("Please sign in again.");
              return data.session.access_token;
            }
          : undefined,
      ),
    [client],
  );
  if (!ready)
    return (
      <main className="startup" role="status">
        Restoring your session…
      </main>
    );
  if (client && !session)
    return (
      <main className="startup">
        <span className="brand-mark">
          <GhostMark />
        </span>
        <h1>Welcome to GhostTab.</h1>
        <p>Sign in to your private workspace.</p>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            const form = new FormData(event.currentTarget);
            void client.auth
              .signInWithPassword({
                email: String(form.get("email")),
                password: String(form.get("password")),
              })
              .then(({ error }) => setAuthError(error?.message ?? ""));
          }}
        >
          <label>
            Email
            <input name="email" type="email" autoComplete="username" required />
          </label>
          <label>
            Password
            <input
              name="password"
              type="password"
              autoComplete="current-password"
              required
            />
          </label>
          <button className="primary">Sign in</button>
        </form>
        {authError && <p role="alert">{authError}</p>}
      </main>
    );
  return (
    <Home
      key={session?.user.id ?? "local"}
      api={api}
      config={config}
      owner={session?.user.id ?? "local"}
      onSignOut={
        client
          ? () => {
              void client.auth.signOut();
            }
          : undefined
      }
    />
  );
}

type Page = "Today" | "Workspaces" | "Connections";
function Home({
  api,
  config,
  owner,
  onSignOut,
}: {
  api: Api;
  config: Config;
  owner: string;
  onSignOut?: () => void;
}) {
  const queryClient = useQueryClient();
  const [page, setPage] = useState<Page>("Today");
  const [selected, setSelected] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [feedback, setFeedback] = useState(() =>
    new URLSearchParams(location.search).get("calendar") === "connection_failed"
      ? "Calendar was not connected. Check the setup and try again."
      : "",
  );
  const tasks = useQuery({
    queryKey: ["tasks", owner],
    queryFn: () => api.tasks(),
  });
  const connections = useQuery({
    queryKey: ["connections", owner],
    queryFn: () => api.connections(),
  });
  const connected = connections.data?.google_calendar === "connected";
  const events = useQuery({
    queryKey: ["events", owner],
    queryFn: () => api.events(),
    enabled: connected && page === "Today",
    retry: false,
    staleTime: 60000,
  });
  const refresh = () => {
    void queryClient.invalidateQueries({ queryKey: ["tasks", owner] });
    void queryClient.invalidateQueries({ queryKey: ["connections", owner] });
  };
  const create = useMutation({
    mutationFn: ({ title, goal }: { title: string; goal: string }) =>
      api.createTask(title, goal),
    onSuccess: (task) => {
      setSelected(task.id);
      setCreating(false);
      setPage("Workspaces");
      refresh();
    },
  });
  const importMeeting = useMutation({
    mutationFn: (id: string) => api.importEvent(id),
    onSuccess: (task) => {
      setSelected(task.id);
      setPage("Workspaces");
      refresh();
    },
  });
  const connect = useMutation({
    mutationFn: () => api.connect(),
    onSuccess: ({ url }) => {
      window.location.assign(url);
    },
  });
  const disconnect = useMutation({
    mutationFn: () => api.disconnect(),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: ["events", owner] });
      queryClient.removeQueries({ queryKey: ["workspace", owner] });
      refresh();
      setFeedback(
        "Calendar disconnected. Imported calendar context is blocked from prepared briefs.",
      );
    },
  });
  const open = (task: Task) => {
    setSelected(task.id);
    setPage("Workspaces");
  };
  const date = new Intl.DateTimeFormat(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
  }).format(new Date());
  return (
    <div className="shell">
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          onClick={(event) => {
            event.preventDefault();
            setPage("Today");
          }}
        >
          <span className="brand-mark">
            <GhostMark />
          </span>
          GhostTab
        </a>
        <p className="sidebar-label">A LITTLE MORE HEADSPACE</p>
        <nav aria-label="Main navigation">
          {(["Today", "Workspaces", "Connections"] as Page[]).map((item, i) => (
            <button
              key={item}
              className={`nav-item ${page === item ? "selected" : ""}`}
              aria-current={page === item ? "page" : undefined}
              onClick={() => {
                setPage(item);
                if (item === "Workspaces") setSelected(null);
              }}
            >
              <span aria-hidden="true">{["◷", "▦", "⌁"][i]}</span>
              {item}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          <span aria-hidden="true">✧</span>
          <p>
            Less gathering.
            <br />
            More getting somewhere.
          </p>
        </div>
        <div className="sidebar-footer">
          <span className="avatar">
            {config.auth_mode === "local" ? "L" : "Y"}
          </span>
          <div>
            {config.auth_mode === "local"
              ? "Local workspace"
              : "Your private space"}
            <small>
              {config.auth_mode === "local"
                ? "Saved on this computer"
                : "Signed in securely"}
            </small>
          </div>
          {onSignOut && (
            <button className="text-button" onClick={onSignOut}>
              Sign out
            </button>
          )}
        </div>
      </aside>
      <div className="main-column">
        <header className="topbar">
          <span>
            Your space <span className="slash">/</span> <strong>{page}</strong>
          </span>
          <span className="quiet-label">
            <span className="status-dot" /> One thing at a time
          </span>
        </header>
        <main className="content">
          <ErrorNotice error={tasks.error || connections.error} />
          {feedback && (
            <p className="notice" role="status">
              {feedback}
              <button className="text-button" onClick={() => setFeedback("")}>
                Dismiss
              </button>
            </p>
          )}
          {page === "Today" && (
            <>
              <p className="eyebrow">{date}</p>
              <div className="page-heading">
                <div>
                  <h1>
                    A calmer start
                    <br />
                    <span>to what’s next.</span>
                  </h1>
                  <p>Your meetings and the context to walk into them ready.</p>
                </div>
                <button className="primary" onClick={() => setCreating(true)}>
                  ＋ New workspace
                </button>
              </div>
              <div className="overview-grid">
                <section className="welcome-card">
                  <span className="card-eyebrow">
                    MAKE SPACE FOR THE IMPORTANT PART
                  </span>
                  <h2>Arrive with context.</h2>
                  <p>
                    Choose a meeting. Bring its notes together.
                    <br />
                    Prepare the questions worth asking.
                  </p>
                  <button
                    className="secondary"
                    onClick={() => {
                      if (connected) void events.refetch();
                      else setPage("Connections");
                    }}
                  >
                    {connected
                      ? "Refresh upcoming meetings"
                      : "Connect your calendar"}{" "}
                    <span aria-hidden="true">↗</span>
                  </button>
                  <div className="orb orb-one" />
                  <div className="orb orb-two" />
                </section>
                <section className="small-card">
                  <span className="mini-calendar" aria-hidden="true">
                    ▦
                  </span>
                  <span className="card-eyebrow">YOUR CONTEXT, TOGETHER</span>
                  <h2>
                    {tasks.data?.length ?? "—"}{" "}
                    <span>
                      {tasks.data?.length === 1 ? "workspace" : "workspaces"}
                    </span>
                  </h2>
                  <p>
                    {connected
                      ? "Google Calendar is connected. Choose which event to bring into GhostTab."
                      : "Start with a calendar event, or add a task and notes yourself."}
                  </p>
                  <span className="badge">
                    {connected ? "Calendar connected" : "No calendar connected"}
                  </span>
                </section>
              </div>
              <div className="section-heading">
                <h2>On your calendar</h2>
                <span>Next 14 days · up to 25 events</span>
              </div>
              <ErrorNotice error={events.error || importMeeting.error} />
              {!connected ? (
                <div className="empty-state">
                  <span className="empty-icon" aria-hidden="true">
                    ◷
                  </span>
                  <h3>A little preparation goes a long way.</h3>
                  <p>
                    Connect Google Calendar to choose a meeting.
                    <br />
                    Only the events you select become saved workspaces.
                  </p>
                  <button
                    className="text-button"
                    onClick={() => setPage("Connections")}
                  >
                    Set up Calendar <span aria-hidden="true">→</span>
                  </button>
                </div>
              ) : events.isPending ? (
                <p role="status">Reading upcoming events…</p>
              ) : events.data?.events.length ? (
                <div className="meeting-list">
                  {events.data.events.map((event) => (
                    <article key={event.id} className="meeting-row">
                      <div className="event-symbol" aria-hidden="true">
                        ◷
                      </div>
                      <div>
                        <h3>{event.title}</h3>
                        <p>
                          {event.start.dateTime
                            ? new Intl.DateTimeFormat(undefined, {
                                dateStyle: "medium",
                                timeStyle: "short",
                              }).format(new Date(event.start.dateTime))
                            : `${event.start.date} · All day`}
                        </p>
                      </div>
                      <button
                        className="secondary"
                        disabled={importMeeting.isPending}
                        onClick={() => importMeeting.mutate(event.id)}
                      >
                        Open workspace →
                      </button>
                    </article>
                  ))}
                  {events.data.has_more && (
                    <p className="muted">
                      Showing the first 25 events. More events exist in this
                      period.
                    </p>
                  )}
                </div>
              ) : (
                <div className="empty-state">
                  <h3>A little breathing room.</h3>
                  <p>
                    No upcoming events were found in your primary calendar for
                    this period.
                  </p>
                </div>
              )}
              {!!tasks.data?.length && (
                <>
                  <div className="section-heading">
                    <h2>Pick up where you left off</h2>
                    <button
                      className="text-button"
                      onClick={() => {
                        setPage("Workspaces");
                        setSelected(null);
                      }}
                    >
                      View all →
                    </button>
                  </div>
                  <TaskList tasks={tasks.data.slice(0, 3)} onOpen={open} />
                </>
              )}
            </>
          )}
          {page === "Workspaces" &&
            (selected ? (
              <WorkspaceView
                key={selected}
                id={selected}
                api={api}
                config={config}
                owner={owner}
                onBack={() => {
                  setSelected(null);
                  refresh();
                }}
              />
            ) : (
              <>
                <p className="eyebrow">EVERYTHING IN ITS PLACE</p>
                <div className="page-heading">
                  <div>
                    <h1>Your workspaces.</h1>
                    <p>
                      Meeting context, questions, and a next step you can
                      review.
                    </p>
                  </div>
                  <button className="primary" onClick={() => setCreating(true)}>
                    ＋ New workspace
                  </button>
                </div>
                {tasks.isPending ? (
                  <p role="status">Loading workspaces…</p>
                ) : tasks.data?.length ? (
                  <TaskList tasks={tasks.data} onOpen={open} />
                ) : (
                  <div className="empty-state">
                    <h2>Start with one thing on your mind.</h2>
                    <p>
                      A meeting, a decision, or a request.
                      <br />
                      Add the context you need to move it forward.
                    </p>
                    <button
                      className="secondary"
                      onClick={() => setCreating(true)}
                    >
                      Create your first workspace
                    </button>
                  </div>
                )}
              </>
            ))}
          {page === "Connections" && (
            <>
              <p className="eyebrow">BRING YOUR CONTEXT CLOSER</p>
              <div className="page-heading">
                <div>
                  <h1>A place for your tools.</h1>
                  <p>You choose what GhostTab can read and what to prepare.</p>
                </div>
              </div>
              <div className="connection-card">
                <span className="calendar-logo" aria-hidden="true">
                  31
                </span>
                <div>
                  <h2>Google Calendar</h2>
                  <p>
                    Read upcoming events from your primary calendar.
                    <br />
                    Select a meeting to save its time, location, and
                    description.
                  </p>
                  <span className="badge">
                    {connected
                      ? "Connected · read only"
                      : "Read only · selected meetings"}
                  </span>
                </div>
                {connected ? (
                  <button
                    className="secondary"
                    disabled={disconnect.isPending}
                    onClick={() => disconnect.mutate()}
                  >
                    Disconnect
                  </button>
                ) : (
                  <button
                    className="primary"
                    disabled={connect.isPending || !config.calendar_configured}
                    onClick={() => connect.mutate()}
                  >
                    {connect.isPending ? "Opening Google…" : "Connect Calendar"}
                  </button>
                )}
              </div>
              <ErrorNotice error={connect.error || disconnect.error} />
              {!config.calendar_configured && (
                <p className="notice">
                  Calendar setup is pending. Follow <code>docs/setup.md</code>{" "}
                  to configure Google authorization locally. You can create
                  workspaces and add notes in the meantime.
                </p>
              )}
              <div className="privacy-grid">
                <Panel title="A connection you control">
                  <p>
                    No event creation, changes, or invitations. Disconnecting
                    removes stored credentials and blocks the imported calendar
                    context from prepared briefs.
                  </p>
                </Panel>
                <Panel title="Your next step stays yours">
                  <p>
                    Prepared drafts stay inside GhostTab for review. They are
                    never automatically sent to attendees.
                  </p>
                </Panel>
              </div>
              <Panel title="Preparation access">
                <p>
                  {config.model_configured
                    ? "Meta preparation is enabled with the configured server key."
                    : "Meta preparation is disabled until promotional credits and API access are verified."}
                </p>
                <p className="muted">
                  No model requests run just by opening GhostTab. Preparation
                  runs only when requested.
                </p>
              </Panel>
            </>
          )}
          {creating && (
            <section className="form-panel" aria-labelledby="new-title">
              <div className="section-heading">
                <h2 id="new-title">What are you preparing for?</h2>
                <button
                  className="text-button"
                  onClick={() => setCreating(false)}
                >
                  Close
                </button>
              </div>
              <form
                onSubmit={(event) => {
                  event.preventDefault();
                  const form = new FormData(event.currentTarget);
                  create.mutate({
                    title: String(form.get("title")),
                    goal: String(form.get("goal")),
                  });
                }}
              >
                <label>
                  Workspace title
                  <input
                    name="title"
                    placeholder="Client planning meeting"
                    maxLength={200}
                    required
                    autoFocus
                  />
                </label>
                <label>
                  What would a useful outcome look like?
                  <textarea
                    name="goal"
                    placeholder="Prepare the agenda, decisions needed, and questions to clarify."
                    maxLength={2000}
                    required
                  />
                </label>
                <ErrorNotice error={create.error} />
                <button className="primary" disabled={create.isPending}>
                  {create.isPending ? "Creating…" : "Create workspace"}
                </button>
              </form>
            </section>
          )}
          <footer className="workspace-footer">
            <span>
              <span className="tiny-mark" /> A little less context switching.
            </span>
            <span>GhostTab · Built with care</span>
          </footer>
        </main>
      </div>
    </div>
  );
}

function TaskList({
  tasks,
  onOpen,
}: {
  tasks: Task[];
  onOpen: (task: Task) => void;
}) {
  return (
    <div className="task-list">
      {tasks.map((task) => (
        <button className="task-row" key={task.id} onClick={() => onOpen(task)}>
          <span className="event-symbol" aria-hidden="true">
            {task.from_calendar ? "◷" : "✧"}
          </span>
          <span className="task-copy">
            <strong>{task.title}</strong>
            <span>{task.goal}</span>
          </span>
          <span
            className={`badge ${task.freshness === "stale" ? "stale" : ""}`}
          >
            {task.job?.generation === task.generation &&
            (task.job.status === "queued" || task.job.status === "running")
              ? "Preparing…"
              : task.freshness === "current"
                ? "Brief ready"
                : task.freshness === "stale"
                  ? "Update needed"
                  : "Add context & prepare"}
          </span>
          <span aria-hidden="true">↗</span>
        </button>
      ))}
    </div>
  );
}

function WorkspaceView({
  id,
  api,
  config,
  owner,
  onBack,
}: {
  id: string;
  api: Api;
  config: Config;
  owner: string;
  onBack: () => void;
}) {
  const queryClient = useQueryClient();
  const briefRef = useRef<HTMLDivElement>(null);
  const [editing, setEditing] = useState<Evidence | "new" | null>(null);
  const [citation, setCitation] = useState<{
    title: string;
    quote: string;
    content: string;
    url: string;
  } | null>(null);
  const workspace = useQuery({
    queryKey: ["workspace", owner, id],
    queryFn: () => api.workspace(id),
    refetchInterval: (query) =>
      ["queued", "running"].includes(query.state.data?.task.job?.status ?? "")
        ? 2000
        : false,
  });
  const refresh = () => {
    void workspace.refetch();
    void queryClient.invalidateQueries({ queryKey: ["tasks", owner] });
  };
  const prepare = useMutation({
    mutationFn: () => api.prepare(id),
    onSuccess: (job) => {
      queryClient.setQueryData<Workspace>(["workspace", owner, id], (saved) =>
        saved ? { ...saved, task: { ...saved.task, job } } : saved,
      );
      refresh();
    },
  });
  const sync = useMutation({
    mutationFn: () => api.sync(id),
    onSuccess: refresh,
  });
  const source = useMutation({
    mutationFn: (data: SourceInput) =>
      editing && editing !== "new"
        ? api.editEvidence(id, editing.id, data)
        : api.addEvidence(id, data),
    onSuccess: () => {
      setEditing(null);
      refresh();
    },
  });
  const remove = useMutation({
    mutationFn: (evidence: string) => api.removeEvidence(id, evidence),
    onSuccess: () => {
      setCitation(null);
      refresh();
    },
  });
  const data = workspace.data;
  if (!data)
    return (
      <>
        <button className="text-button" onClick={onBack}>
          ← Workspaces
        </button>
        <ErrorNotice error={workspace.error} />
        <p role="status">
          {workspace.isPending
            ? "Opening context…"
            : "Workspace could not load."}
        </p>
        <button onClick={() => void workspace.refetch()}>Retry</button>
      </>
    );
  const currentJob =
    data.task.job?.generation === data.task.generation ? data.task.job : null;
  const busy = ["queued", "running"].includes(currentJob?.status ?? "");
  const exhausted =
    currentJob?.status === "failed" &&
    currentJob.attempts >= 3 &&
    currentJob.generation === data.task.generation;
  const canReview = !!data.snapshot && data.task.freshness === "current";
  const reviewBrief = () => {
    briefRef.current?.focus({ preventScroll: true });
    briefRef.current?.scrollIntoView({
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "instant"
        : "smooth",
      block: "start",
    });
  };
  const showCitation = (point: Point, index: number) => {
    const ref = point.citations[index];
    const version = data.snapshot?.citations.find(
      (x) => x.id === ref.evidence_id,
    );
    if (version)
      setCitation({
        title: version.title,
        content: version.content,
        url: version.url,
        quote: ref.quote,
      });
  };
  const point = (value: Point, key: string | number) => (
    <div className="grounded-point" key={key}>
      <p>{value.text}</p>
      <div className="citations">
        {value.citations.map((ref, i) => (
          <button
            key={`${ref.evidence_id}-${i}`}
            onClick={() => showCitation(value, i)}
          >
            ↗{" "}
            {data.snapshot?.citations.find((x) => x.id === ref.evidence_id)
              ?.title ?? "Source"}
          </button>
        ))}
      </div>
    </div>
  );
  return (
    <>
      <button className="text-button back" onClick={onBack}>
        ← All workspaces
      </button>
      <p className="eyebrow">A CLEARER WAY INTO THE WORK</p>
      <div className="page-heading">
        <div>
          <h1 className="task-title">{data.task.title}</h1>
          <p>{data.task.goal}</p>
        </div>
        <div className="button-group">
          {data.task.from_calendar && (
            <button
              className="secondary"
              disabled={sync.isPending}
              onClick={() => sync.mutate()}
            >
              {sync.isPending ? "Checking…" : "Check Calendar"}
            </button>
          )}
          <button
            className="primary"
            disabled={
              busy ||
              prepare.isPending ||
              (!canReview &&
                (!config.model_configured ||
                  !data.evidence.length ||
                  exhausted))
            }
            onClick={() => (canReview ? reviewBrief() : prepare.mutate())}
          >
            {busy || prepare.isPending
              ? "Preparing…"
              : data.task.freshness === "stale"
                ? "Update brief"
                : canReview
                  ? "Review brief"
                  : "Prepare brief"}
          </button>
        </div>
      </div>
      <ErrorNotice
        error={
          workspace.error ||
          prepare.error ||
          source.error ||
          remove.error ||
          sync.error
        }
      />
      <PreparationStatus
        task={data.task}
        hasBrief={!!data.snapshot}
        sourceCount={data.evidence.length}
        enabled={config.model_configured}
        starting={prepare.isPending}
        onRetry={() => prepare.mutate()}
        onReview={reviewBrief}
      />
      <div className="workspace-grid">
        <div
          className="brief-column"
          ref={briefRef}
          tabIndex={-1}
          role="region"
          aria-label="Prepared brief"
        >
          {data.snapshot ? (
            <>
              <Panel
                title={
                  data.task.freshness === "stale"
                    ? "Previous brief"
                    : "The brief"
                }
              >
                {point(data.snapshot.brief.summary, "summary")}
                <p className="muted small">
                  Prepared{" "}
                  {new Date(data.snapshot.created_at * 1000).toLocaleString()} ·
                  Review against the sources
                </p>
              </Panel>
              <Panel title="What we know">
                {data.snapshot.brief.facts.length ? (
                  data.snapshot.brief.facts.map(point)
                ) : (
                  <p className="muted">No additional facts were established.</p>
                )}
              </Panel>
              <Panel title="A useful next step">
                {data.snapshot.brief.next_steps.length ? (
                  data.snapshot.brief.next_steps.map(point)
                ) : (
                  <p className="muted">
                    No next steps were supported by the available context.
                  </p>
                )}
              </Panel>
              <Panel title="Still to clarify">
                {data.snapshot.brief.unknowns.length ? (
                  <ul className="question-list">
                    {data.snapshot.brief.unknowns.map((text, i) => (
                      <li key={i}>{text}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">
                    No additional questions were listed. Check the source
                    context before treating it as complete.
                  </p>
                )}
              </Panel>
              <DraftEditor key={data.snapshot.id} api={api} data={data} />
            </>
          ) : (
            <section className="empty-state brief-empty">
              <span className="empty-mark">
                <GhostMark />
              </span>
              <h2>The context comes first.</h2>
              <p>
                Add the notes that matter, then prepare a brief.
                <br />
                Every point will link back to its source.
              </p>
            </section>
          )}
        </div>
        <aside className="evidence-column">
          <div className="section-heading">
            <h2>Your source context</h2>
            <button className="text-button" onClick={() => setEditing("new")}>
              ＋ Add notes
            </button>
          </div>
          {!data.evidence.length && (
            <p className="muted">
              Add a meeting description, request, or working notes. Manual
              imports are saved as notes.
            </p>
          )}
          {data.evidence.map((item) => (
            <article className="source-card" key={item.id}>
              <span className="card-eyebrow">
                {item.origin === "google_calendar"
                  ? "GOOGLE CALENDAR · READ ONLY"
                  : "MANUALLY ADDED NOTES"}
              </span>
              <h3>{item.title}</h3>
              <p className="source-excerpt">{item.content}</p>
              <details>
                <summary>Read full source</summary>
                <p className="source-content">{item.content}</p>
                {item.url.startsWith("https://") && (
                  <a href={item.url} target="_blank" rel="noreferrer">
                    Open original ↗
                  </a>
                )}
              </details>
              <div className="source-actions">
                {item.origin === "manual" && (
                  <button
                    className="text-button"
                    onClick={() => setEditing(item)}
                  >
                    Edit notes
                  </button>
                )}
                <button
                  className="text-button"
                  disabled={remove.isPending}
                  onClick={() => remove.mutate(item.id)}
                >
                  Remove
                </button>
              </div>
            </article>
          ))}
          {citation && (
            <section className="citation-card" aria-live="polite">
              <div className="section-heading">
                <h3>Cited source revision</h3>
                <button
                  className="text-button"
                  onClick={() => setCitation(null)}
                >
                  Close
                </button>
              </div>
              <strong>{citation.title}</strong>
              <blockquote>{citation.quote}</blockquote>
              <details>
                <summary>Read cited version</summary>
                <p className="source-content">{citation.content}</p>
              </details>
              {citation.url.startsWith("https://") && (
                <a href={citation.url} target="_blank" rel="noreferrer">
                  Open original ↗
                </a>
              )}
            </section>
          )}
        </aside>
      </div>
      {editing && (
        <section className="form-panel">
          <div className="section-heading">
            <h2>
              {editing === "new"
                ? "Bring in some context"
                : "Update your notes"}
            </h2>
            <button className="text-button" onClick={() => setEditing(null)}>
              Close
            </button>
          </div>
          <SourceForm
            key={editing === "new" ? "new" : editing.version_id}
            value={editing === "new" ? undefined : editing}
            busy={source.isPending}
            onSubmit={(value) => source.mutate(value)}
          />
          <ErrorNotice error={source.error} />
        </section>
      )}
    </>
  );
}

function SourceForm({
  value,
  busy,
  onSubmit,
}: {
  value?: SourceInput;
  busy: boolean;
  onSubmit: (data: SourceInput) => void;
}) {
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    onSubmit({
      title: String(form.get("title")),
      content: String(form.get("content")),
      url: String(form.get("url")),
    });
  }
  return (
    <form onSubmit={submit}>
      <p className="muted">
        Add only context you have permission to use. This is a manual import.
      </p>
      <label>
        Source title
        <input
          name="title"
          defaultValue={value?.title}
          placeholder="Meeting notes or project brief"
          maxLength={200}
          required
          autoFocus
        />
      </label>
      <label>
        Notes or source text
        <textarea
          name="content"
          defaultValue={value?.content}
          rows={7}
          maxLength={12000}
          required
        />
      </label>
      <label>
        Original link <span className="muted">(optional)</span>
        <input
          name="url"
          type="url"
          pattern="https://.*"
          defaultValue={value?.url}
          placeholder="https://…"
          maxLength={2000}
        />
      </label>
      <button className="primary" disabled={busy}>
        {busy ? "Saving…" : "Save context"}
      </button>
    </form>
  );
}

function DraftEditor({ api, data }: { api: Api; data: Workspace }) {
  const [draft, setDraft] = useState(data.snapshot?.draft ?? "");
  const save = useMutation({
    mutationFn: () => api.saveDraft(data.task.id, data.snapshot!.id, draft),
  });
  return (
    <Panel title="A draft to make your own">
      <p className="muted">
        Review and edit before using it. This message stays unsent.
      </p>
      <label className="sr-only" htmlFor="draft">
        Editable draft
      </label>
      <textarea
        id="draft"
        rows={7}
        maxLength={6000}
        value={draft}
        onChange={(event) => {
          setDraft(event.target.value);
          save.reset();
        }}
      />
      <div className="draft-actions">
        <button
          className="secondary"
          disabled={save.isPending}
          onClick={() => save.mutate()}
        >
          {save.isPending ? "Saving…" : "Save draft"}
        </button>
        <span role="status">
          {save.isSuccess ? "Draft saved · unsent" : "For your review"}
        </span>
      </div>
      <ErrorNotice error={save.error} />
    </Panel>
  );
}
