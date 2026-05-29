#!/usr/bin/env python3
"""
Package Monitor - macOS 第三方包安装监控工具

一个用于监控和展示每天安装的第三方包的 GUI 桌面应用。
支持 Homebrew、pip、npm、cargo、gem、go 等主流包管理器。

安装依赖:
    pip install -r requirements.txt

运行:
    python main.py
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from storage import Storage
from scanner import ScannerManager
from report import ReportGenerator
from ui import PackageMonitorUI


def main():
    """Main entry point"""
    print("=" * 50)
    print("Package Monitor - 包安装监控工具")
    print("=" * 50)
    
    # Initialize configuration
    config = Config()
    print(f"配置文件: {config.config_path}")
    print(f"数据存储: {config.records_path}")
    print(f"报告目录: {config.reports_path}")
    
    # Initialize storage
    storage = Storage(config.records_path)
    
    # Initialize scanner
    scanner_manager = ScannerManager(config.get("enabled_managers"))
    available = scanner_manager.get_available_managers()
    print(f"可用的包管理器: {', '.join(available)}")
    
    # Initialize report generator
    report_generator = ReportGenerator(config.reports_path)
    
    # Launch GUI
    print("\n正在启动图形界面...")
    app = PackageMonitorUI(scanner_manager, storage, report_generator, config)
    app.run()


if __name__ == "__main__":
    main()
