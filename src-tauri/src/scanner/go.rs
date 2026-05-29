use crate::models::PackageInfo;
use std::fs;
use std::path::PathBuf;
use super::command_output;

pub fn scan(scanned_at: &str) -> Vec<PackageInfo> {
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
