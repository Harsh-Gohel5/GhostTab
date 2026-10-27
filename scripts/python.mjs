import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const python = resolve(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const tasks = {
  dev: [['-m', 'uvicorn', 'ghosttab_api.main:app', '--reload', '--reload-dir', 'apps/api/src', '--host', '127.0.0.1', '--port', '8000', '--no-access-log']],
  check: [
    ['-m', 'ruff', 'check', 'apps/api'],
    ['-m', 'ruff', 'format', '--check', 'apps/api'],
    ['-m', 'pytest', 'apps/api/tests'],
  ],
  test: [['-m', 'pytest', 'apps/api/tests']],
  worker: [['-m', 'ghosttab_api.worker']],
  migrate: [['-m', 'alembic', 'upgrade', 'head']],
};

if (!existsSync(python)) {
  console.error('Create the .venv and install backend dependencies first. See README.md.');
  process.exit(1);
}

const commands = tasks[process.argv[2]];
if (!commands) {
  console.error('Usage: node scripts/python.mjs <dev|check|test|worker|migrate>');
  process.exit(1);
}

for (const args of commands) {
  const result = spawnSync(python, args, { cwd: root, stdio: 'inherit' });
  if (result.error) console.error(result.error.message);
  if (result.status !== 0) process.exit(result.status ?? 1);
}
