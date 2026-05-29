use crate::models::PackageInfo;
use super::command_output;

pub fn scan(scanned_at: &str) -> Vec<PackageInfo> {
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
