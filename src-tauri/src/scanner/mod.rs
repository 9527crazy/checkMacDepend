pub mod homebrew;
pub mod cargo;
pub mod gem;
pub mod go;
pub mod npm;
pub mod pip;

use std::collections::HashSet;
use std::process::Command;

use crate::models::PackageInfo;

pub fn command_output(command: &str, args: &[&str]) -> Option<String> {
    let output = Command::new(command).args(args).output().ok()?;
    if output.status.success() {
        Some(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        None
    }
}

pub fn is_available(command: &str) -> bool {
    command_output("which", &[command]).is_some()
}

pub fn available_managers() -> Vec<String> {
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

pub fn package_key(package: &PackageInfo) -> String {
    format!("{}:{}", package.manager, package.name)
}

pub fn snapshot_package(package: &PackageInfo) -> PackageInfo {
    PackageInfo {
        manager: package.manager.clone(),
        name: package.name.clone(),
        version: package.version.clone(),
        time: String::new(),
    }
}

pub fn total_count(records: &std::collections::BTreeMap<String, Vec<PackageInfo>>) -> usize {
    records
        .values()
        .flat_map(|packages| packages.iter().map(package_key))
        .collect::<HashSet<_>>()
        .len()
}

pub fn scan_all_packages_with_log(
    app: &tauri::AppHandle,
    scanned_at: &str,
) -> Vec<PackageInfo> {
    crate::emit_log(app, "info", "开始扫描系统包...");

    let mut packages = Vec::new();

    let managers: Vec<(&str, &str, fn(&str) -> Vec<PackageInfo>)> = vec![
        ("homebrew", "brew", homebrew::scan),
        ("pip", "pip3", pip::scan),
        ("npm", "npm", npm::scan),
        ("cargo", "cargo", cargo::scan),
        ("gem", "gem", gem::scan),
        ("go", "go", go::scan),
    ];

    for (name, command, scan_fn) in &managers {
        if is_available(command) {
            crate::emit_log(app, "info", &format!("检测 {}...", name));
            let found = scan_fn(scanned_at);
            crate::emit_log(app, "info", &format!("{}: 找到 {} 个包", name, found.len()));
            packages.extend(found);
        } else {
            crate::emit_log(app, "warning", &format!("{}: 未安装，跳过", name));
        }
    }

    packages
}
