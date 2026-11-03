import { existsSync, readFileSync, readdirSync } from "node:fs";
import { dirname, resolve, relative } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const files = [
  "README.md",
  "CONTRIBUTING.md",
  "AGENTS.md",
  "PROJECT_CONTEXT.md",
];
for (const directory of ["docs", "apps/web", "apps/api"]) {
  for (const entry of readdirSync(resolve(root, directory), {
    recursive: true,
    withFileTypes: true,
  })) {
    if (!entry.isFile() || !entry.name.endsWith(".md")) continue;
    const path = resolve(entry.parentPath, entry.name);
    if (
      /(?:^|[/\\])(?:node_modules|dist|__pycache__|\.pytest_cache)(?:[/\\]|$)/.test(
        path,
      )
    )
      continue;
    files.push(relative(root, path));
  }
}

let checked = 0;
const broken = [];
for (const file of files) {
  const fullPath = resolve(root, file);
  const markdown = readFileSync(fullPath, "utf8").replace(
    /```[\s\S]*?```/g,
    "",
  );
  for (const match of markdown.matchAll(
    /!?\[[^\]\n]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)/g,
  )) {
    const link = match[1].replace(/^<|>$/g, "");
    if (/^(?:[a-z][a-z\d+.-]*:|#|\/)/i.test(link)) continue;
    const target = decodeURIComponent(link.split(/[?#]/, 1)[0]);
    if (!target) continue;
    checked++;
    if (!existsSync(resolve(dirname(fullPath), target)))
      broken.push(`${file}: ${link}`);
  }
}
if (broken.length) {
  console.error(
    `Broken local documentation links (${broken.length}):\n${broken.join("\n")}`,
  );
  process.exitCode = 1;
} else {
  console.log(
    `Checked ${checked} local links across ${files.length} Markdown files.`,
  );
}
