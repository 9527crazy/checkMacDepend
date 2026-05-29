use crate::models::PackageInfo;
use super::command_output;

pub fn scan(scanned_at: &str) -> Vec<PackageInfo> {
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
