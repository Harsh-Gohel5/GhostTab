// Display source wall time and its explicit offset, never the viewer's timezone.
const timestamp =
  /\b(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})(?::(\d{2})(?:\.\d+)?)?(Z|[+-]\d{2}:\d{2})\b/g;

export function readableTimestamp(value: string): string {
  const match =
    /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})(?::(\d{2})(?:\.\d+)?)?(Z|[+-]\d{2}:\d{2})$/.exec(
      value,
    );
  if (!match || !Number.isFinite(Date.parse(value))) return value;
  const wall = new Date(`${match[1]}T${match[2]}:${match[3] ?? "00"}Z`);
  if (
    !Number.isFinite(wall.getTime()) ||
    wall.toISOString().slice(0, 10) !== match[1]
  )
    return value;
  const date = new Intl.DateTimeFormat("en-US", {
    timeZone: "UTC",
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  }).format(wall);
  const time = new Intl.DateTimeFormat("en-US", {
    timeZone: "UTC",
    hour: "numeric",
    minute: "2-digit",
  }).format(wall);
  const offset =
    match[4] === "Z" || match[4] === "+00:00"
      ? "UTC"
      : `UTC${match[4].replace("-", "−")}`;
  return `${date} at ${time} (${offset})`;
}

export function readableDates(text: string): string {
  return text
    .replace(timestamp, (value) => readableTimestamp(value))
    .replace(
      /\bat (Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),/g,
      "on $1,",
    );
}

export function readableCalendar(content: string): string {
  const lines = content.split("\n");
  const start = lines.find((line) => line.startsWith("Starts: "))?.slice(8);
  const end = lines.find((line) => line.startsWith("Ends: "))?.slice(6);
  const first = start ? readableTimestamp(start) : "";
  const last = end ? readableTimestamp(end) : "";
  const sameDay =
    start &&
    end &&
    start.slice(0, 10) === end.slice(0, 10) &&
    start.match(/(?:Z|[+-]\d{2}:\d{2})$/)?.[0] ===
      end.match(/(?:Z|[+-]\d{2}:\d{2})$/)?.[0] &&
    first.includes(" at ") &&
    last.includes(" at ");
  return lines
    .flatMap((line) => {
      if (sameDay && line.startsWith("Starts: "))
        return [
          `Date: ${first.split(" at ")[0]}`,
          `Time: ${first.split(" at ")[1].replace(/ \(UTC.*\)$/, "")} – ${last.split(" at ")[1]}`,
        ];
      if (sameDay && line.startsWith("Ends: ")) return [];
      if (line.startsWith("Timezone: "))
        return line.replace(
          /Timezone: ([A-Za-z_]+)\/([A-Za-z_/]+)/,
          (_all, region, city) =>
            `Timezone: ${city.replaceAll("_", " ")} (${region})`,
        );
      return readableDates(line);
    })
    .join("\n");
}

export function readableDay(value: string): string {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return value;
  const date = new Date(`${value}T00:00:00Z`);
  if (
    !Number.isFinite(date.getTime()) ||
    date.toISOString().slice(0, 10) !== value
  )
    return value;
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "UTC",
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

export function preparedDate(seconds: number): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  }).format(new Date(seconds * 1000));
}
