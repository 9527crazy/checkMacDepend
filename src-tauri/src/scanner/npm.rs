use crate::models::{PackageInfo, NpmList};
use super::command_output;

pub fn scan(scanned_at: &str) -> Vec<PackageInfo> {
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
