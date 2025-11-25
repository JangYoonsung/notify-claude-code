#!/usr/bin/env node

/**
 * Claude Monitor CLI
 * TypeScript wrapper for the Python-based notification system
 */

import { execSync } from "child_process";
import { join } from "path";
import { homedir } from "os";
import { existsSync } from "fs";

/**
 * Find the scripts directory by checking multiple possible locations
 */
function findScriptsDir(): string | null {
  const homeDir = homedir();

  // Possible locations in priority order
  const possiblePaths = [
    // 1. Environment variable override
    process.env.CLAUDE_MONITOR_SCRIPTS_DIR,

    // 2. Default user installation location
    join(homeDir, ".claude-monitor", "scripts"),

    // 3. Bundled with npm package (for global install)
    join(__dirname, "..", "scripts"),

    // 4. Alternative user location
    join(homeDir, ".claude", "scripts"),
  ];

  for (const path of possiblePaths) {
    if (path && existsSync(path)) {
      const scriptPath = join(path, "notification_system.py");
      if (existsSync(scriptPath)) {
        return path;
      }
    }
  }

  return null;
}

// Find scripts directory
const scriptsDir = findScriptsDir();

if (!scriptsDir) {
  console.error("Error: Could not find notification_system.py");
  console.error("");
  console.error("Please ensure Python scripts are installed in one of:");
  console.error(`  - ${join(homedir(), ".claude-monitor", "scripts")}`);
  console.error(`  - Set CLAUDE_MONITOR_SCRIPTS_DIR environment variable`);
  console.error("");
  console.error(
    "See: https://github.com/JangYoonsung/notify-claude-code#installation"
  );
  process.exit(1);
}

const notificationScript = join(scriptsDir, "notification_system.py");

// Parse command line arguments
const args = process.argv.slice(2);

// Build the Python command
const pythonCmd = `python3 "${notificationScript}" ${args.join(" ")}`;

try {
  // Execute the Python script
  execSync(pythonCmd, {
    stdio: "inherit",
    cwd: scriptsDir,
  });
} catch (error: any) {
  // Error already displayed via stdio: 'inherit'
  process.exit(error.status || 1);
}
