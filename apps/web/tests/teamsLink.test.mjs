import assert from "node:assert/strict";
import test from "node:test";
import { teamsChat } from "../src/teamsLink.ts";

test("Teams selects an existing chat without forwarding URLs or query context", () => {
  assert.deepEqual(teamsChat("19:demo@thread.v2"), {
    chat_id: "19:demo@thread.v2",
  });
  assert.deepEqual(
    teamsChat(
      "https://teams.microsoft.com/l/chat/19%3Ademo%40thread.v2/conversations?tenantId=ignored",
    ),
    { chat_id: "19:demo@thread.v2" },
  );
  assert.deepEqual(
    teamsChat(
      "https://teams.cloud.microsoft/l/chat/19:demo@thread.v2/conversations",
    ),
    { chat_id: "19:demo@thread.v2" },
  );
  for (const link of [
    "https://evil.test/l/chat/19:demo/conversations",
    "https://user@teams.microsoft.com/l/chat/19:demo/conversations",
    "https://teams.microsoft.com/l/channel/19:demo/general",
    "https://teams.microsoft.com/l/chat/0/0?users=someone",
    "19:demo/../../me",
    "https://teams.microsoft.com/l/chat/19%3Ademo%2Fsecret/conversations",
  ])
    assert.throws(() => teamsChat(link));
});
