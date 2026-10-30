import assert from "node:assert/strict";
import test from "node:test";
import { slackSelection } from "../src/slackLink.ts";

test("Slack permalink resolves the selected root timestamp, including copied replies", () => {
  assert.deepEqual(
    slackSelection(
      "https://demo.slack.com/archives/CDEMO123/p1234567890000001",
    ),
    { channel_id: "CDEMO123", thread_ts: "1234567890.000001" },
  );
  assert.equal(
    slackSelection(
      "https://demo.slack.com/archives/CDEMO123/p1234567890000002?thread_ts=1234567890.000001",
    ).thread_ts,
    "1234567890.000001",
  );
});
test("untrusted hosts, credentials and malformed timestamps never become requests", () => {
  for (const value of [
    "https://evil.test/archives/CDEMO123/p1234567890000001",
    "https://demo.slack.com.evil.test/archives/CDEMO123/p1234567890000001",
    "https://name:secret@demo.slack.com/archives/CDEMO123/p1234567890000001",
    "https://demo.slack.com/archives/CDEMO123/p1234567890000001?thread_ts=bad",
    "file:///secret",
  ])
    assert.throws(() => slackSelection(value), /public-channel message link/);
});
