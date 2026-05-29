use crate::models::PackageInfo;
use super::command_output;

pub fn scan(scanned_at: &str) -> Vec<PackageInfo> {
    command_output("gem", &["list", "--local"])
        .map(|output| {
            output
                .lines()
                .filter_map(|line| {
                    let (name, versions) = line.split_once('(')?;
                    let version = versions
                        .trim_end_matches(')')
                        .split(',')
                        .next()
                        .unwrap_or("unknown")
                        .trim();
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
