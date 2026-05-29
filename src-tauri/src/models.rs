use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PackageInfo {
    pub manager: String,
    pub name: String,
    pub version: String,
    #[serde(default)]
    pub time: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Snapshot {
    pub packages: Vec<PackageInfo>,
    pub scanned_at: Option<String>,
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
pub struct Metadata {
    pub schema_version: u8,
    pub last_scan_at: Option<String>,
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
pub struct StorageData {
    pub records: BTreeMap<String, Vec<PackageInfo>>,
    pub snapshot: Snapshot,
    pub metadata: Metadata,
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
pub struct AppState {
    pub dates: Vec<String>,
    pub records: BTreeMap<String, Vec<PackageInfo>>,
    pub total_count: usize,
    pub last_scan_at: Option<String>,
    pub available_managers: Vec<String>,
}

#[derive(Debug, Serialize)]
pub struct ScanResult {
    pub new_packages: Vec<PackageInfo>,
    pub new_count: usize,
    pub scanned_count: usize,
    pub is_initial_scan: bool,
    pub scanned_at: String,
}

#[derive(Debug, Deserialize)]
pub struct PipPackage {
    pub name: String,
    pub version: String,
}

#[derive(Debug, Deserialize)]
pub struct NpmList {
    #[serde(default)]
    pub dependencies: std::collections::HashMap<String, NpmPackage>,
}

#[derive(Debug, Deserialize)]
pub struct NpmPackage {
    #[serde(default)]
    pub version: String,
}

#[derive(Debug, Serialize)]
pub struct ScanScheduleState {
    pub enabled: bool,
    pub interval_hours: u32,
    pub last_scan_at: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct ScanLogPayload {
    pub timestamp: String,
    pub level: String,
    pub message: String,
}
