use std::collections::HashSet;

use tauri::Manager;

use crate::models::{AppState, ScanResult, ScanScheduleState};
use crate::report;
use crate::scanner::{
    available_managers, package_key, scan_all_packages_with_log, snapshot_package, total_count,
};
use crate::scheduler::{self, SchedulerHandle};
use crate::storage;
use crate::{emit_log, now_minutes, today};

pub fn scan_and_persist(
    app: &tauri::AppHandle,
    schedule_handle: &SchedulerHandle,
) -> Result<ScanResult, String> {
    let scanned_at = now_minutes();
    let scanned_date = today();
    let packages = scan_all_packages_with_log(app, &scanned_at);
    let mut data = storage::load_storage()?;
    let previous_keys: HashSet<String> = data
        .snapshot
        .packages
        .iter()
        .map(package_key)
        .collect();
    let has_baseline =
        !data.snapshot.packages.is_empty() || data.metadata.last_scan_at.is_some();

    let mut new_packages = Vec::new();
    if has_baseline {
        for package in &packages {
            if !previous_keys.contains(&package_key(package)) {
                new_packages.push(package.clone());
            }
        }
    }

    if !new_packages.is_empty() {
        let day_records = data.records.entry(scanned_date).or_default();
        let mut existing_keys: HashSet<String> =
            day_records.iter().map(package_key).collect();
        for package in &new_packages {
            if existing_keys.insert(package_key(package)) {
                day_records.push(package.clone());
            }
        }
    }

    data.snapshot = crate::models::Snapshot {
        packages: packages.iter().map(snapshot_package).collect(),
        scanned_at: Some(scanned_at.clone()),
    };
    data.metadata.schema_version = 2;
    data.metadata.last_scan_at = Some(scanned_at.clone());
    storage::save_storage(&data)?;

    scheduler::update_last_scan(schedule_handle, &scanned_at);

    if has_baseline {
        emit_log(
            app,
            "success",
            &format!(
                "扫描完成！共 {} 个包，发现 {} 个新增包",
                packages.len(),
                new_packages.len()
            ),
        );
    } else {
        emit_log(
            app,
            "success",
            &format!(
                "首次扫描完成！共 {} 个包，已建立基线",
                packages.len()
            ),
        );
    }

    Ok(ScanResult {
        new_count: new_packages.len(),
        scanned_count: packages.len(),
        new_packages,
        is_initial_scan: !has_baseline,
        scanned_at,
    })
}

#[tauri::command]
pub fn get_app_state() -> Result<AppState, String> {
    let data = storage::load_storage()?;
    let mut dates = data.records.keys().cloned().collect::<Vec<_>>();
    dates.sort_by(|a, b| b.cmp(a));

    Ok(AppState {
        dates,
        total_count: total_count(&data.records),
        last_scan_at: data.metadata.last_scan_at.clone(),
        records: data.records,
        available_managers: available_managers(),
    })
}

#[tauri::command]
pub async fn scan_packages(
    app: tauri::AppHandle,
    schedule_handle: tauri::State<'_, SchedulerHandle>,
) -> Result<ScanResult, String> {
    let app_clone = app.clone();
    let schedule_clone = schedule_handle.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        scan_and_persist(&app_clone, &schedule_clone)
    })
    .await
    .map_err(|e| e.to_string())?
}

#[tauri::command]
pub fn generate_report(app: tauri::AppHandle, date: String) -> Result<String, String> {
    report::generate_report(&app, &date)
}

#[tauri::command]
pub fn get_scan_schedule(
    handle: tauri::State<'_, SchedulerHandle>,
) -> ScanScheduleState {
    scheduler::get_state(&handle)
}

#[tauri::command]
pub fn start_scheduled_scan(
    app: tauri::AppHandle,
    handle: tauri::State<'_, SchedulerHandle>,
    interval_hours: u32,
) -> Result<ScanScheduleState, String> {
    scheduler::start_scheduler(handle.inner().clone(), app, interval_hours)
}

#[tauri::command]
pub fn stop_scheduled_scan(
    handle: tauri::State<'_, SchedulerHandle>,
) -> ScanScheduleState {
    scheduler::stop_scheduler(&handle)
}

#[tauri::command]
pub fn toggle_devtools(app: tauri::AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        window.open_devtools();
    }
}
