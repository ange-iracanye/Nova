import { spawnSync } from "node:child_process";

const command = process.platform === "win32" ? "npm.cmd" : "npm";
const result = spawnSync(command, ["run", "build"], {
  cwd: new URL("../../frontend/", import.meta.url),
  env: { ...process.env, NOVA_NATIVE_BUILD: "1" },
  stdio: "inherit",
});

if (result.status !== 0) process.exit(result.status ?? 1);
