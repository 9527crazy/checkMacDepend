use chrono::Local;
use serde::{Deserialize, Serialize};
use std::{
    collections::{BTreeMap, HashMap, HashSet},
    fs,
    path::PathBuf,
    process::Command,
    sync::{Arc, Mutex},
    thread,
    time::Duration,
};
// use tauri::Manager;
use tauri_plugin_opener::OpenerExt;

#[derive(Debug, Clone, Serialize, Deserialize)]
struct PackageInfo {
    manager: String,
    name: String,
    version: String,
    #[serde(default)]
    time: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Snapshot {
    packages: Vec<PackageInfo>,
    scanned_at: Option<String>,
}

impl Default for Snapshot {
    fn default() -> Self {
        Self {
            packages: Vec::new(),
            scanned_at: None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Metadata {
    schema_version: u8,
    last_scan_at: Option<String>,
}

impl Default for Metadata {
    fn default() -> Self {
        Self {
            schema_version: 2,
            last_scan_at: None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct StorageData {
    records: BTreeMap<String, Vec<PackageInfo>>,
    snapshot: Snapshot,
    metadata: Metadata,
}

impl Default for StorageData {
    fn default() -> Self {
        Self {
            records: BTreeMap::new(),
            snapshot: Snapshot::default(),
            metadata: Metadata::default(),
        }
    }
}

#[derive(Debug, Serialize)]
struct AppState {
    dates: Vec<String>,
    records: BTreeMap<String, Vec<PackageInfo>>,
    total_count: usize,
    last_scan_at: Option<String>,
    available_managers: Vec<String>,
}

#[derive(Debug, Serialize)]
struct ScanResult {
    new_packages: Vec<PackageInfo>,
    new_count: usize,
    scanned_count: usize,
    is_initial_scan: bool,
    scanned_at: String,
}

#[derive(Debug, Deserialize)]
struct PipPackage {
    name: String,
    version: String,
}

#[derive(Debug, Deserialize)]
struct NpmList {
    #[serde(default)]
    dependencies: HashMap<String, NpmPackage>,
}

#[derive(Debug, Deserialize)]
struct NpmPackage {
    #[serde(default)]
    version: String,
}



#[derive(Debug, Clone, Serialize, Deserialize)]
struct ScanSchedule {
    enabled: bool,
    interval_hours: u32,
    last_scan_at: Option<String>,
}

impl Default for ScanSchedule {
    fn default() -> Self {
        Self {
            enabled: false,
            interval_hours: 24,
            last_scan_at: None,
        }
    }
}

#[derive(Debug, Serialize)]
struct ScanScheduleState {
    enabled: bool,
    interval_hours: u32,
    last_scan_at: Option<String>,
}

fn now_minutes() -> String {
    Local::now().format("%Y-%m-%d %H:%M").to_string()
}

fn today() -> String {
    Local::now().format("%Y-%m-%d").to_string()
}

fn storage_dir() -> Result<PathBuf, String> {
    let home = dirs::home_dir().ok_or_else(|| "无法定位用户主目录".to_string())?;
    Ok(home.join(".pkg-monitor"))
}

fn records_path() -> Result<PathBuf, String> {
    Ok(storage_dir()?.join("records.json"))
}

fn reports_dir() -> Result<PathBuf, String> {
    Ok(storage_dir()?.join("reports"))
}

fn ensure_storage_dirs() -> Result<(), String> {
    fs::create_dir_all(storage_dir()?).map_err(|error| error.to_string())?;
    fs::create_dir_all(reports_dir()?).map_err(|error| error.to_string())?;
    Ok(())
}

fn load_storage() -> Result<StorageData, String> {
    ensure_storage_dirs()?;
    let path = records_path()?;
    if !path.exists() {
        return Ok(StorageData::default());
    }

    let content = fs::read_to_string(path).map_err(|error| error.to_string())?;
    let value: serde_json::Value = serde_json::from_str(&content).map_err(|error| error.to_string())?;

    if value.get("records").is_some() || value.get("snapshot").is_some() || value.get("metadata").is_some() {
        let mut data: StorageData = serde_json::from_value(value).map_err(|error| error.to_string())?;
        data.metadata.schema_version = 2;
        if data.metadata.last_scan_at.is_none() {
            data.metadata.last_scan_at = data.snapshot.scanned_at.clone();
        }
        Ok(data)
    } else {
        let records: BTreeMap<String, Vec<PackageInfo>> =
            serde_json::from_value(value).map_err(|error| error.to_string())?;
        Ok(StorageData {
            records,
            ..StorageData::default()
        })
    }
}

fn save_storage(data: &StorageData) -> Result<(), String> {
    ensure_storage_dirs()?;
    let content = serde_json::to_string_pretty(data).map_err(|error| error.to_string())?;
    fs::write(records_path()?, content).map_err(|error| error.to_string())
}

fn package_key(package: &PackageInfo) -> String {
    format!("{}:{}", package.manager, package.name)
}

fn snapshot_package(package: &PackageInfo) -> PackageInfo {
    PackageInfo {
        manager: package.manager.clone(),
        name: package.name.clone(),
        version: package.version.clone(),
        time: String::new(),
    }
}

fn command_output(command: &str, args: &[&str]) -> Option<String> {
    let output = Command::new(command).args(args).output().ok()?;
    if output.status.success() {
        Some(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        None
    }
}

fn is_available(command: &str) -> bool {
    command_output("which", &[command]).is_some()
}

fn scan_homebrew(scanned_at: &str) -> Vec<PackageInfo> {
    command_output("brew", &["list", "--versions"])
        .map(|output| {
            output
                .lines()
                .filter_map(|line| {
                    let mut parts = line.split_whitespace();
                    let name = parts.next()?;
                    let version = parts.next().unwrap_or("unknown");
                    Some(PackageInfo {
                        manager: "homebrew".to_string(),
                        name: name.to_string(),
                        version: version.to_string(),
                        time: scanned_at.to_string(),
                    })
                })
                .collect()
        })
        .unwrap_or_default()
}

fn scan_pip(scanned_at: &str) -> Vec<PackageInfo> {
    for command in ["pip3", "pip"] {
        if let Some(output) = command_output(command, &["list", "--format=json"]) {
            if let Ok(packages) = serde_json::from_str::<Vec<PipPackage>>(&output) {
                return packages
                    .into_iter()
                    .map(|package| PackageInfo {
                        manager: "pip".to_string(),
                        name: package.name,
                        version: package.version,
                        time: scanned_at.to_string(),
                    })
                    .collect();
            }
        }
    }
    Vec::new()
}

fn scan_npm(scanned_at: &str) -> Vec<PackageInfo> {
    command_output("npm", &["list", "-g", "--depth=0", "--json"])
        .and_then(|output| serde_json::from_str::<NpmList>(&output).ok())
        .map(|list| {
            list.dependencies
                .into_iter()
                .map(|(name, package)| PackageInfo {
                    manager: "npm".to_string(),
                    name,
                    version: if package.version.is_empty() {
                        "unknown".to_string()
                    } else {
                        package.version
                    },
                    time: scanned_at.to_string(),
                })
                .collect()
        })
        .unwrap_or_default()
}

fn scan_cargo(scanned_at: &str) -> Vec<PackageInfo> {
    command_output("cargo", &["install", "--list"])
        .map(|output| {
            output
                .lines()
                .filter_map(|line| {
                    if line.starts_with(' ') || line.trim().is_empty() {
                        return None;
                    }
                    let mut parts = line.split_whitespace();
                    let name = parts.next()?.trim_end_matches(':');
                    let version = parts.next().unwrap_or("unknown").trim_end_matches(':');
                    Some(PackageInfo {
                        manager: "cargo".to_string(),
                        name: name.to_string(),
                        version: version.to_string(),
                        time: scanned_at.to_string(),
                    })
                })
                .collect()
        })
        .unwrap_or_default()
}

fn scan_gem(scanned_at: &str) -> Vec<PackageInfo> {
    command_output("gem", &["list", "--local"])
        .map(|output| {
            output
                .lines()
                .filter_map(|line| {
                    let (name, versions) = line.split_once('(')?;
                    let version = versions.trim_end_matches(')').split(',').next().unwrap_or("unknown").trim();
                    Some(PackageInfo {
                        manager: "gem".to_string(),
                        name: name.trim().to_string(),
                        version: version.to_string(),
                        time: scanned_at.to_string(),
                    })
                })
                .collect()
        })
        .unwrap_or_default()
}

fn scan_go(scanned_at: &str) -> Vec<PackageInfo> {
    let Some(gopath) = command_output("go", &["env", "GOPATH"]) else {
        return Vec::new();
    };
    let bin_dir = PathBuf::from(gopath.trim()).join("bin");
    let Ok(entries) = fs::read_dir(bin_dir) else {
        return Vec::new();
    };

    entries
        .filter_map(|entry| {
            let entry = entry.ok()?;
            let metadata = entry.metadata().ok()?;
            if !metadata.is_file() {
                return None;
            }
            Some(PackageInfo {
                manager: "go".to_string(),
                name: entry.file_name().to_string_lossy().to_string(),
                version: "installed".to_string(),
                time: scanned_at.to_string(),
            })
        })
        .collect()
}

fn available_managers() -> Vec<String> {
    [
        ("homebrew", "brew"),
        ("pip", "pip3"),
        ("npm", "npm"),
        ("cargo", "cargo"),
        ("gem", "gem"),
        ("go", "go"),
    ]
    .into_iter()
    .filter_map(|(manager, command)| is_available(command).then(|| manager.to_string()))
    .collect()
}

fn scan_all_packages(scanned_at: &str) -> Vec<PackageInfo> {
    let mut packages = Vec::new();
    if is_available("brew") {
        packages.extend(scan_homebrew(scanned_at));
    }
    if is_available("pip3") || is_available("pip") {
        packages.extend(scan_pip(scanned_at));
    }
    if is_available("npm") {
        packages.extend(scan_npm(scanned_at));
    }
    if is_available("cargo") {
        packages.extend(scan_cargo(scanned_at));
    }
    if is_available("gem") {
        packages.extend(scan_gem(scanned_at));
    }
    if is_available("go") {
        packages.extend(scan_go(scanned_at));
    }
    packages
}

fn total_count(records: &BTreeMap<String, Vec<PackageInfo>>) -> usize {
    records
        .values()
        .flat_map(|packages| packages.iter().map(package_key))
        .collect::<HashSet<_>>()
        .len()
}

#[tauri::command]
fn get_app_state() -> Result<AppState, String> {
    let data = load_storage()?;
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
fn scan_packages() -> Result<ScanResult, String> {
    let scanned_at = now_minutes();
    let scanned_date = today();
    let packages = scan_all_packages(&scanned_at);
    let mut data = load_storage()?;
    let previous_keys = data
        .snapshot
        .packages
        .iter()
        .map(package_key)
        .collect::<HashSet<_>>();
    let has_baseline = data.snapshot.scanned_at.is_some() || data.metadata.last_scan_at.is_some();

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
        let mut existing_keys = day_records.iter().map(package_key).collect::<HashSet<_>>();
        for package in &new_packages {
            if existing_keys.insert(package_key(package)) {
                day_records.push(package.clone());
            }
        }
    }

    data.snapshot = Snapshot {
        packages: packages.iter().map(snapshot_package).collect(),
        scanned_at: Some(scanned_at.clone()),
    };
    data.metadata.schema_version = 2;
    data.metadata.last_scan_at = Some(scanned_at.clone());
    save_storage(&data)?;

    Ok(ScanResult {
        new_count: new_packages.len(),
        scanned_count: packages.len(),
        new_packages,
        is_initial_scan: !has_baseline,
        scanned_at,
    })
}

fn escape_html(value: &str) -> String {
    value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&#39;")
}

fn render_report(date: &str, packages: &[PackageInfo], total_unique: usize) -> String {
    let mut rows = String::new();
    for package in packages {
        rows.push_str(&format!(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>",
            escape_html(&package.manager),
            escape_html(&package.name),
            escape_html(&package.version),
            escape_html(&package.time)
        ));
    }

    if rows.is_empty() {
        rows = "<tr><td colspan=\"4\" class=\"empty\">今日暂无安装记录</td></tr>".to_string();
    }

    format!(
        r#"<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>包安装监控报告 - {date}</title>
  <style>
    body {{ margin: 0; background: #eef1f5; color: #1f2937; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 32px; }}
    header, section {{ background: #fff; border: 1px solid #dbe3ea; border-radius: 8px; margin-bottom: 16px; padding: 22px; }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    .meta {{ color: #64748b; }}
    .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
    .stat {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; }}
    .stat strong {{ display: block; font-size: 30px; margin-top: 6px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border-bottom: 1px solid #e2e8f0; padding: 12px; text-align: left; }}
    th {{ background: #f8fafc; color: #475569; }}
    .empty {{ color: #64748b; text-align: center; }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>包安装监控报告</h1>
      <div class="meta">{date} | 生成时间: {generated_at}</div>
    </header>
    <section class="stats">
      <div class="stat">当日新增<strong>{package_count}</strong></div>
      <div class="stat">历史总数<strong>{total_unique}</strong></div>
      <div class="stat">包管理器<strong>{manager_count}</strong></div>
    </section>
    <section>
      <table>
        <thead><tr><th>包管理器</th><th>包名</th><th>版本</th><th>安装时间</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </section>
  </main>
</body>
</html>"#,
        date = escape_html(date),
        generated_at = Local::now().format("%Y-%m-%d %H:%M:%S"),
        package_count = packages.len(),
        total_unique = total_unique,
        manager_count = packages
            .iter()
            .map(|package| package.manager.clone())
            .collect::<HashSet<_>>()
            .len(),
        rows = rows
    )
}

#[tauri::command]
fn get_scan_schedule(state: tauri::State<'_, Arc<Mutex<ScanSchedule>>>) -> ScanScheduleState {
    let schedule = state.lock().unwrap();
    ScanScheduleState {
        enabled: schedule.enabled,
        interval_hours: schedule.interval_hours,
        last_scan_at: schedule.last_scan_at.clone(),
    }
}

#[tauri::command]
fn start_scheduled_scan(
    app: tauri::AppHandle,
    state: tauri::State<'_, Arc<Mutex<ScanSchedule>>>,
    interval_hours: u32,
) -> Result<ScanScheduleState, String> {
    let mut schedule = state.lock().unwrap();
    schedule.enabled = true;
    schedule.interval_hours = interval_hours.max(1);
    
    let state_clone = Arc::clone(&state);
    let app_handle = app.clone();
    
    thread::spawn(move || {
        loop {
            {
                let schedule = state_clone.lock().unwrap();
                if !schedule.enabled {
                    break;
                }
            }
            
            thread::sleep(Duration::from_secs(3600 * interval_hours as u64));
            
            {
                let schedule = state_clone.lock().unwrap();
                if !schedule.enabled {
                    break;
                }
            }
            
            let _ = scan_packages_internal(&app_handle, &state_clone);
        }
    });
    
    Ok(ScanScheduleState {
        enabled: schedule.enabled,
        interval_hours: schedule.interval_hours,
        last_scan_at: schedule.last_scan_at.clone(),
    })
}

#[tauri::command]
fn stop_scheduled_scan(state: tauri::State<'_, Arc<Mutex<ScanSchedule>>>) -> ScanScheduleState {
    let mut schedule = state.lock().unwrap();
    schedule.enabled = false;
    ScanScheduleState {
        enabled: false,
        interval_hours: schedule.interval_hours,
        last_scan_at: schedule.last_scan_at.clone(),
    }
}

fn scan_packages_internal(
    _app: &tauri::AppHandle,
    schedule_state: &Arc<Mutex<ScanSchedule>>,
) -> Result<ScanResult, String> {
    let scanned_date = today();
    let scanned_at = now_minutes();
    let packages = scan_all_packages(&scanned_at);
    
    let mut data = load_storage()?;
    let previous_keys: HashSet<String> = data
        .snapshot
        .packages
        .iter()
        .map(package_key)
        .collect();
    
    let has_baseline = !data.snapshot.packages.is_empty() || data.metadata.last_scan_at.is_some();

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
        let mut existing_keys = day_records.iter().map(package_key).collect::<HashSet<_>>();
        for package in &new_packages {
            if existing_keys.insert(package_key(package)) {
                day_records.push(package.clone());
            }
        }
    }

    data.snapshot = Snapshot {
        packages: packages.iter().map(snapshot_package).collect(),
        scanned_at: Some(scanned_at.clone()),
    };
    data.metadata.schema_version = 2;
    data.metadata.last_scan_at = Some(scanned_at.clone());
    save_storage(&data)?;
    
    {
        let mut schedule = schedule_state.lock().unwrap();
        schedule.last_scan_at = Some(scanned_at.clone());
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
fn generate_report(app: tauri::AppHandle, date: String) -> Result<String, String> {
    let data = load_storage()?;
    let packages = data.records.get(&date).cloned().unwrap_or_default();
    let html = render_report(&date, &packages, total_count(&data.records));
    let path = reports_dir()?.join(format!("report_{}.html", date));

    fs::write(&path, html).map_err(|error| error.to_string())?;
    app.opener()
        .open_path(path.to_string_lossy().to_string(), None::<&str>)
        .map_err(|error| error.to_string())?;

    Ok(path.to_string_lossy().to_string())
}

fn main() {
    let scan_schedule = Arc::new(Mutex::new(ScanSchedule::default()));
    
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(scan_schedule)
        .invoke_handler(tauri::generate_handler![
            get_app_state,
            scan_packages,
            generate_report,
            get_scan_schedule,
            start_scheduled_scan,
            stop_scheduled_scan
        ])
        .run(tauri::generate_context!())
        .expect("error while running Package Monitor");
}
