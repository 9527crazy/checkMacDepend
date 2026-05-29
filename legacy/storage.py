"""
Data storage module using JSON format
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Optional


class Storage:
    SCHEMA_VERSION = 2

    def __init__(self, records_path: str):
        self.records_path = records_path
        self.records = {}
        self.snapshot = {
            "packages": [],
            "scanned_at": None
        }
        self.metadata = {
            "schema_version": self.SCHEMA_VERSION,
            "last_scan_at": None
        }
        self.load()
    
    def load(self):
        """Load records from JSON file"""
        try:
            if os.path.exists(self.records_path):
                with open(self.records_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._load_data(data)
        except Exception as e:
            print(f"Warning: Could not load records: {e}")
            self.records = {}
            self.snapshot = {"packages": [], "scanned_at": None}
            self.metadata = {
                "schema_version": self.SCHEMA_VERSION,
                "last_scan_at": None
            }

    def _load_data(self, data: Dict):
        """Load both legacy date-indexed records and schema v2 data."""
        if not isinstance(data, dict):
            self.records = {}
            return

        if "records" in data or "snapshot" in data or "metadata" in data:
            self.records = data.get("records", {})
            self.snapshot = data.get("snapshot", {"packages": [], "scanned_at": None})
            self.metadata = data.get("metadata", {})
            self.metadata["schema_version"] = self.SCHEMA_VERSION
            self.metadata.setdefault("last_scan_at", self.snapshot.get("scanned_at"))
            self.snapshot.setdefault("packages", [])
            self.snapshot.setdefault("scanned_at", self.metadata.get("last_scan_at"))
            return

        # Legacy format: {"YYYY-MM-DD": [packages...]}
        self.records = data
    
    def save(self):
        """Save records to JSON file"""
        try:
            records_dir = os.path.dirname(self.records_path)
            if records_dir:
                os.makedirs(records_dir, exist_ok=True)
            with open(self.records_path, 'w', encoding='utf-8') as f:
                json.dump(self._to_data(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save records: {e}")

    def _to_data(self) -> Dict:
        """Serialize current storage state as schema v2."""
        self.metadata["schema_version"] = self.SCHEMA_VERSION
        return {
            "records": self.records,
            "snapshot": self.snapshot,
            "metadata": self.metadata
        }

    def _package_key(self, package: Dict):
        return (package.get("manager"), package.get("name"))

    def _snapshot_package(self, package: Dict) -> Dict:
        return {
            "manager": package.get("manager", "unknown"),
            "name": package.get("name", "unknown"),
            "version": package.get("version", "unknown")
        }
    
    def add_packages(self, date_str: str, packages: List[Dict]):
        """Add packages for a specific date"""
        if date_str not in self.records:
            self.records[date_str] = []
        
        # Avoid duplicates
        existing_keys = {(p['manager'], p['name']) for p in self.records[date_str]}
        
        for pkg in packages:
            key = (pkg['manager'], pkg['name'])
            if key not in existing_keys:
                self.records[date_str].append(pkg)
                existing_keys.add(key)
        
        self.save()

    def get_snapshot_packages(self) -> List[Dict]:
        """Get packages from the latest full scan snapshot."""
        return self.snapshot.get("packages", [])

    def get_last_scan_at(self) -> Optional[str]:
        """Get the latest scan timestamp."""
        return self.metadata.get("last_scan_at")

    def update_snapshot(self, packages: List[Dict], scanned_at: Optional[str] = None):
        """Replace the full package snapshot."""
        if scanned_at is None:
            scanned_at = datetime.now().strftime("%Y-%m-%d %H:%M")

        self.snapshot = {
            "packages": [self._snapshot_package(pkg) for pkg in packages],
            "scanned_at": scanned_at
        }
        self.metadata["schema_version"] = self.SCHEMA_VERSION
        self.metadata["last_scan_at"] = scanned_at
        self.save()

    def record_scan(self, date_str: str, packages: List[Dict], scanned_at: Optional[str] = None) -> Dict:
        """Record newly installed packages by comparing against the previous snapshot."""
        if scanned_at is None:
            scanned_at = datetime.now().strftime("%Y-%m-%d %H:%M")

        previous_packages = self.get_snapshot_packages()
        previous_keys = {self._package_key(pkg) for pkg in previous_packages}
        has_baseline = bool(self.snapshot.get("scanned_at") or self.metadata.get("last_scan_at"))

        new_packages = []
        if has_baseline:
            for package in packages:
                key = self._package_key(package)
                if key not in previous_keys:
                    package_copy = package.copy()
                    package_copy["time"] = scanned_at
                    new_packages.append(package_copy)

        if new_packages:
            if date_str not in self.records:
                self.records[date_str] = []

            existing_keys = {self._package_key(pkg) for pkg in self.records[date_str]}
            for package in new_packages:
                key = self._package_key(package)
                if key not in existing_keys:
                    self.records[date_str].append(package)
                    existing_keys.add(key)

        self.snapshot = {
            "packages": [self._snapshot_package(pkg) for pkg in packages],
            "scanned_at": scanned_at
        }
        self.metadata["schema_version"] = self.SCHEMA_VERSION
        self.metadata["last_scan_at"] = scanned_at
        self.save()

        return {
            "new_packages": new_packages,
            "new_count": len(new_packages),
            "scanned_count": len(packages),
            "is_initial_scan": not has_baseline,
            "scanned_at": scanned_at
        }
    
    def get_packages(self, date_str: str) -> List[Dict]:
        """Get packages for a specific date"""
        return self.records.get(date_str, [])
    
    def get_all_dates(self) -> List[str]:
        """Get all dates with records, sorted descending"""
        return sorted(self.records.keys(), reverse=True)
    
    def get_recent_dates(self, days: int = 30) -> List[str]:
        """Get recent dates with records"""
        all_dates = self.get_all_dates()
        return all_dates[:days]
    
    def get_total_count(self) -> int:
        """Get total number of unique packages across all dates"""
        all_packages = set()
        for date_packages in self.records.values():
            for pkg in date_packages:
                all_packages.add((pkg['manager'], pkg['name']))
        return len(all_packages)
    
    def search_packages(self, query: str, date_str: Optional[str] = None) -> List[Dict]:
        """Search packages by name"""
        query = query.lower()
        results = []
        
        if date_str:
            packages = self.get_packages(date_str)
            for pkg in packages:
                if query in pkg['name'].lower() or query in pkg['manager'].lower():
                    results.append(pkg)
        else:
            for date, packages in self.records.items():
                for pkg in packages:
                    if query in pkg['name'].lower() or query in pkg['manager'].lower():
                        pkg_copy = pkg.copy()
                        pkg_copy['date'] = date
                        results.append(pkg_copy)
        
        return results
    
    def get_manager_stats(self) -> Dict[str, int]:
        """Get package count by manager"""
        stats = {}
        for date_packages in self.records.values():
            for pkg in date_packages:
                manager = pkg['manager']
                stats[manager] = stats.get(manager, 0) + 1
        return stats
