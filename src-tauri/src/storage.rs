use std::collections::BTreeMap;
use std::fs::{self, OpenOptions};
use std::io::{Read, Write};
use std::path::PathBuf;

use crate::models::{PackageInfo, StorageData};

pub fn storage_dir() -> Result<PathBuf, String> {
    let home = dirs::home_dir().ok_or_else(|| "无法定位用户主目录".to_string())?;
    Ok(home.join(".pkg-monitor"))
}

pub fn records_path() -> Result<PathBuf, String> {
    Ok(storage_dir()?.join("records.json"))
}

pub fn reports_dir() -> Result<PathBuf, String> {
    Ok(storage_dir()?.join("reports"))
}

pub fn ensure_storage_dirs() -> Result<(), String> {
    fs::create_dir_all(storage_dir()?).map_err(|e| e.to_string())?;
    fs::create_dir_all(reports_dir()?).map_err(|e| e.to_string())?;
    Ok(())
}

pub fn load_storage() -> Result<StorageData, String> {
    ensure_storage_dirs()?;
    let path = records_path()?;

    let mut file = OpenOptions::new()
        .read(true)
        .create(true)
        .write(true)
        .truncate(false)
        .open(&path)
        .map_err(|e| e.to_string())?;

    fs2::FileExt::lock_shared(&file).map_err(|e| e.to_string())?;

    let mut content = String::new();
    file.read_to_string(&mut content).map_err(|e| e.to_string())?;
    fs2::FileExt::unlock(&file).map_err(|e| e.to_string())?;

    if content.is_empty() {
        return Ok(StorageData::default());
    }

    let value: serde_json::Value =
        serde_json::from_str(&content).map_err(|e| e.to_string())?;

    if value.get("records").is_some()
        || value.get("snapshot").is_some()
        || value.get("metadata").is_some()
    {
        let mut data: StorageData =
            serde_json::from_value(value).map_err(|e| e.to_string())?;
        data.metadata.schema_version = 2;
        if data.metadata.last_scan_at.is_none() {
            data.metadata.last_scan_at = data.snapshot.scanned_at.clone();
        }
        Ok(data)
    } else {
        let records: BTreeMap<String, Vec<PackageInfo>> =
            serde_json::from_value(value).map_err(|e| e.to_string())?;
        Ok(StorageData {
            records,
            ..StorageData::default()
        })
    }
}

pub fn save_storage(data: &StorageData) -> Result<(), String> {
    ensure_storage_dirs()?;
    let path = records_path()?;
    let content = serde_json::to_string_pretty(data).map_err(|e| e.to_string())?;

    let mut file = OpenOptions::new()
        .create(true)
        .write(true)
        .truncate(true)
        .open(&path)
        .map_err(|e| e.to_string())?;

    fs2::FileExt::lock_exclusive(&file).map_err(|e| e.to_string())?;
    file.write_all(content.as_bytes())
        .map_err(|e| e.to_string())?;
    file.flush().map_err(|e| e.to_string())?;
    fs2::FileExt::unlock(&file).map_err(|e| e.to_string())?;

    Ok(())
}
