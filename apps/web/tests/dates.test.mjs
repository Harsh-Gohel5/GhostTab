import assert from "node:assert/strict";
import test from "node:test";
import {
  readableTimestamp,
  readableDates,
  readableDay,
  readableCalendar,
} from "../src/dates.ts";

test("Phoenix timestamps are readable and preserve source time regardless of viewer timezone", () => {
  assert.equal(
    readableTimestamp("2026-10-29T13:30:00-07:00"),
    "Thursday, October 29, 2026 at 1:30 PM (UTC−07:00)",
  );
  assert.match(
    readableTimestamp("2026-10-29T00:00:00+05:30"),
    /October 29, 2026 at 12:00 AM \(UTC\+05:30\)/,
  );
  assert.match(readableTimestamp("2026-10-29T12:00:00Z"), /12:00 PM \(UTC\)/);
});
test("same-day UTC ranges are grouped; changing offsets are kept explicit", () => {
  assert.match(
    readableCalendar(
      "Starts: 2026-10-29T13:30:00Z\nEnds: 2026-10-29T15:00:00Z",
    ),
    /Time: 1:30 PM – 3:00 PM \(UTC\)/,
  );
  const shifted = readableCalendar(
    "Starts: 2026-11-01T01:30:00-04:00\nEnds: 2026-11-01T01:30:00-05:00",
  );
  assert.match(shifted, /UTC−04:00/);
  assert.match(shifted, /UTC−05:00/);
});
test("calendar source presents one date and a clear time range without changing stored input", () => {
  const source =
    "Starts: 2026-10-29T13:30:00-07:00\nEnds: 2026-10-29T15:00:00-07:00\nTimezone: America/Phoenix\nDescription: Deadline at noon.";
  const display = readableCalendar(source);
  assert.match(display, /Date: Thursday, October 29, 2026/);
  assert.match(display, /Time: 1:30 PM – 3:00 PM \(UTC−07:00\)/);
  assert.match(display, /Timezone: Phoenix \(America\)/);
  assert.match(display, /Deadline at noon/);
  assert.ok(source.includes("T13:30:00"));
});
test("overnight and offset-changing ranges retain separate dates and offsets", () => {
  const display = readableCalendar(
    "Starts: 2026-10-29T23:30:00-07:00\nEnds: 2026-10-30T01:00:00-07:00",
  );
  assert.match(display, /October 29, 2026 at 11:30 PM/);
  assert.match(display, /October 30, 2026 at 1:00 AM/);
});
test("all-day dates never shift to the previous local day", () => {
  assert.equal(readableDay("2026-10-29"), "Thursday, October 29, 2026");
});
test("invalid dates and ordinary text remain unchanged", () => {
  assert.equal(
    readableTimestamp("2026-02-30T13:30:00Z"),
    "2026-02-30T13:30:00Z",
  );
  assert.equal(readableDay("2026-02-30"), "2026-02-30");
  assert.equal(
    readableDates("Thursday at noon, approved by Lee."),
    "Thursday at noon, approved by Lee.",
  );
  assert.equal(readableDates("2026-10-29T25:00:00Z"), "2026-10-29T25:00:00Z");
});
test("formatting prose handles several timestamps without interpreting HTML", () => {
  const display = readableDates(
    "<script> 2026-10-29T13:30:00-07:00 to 2026-10-29T15:00:00-07:00.",
  );
  assert.match(display, /^<script> Thursday/);
  assert.match(display, /3:00 PM/);
});
