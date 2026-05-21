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
