"""
Data storage module using JSON format
"""
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class Storage:
    def __init__(self, records_path: str):
        self.records_path = records_path
        self.records = {}
        self.load()
    
    def load(self):
        """Load records from JSON file"""
        try:
            if os.path.exists(self.records_path):
                with open(self.records_path, 'r', encoding='utf-8') as f:
                    self.records = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load records: {e}")
            self.records = {}
    
    def save(self):
        """Save records to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.records_path), exist_ok=True)
            with open(self.records_path, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save records: {e}")
    
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
