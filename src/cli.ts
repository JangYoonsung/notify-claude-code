#!/usr/bin/env node

/**
 * Claude Monitor CLI
 * TypeScript wrapper for the Python-based notification system
 */

import { execSync } from 'child_process';
import { join } from 'path';
import { homedir } from 'os';

// Get the scripts directory path
const homeDir = homedir();
const scriptsDir = join(homeDir, '.claude-monitor', 'scripts');
const notificationScript = join(scriptsDir, 'notification_system.py');

// Parse command line arguments
const args = process.argv.slice(2);

// Build the Python command
const pythonCmd = `python3 "${notificationScript}" ${args.join(' ')}`;

try {
  // Execute the Python script
  execSync(pythonCmd, {
    stdio: 'inherit',
    cwd: scriptsDir
  });
} catch (error: any) {
  // Error already displayed via stdio: 'inherit'
  process.exit(error.status || 1);
}
