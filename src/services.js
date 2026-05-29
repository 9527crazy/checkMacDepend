import { invoke } from "@tauri-apps/api/core";

export function getAppState() {
  return invoke("get_app_state");
}

export function scanPackages() {
  return invoke("scan_packages");
}

export function generateReport(date) {
  return invoke("generate_report", { date });
}

export function getScanSchedule() {
  return invoke("get_scan_schedule");
}

export function startScheduledScan(intervalHours) {
  return invoke("start_scheduled_scan", { intervalHours });
}

export function stopScheduledScan() {
  return invoke("stop_scheduled_scan");
}
