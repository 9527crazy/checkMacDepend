use crate::models::{PackageInfo, PipPackage};
use super::command_output;

pub fn scan(scanned_at: &str) -> Vec<PackageInfo> {
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
