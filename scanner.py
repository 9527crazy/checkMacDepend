"""
Package manager scanners for macOS
"""
import os
import subprocess
import json
from datetime import datetime
from typing import List, Dict, Optional


class PackageScanner:
    """Base class for package scanners"""
    
    def __init__(self, name: str):
        self.name = name
    
    def is_available(self) -> bool:
        """Check if this package manager is installed"""
        raise NotImplementedError
    
    def scan(self) -> List[Dict]:
        """Scan installed packages"""
        raise NotImplementedError
    
    def _run_command(self, cmd: List[str]) -> Optional[str]:
        """Run a command and return output"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            print(f"Command failed: {' '.join(cmd)}: {e}")
        return None


class HomebrewScanner(PackageScanner):
    """Homebrew package scanner"""
    
    def __init__(self):
        super().__init__("homebrew")
    
    def is_available(self) -> bool:
        return self._run_command(["which", "brew"]) is not None
    
    def scan(self) -> List[Dict]:
        packages = []
        
        # Scan formulae
        output = self._run_command(["brew", "list", "--versions"])
        if output:
            for line in output.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        name = parts[0]
                        version = parts[1] if len(parts) > 1 else "unknown"
                        packages.append({
                            "manager": "homebrew",
                            "name": name,
                            "version": version,
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
        
        return packages


class PipScanner(PackageScanner):
    """pip/pip3 package scanner"""
    
    def __init__(self):
        super().__init__("pip")
    
    def is_available(self) -> bool:
        return (self._run_command(["which", "pip3"]) is not None or 
                self._run_command(["which", "pip"]) is not None)
    
    def scan(self) -> List[Dict]:
        packages = []
        
        # Try pip3 first, then pip
        for pip_cmd in ["pip3", "pip"]:
            output = self._run_command([pip_cmd, "list", "--format=json"])
            if output:
                try:
                    pkg_list = json.loads(output)
                    for pkg in pkg_list:
                        packages.append({
                            "manager": "pip",
                            "name": pkg.get('name', 'unknown'),
                            "version": pkg.get('version', 'unknown'),
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                    break  # Success, no need to try other pip
                except json.JSONDecodeError:
                    continue
        
        return packages


class NpmScanner(PackageScanner):
    """npm package scanner"""
    
    def __init__(self):
        super().__init__("npm")
    
    def is_available(self) -> bool:
        return self._run_command(["which", "npm"]) is not None
    
    def scan(self) -> List[Dict]:
        packages = []
        
        output = self._run_command(["npm", "list", "-g", "--depth=0", "--json"])
        if output:
            try:
                data = json.loads(output)
                deps = data.get('dependencies', {})
                for name, info in deps.items():
                    version = info.get('version', 'unknown')
                    packages.append({
                        "manager": "npm",
                        "name": name,
                        "version": version,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
            except json.JSONDecodeError:
                pass
        
        return packages


class CargoScanner(PackageScanner):
    """Cargo (Rust) package scanner"""
    
    def __init__(self):
        super().__init__("cargo")
    
    def is_available(self) -> bool:
        return self._run_command(["which", "cargo"]) is not None
    
    def scan(self) -> List[Dict]:
        packages = []
        
        output = self._run_command(["cargo", "install", "--list"])
        if output:
            lines = output.strip().split('\n')
            current_pkg = None
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith(' '):
                    # Package line: "package_name version:"
                    parts = line.split()
                    if parts:
                        current_pkg = parts[0].rstrip(':')
                        version = parts[1] if len(parts) > 1 else "unknown"
                        packages.append({
                            "manager": "cargo",
                            "name": current_pkg,
                            "version": version,
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
        
        return packages


class GemScanner(PackageScanner):
    """Ruby gem package scanner"""
    
    def __init__(self):
        super().__init__("gem")
    
    def is_available(self) -> bool:
        return self._run_command(["which", "gem"]) is not None
    
    def scan(self) -> List[Dict]:
        packages = []
        
        output = self._run_command(["gem", "list", "--local"])
        if output:
            for line in output.strip().split('\n'):
                if line and '(' in line:
                    # Format: "package_name (version1, version2)"
                    name_part = line.split('(')[0].strip()
                    version_part = line.split('(')[1].rstrip(')')
                    version = version_part.split(',')[0].strip()
                    
                    packages.append({
                        "manager": "gem",
                        "name": name_part,
                        "version": version,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
        
        return packages


class GoScanner(PackageScanner):
    """Go package scanner"""
    
    def __init__(self):
        super().__init__("go")
    
    def is_available(self) -> bool:
        return self._run_command(["which", "go"]) is not None
    
    def scan(self) -> List[Dict]:
        packages = []
        
        # Get GOPATH
        gopath_output = self._run_command(["go", "env", "GOPATH"])
        if gopath_output:
            gopath = gopath_output.strip()
            bin_dir = os.path.join(gopath, "bin")
            
            if os.path.exists(bin_dir):
                for item in os.listdir(bin_dir):
                    item_path = os.path.join(bin_dir, item)
                    if os.path.isfile(item_path) and os.access(item_path, os.X_OK):
                        packages.append({
                            "manager": "go",
                            "name": item,
                            "version": "installed",
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
        
        return packages


class ScannerManager:
    """Manages all package scanners"""
    
    def __init__(self, enabled_managers: List[str] = None):
        self.scanners = {
            "homebrew": HomebrewScanner(),
            "pip": PipScanner(),
            "npm": NpmScanner(),
            "cargo": CargoScanner(),
            "gem": GemScanner(),
            "go": GoScanner()
        }
        
        if enabled_managers:
            self.enabled_managers = [m for m in enabled_managers if m in self.scanners]
        else:
            self.enabled_managers = list(self.scanners.keys())
    
    def scan_all(self, progress_callback=None) -> List[Dict]:
        """Scan all enabled package managers"""
        all_packages = []
        
        for i, manager_name in enumerate(self.enabled_managers):
            scanner = self.scanners.get(manager_name)
            if scanner and scanner.is_available():
                if progress_callback:
                    progress_callback(f"Scanning {manager_name}...", i, len(self.enabled_managers))
                
                try:
                    packages = scanner.scan()
                    all_packages.extend(packages)
                except Exception as e:
                    print(f"Error scanning {manager_name}: {e}")
        
        return all_packages
    
    def get_available_managers(self) -> List[str]:
        """Get list of available package managers"""
        available = []
        for name, scanner in self.scanners.items():
            if scanner.is_available():
                available.append(name)
        return available
