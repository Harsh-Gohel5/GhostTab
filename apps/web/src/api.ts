import { z } from "zod";

export const configSchema = z.object({
  auth_mode: z.enum(["local", "supabase"]),
  supabase_url: z.string(),
  supabase_publishable_key: z.string(),
  model_configured: z.boolean(),
  calendar_configured: z.boolean(),
});
const jobSchema = z.object({
  id: z.string(),
  task_id: z.string(),
  generation: z.number(),
  status: z.string(),
  attempts: z.number(),
  error_code: z.string().nullable(),
  created_at: z.number(),
});
export const taskSchema = z.object({
  id: z.string(),
  title: z.string(),
  goal: z.string(),
  generation: z.number(),
  created_at: z.number(),
  from_calendar: z.boolean(),
  calendar_event_id: z.string().nullable(),
  source_count: z.number().int().nonnegative(),
  freshness: z.enum(["unprepared", "current", "stale"]),
  job: jobSchema.nullable(),
});
export const evidenceSchema = z.object({
  id: z.string(),
  version_id: z.string(),
  title: z.string(),
  content: z.string(),
  url: z.string(),
  origin: z.string(),
  observed_at: z.number(),
});
const citationSchema = z.object({ evidence_id: z.string(), quote: z.string() });
const pointSchema = z.object({
  text: z.string(),
  citations: z.array(citationSchema),
});
export const workspaceSchema = z.object({
  task: taskSchema,
  evidence: z.array(evidenceSchema),
  snapshot: z
    .object({
      id: z.string(),
      draft: z.string(),
      created_at: z.number(),
      brief: z.object({
        summary: pointSchema,
        facts: z.array(pointSchema),
        next_steps: z.array(pointSchema),
        unknowns: z.array(z.string()),
        draft: z.string(),
      }),
      citations: z.array(
        z.object({
          id: z.string(),
          version_id: z.string(),
          title: z.string(),
          content: z.string(),
          url: z.string(),
        }),
      ),
    })
    .nullable(),
});
export const connectionsSchema = z.object({
  google_calendar: z.enum(["connected", "not_connected"]),
  estimated_usage_usd: z.number(),
  budget_usd: z.number(),
});
export const eventsSchema = z.object({
  has_more: z.boolean(),
  events: z.array(
    z.object({
      id: z.string(),
      title: z.string(),
      start: z.object({
        dateTime: z.string().optional(),
        date: z.string().optional(),
        timeZone: z.string().optional(),
      }),
      end: z.object({
        dateTime: z.string().optional(),
        date: z.string().optional(),
        timeZone: z.string().optional(),
      }),
    }),
  ),
});

export type Config = z.infer<typeof configSchema>;
export type Task = z.infer<typeof taskSchema>;
export type Evidence = z.infer<typeof evidenceSchema>;
export type Workspace = z.infer<typeof workspaceSchema>;
export type Point = z.infer<typeof pointSchema>;
export type SourceInput = { title: string; content: string; url: string };

export class Api {
  constructor(private token?: () => Promise<string | undefined>) {}
  async request<T>(
    path: string,
    schema: z.ZodType<T>,
    method = "GET",
    body?: unknown,
  ): Promise<T> {
    const token = await this.token?.();
    let response: Response;
    try {
      response = await fetch(`/api${path}`, {
        method,
        signal: AbortSignal.timeout(25000),
        headers: {
          "Content-Type": "application/json",
          ...(token
            ? { Authorization: `Bearer ${token}` }
            : { "X-GhostTab-Local": "1" }),
        },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
    } catch {
      throw new Error(
        "GhostTab could not reach the server. Check the connection and retry.",
      );
    }
    if (!response.ok) {
      let detail: unknown;
      try {
        detail = (await response.json()).detail;
      } catch {
        /* Safe fallback below. */
      }
      throw new Error(
        typeof detail === "string"
          ? detail
          : `Request could not complete (${response.status}).`,
      );
    }
    if (response.status === 204) return schema.parse(undefined);
    return schema.parse(await response.json());
  }
  tasks() {
    return this.request("/tasks", z.array(taskSchema));
  }
  workspace(id: string) {
    return this.request(`/tasks/${id}/workspace`, workspaceSchema);
  }
  connections() {
    return this.request("/connections", connectionsSchema);
  }
  events() {
    return this.request("/calendar/events", eventsSchema);
  }
  createTask(title: string, goal: string) {
    return this.request("/tasks", taskSchema, "POST", { title, goal });
  }
  importEvent(event_id: string) {
    return this.request("/tasks/from-calendar", taskSchema, "POST", {
      event_id,
    });
  }
  addEvidence(id: string, body: SourceInput) {
    return this.request(
      `/tasks/${id}/evidence`,
      z.object({ id: z.string() }),
      "POST",
      body,
    );
  }
  editEvidence(task: string, evidence: string, body: SourceInput) {
    return this.request(
      `/tasks/${task}/evidence/${evidence}`,
      z.object({ id: z.string() }),
      "PUT",
      body,
    );
  }
  removeEvidence(task: string, evidence: string) {
    return this.request(
      `/tasks/${task}/evidence/${evidence}`,
      z.undefined(),
      "DELETE",
    );
  }
  prepare(id: string) {
    return this.request(`/tasks/${id}/prepare`, jobSchema, "POST");
  }
  sync(id: string) {
    return this.request(`/tasks/${id}/sync`, taskSchema, "POST");
  }
  saveDraft(id: string, snapshot: string, draft: string) {
    return this.request(
      `/tasks/${id}/draft?snapshot_id=${encodeURIComponent(snapshot)}`,
      z.object({ saved: z.boolean() }),
      "PUT",
      { draft },
    );
  }
  connect() {
    return this.request(
      "/connections/google/start",
      z.object({ url: z.string().url() }),
      "POST",
    );
  }
  disconnect() {
    return this.request("/connections/google", z.undefined(), "DELETE");
  }
}
