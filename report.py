"""
HTML Report Generator using Jinja2
"""
import os
from datetime import datetime
from typing import List, Dict
from jinja2 import Template


# HTML Template for the report
REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>包安装监控报告 - {{ date }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        
        .header h1 {
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }
        
        .header .date {
            color: #666;
            font-size: 16px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .stat-card .number {
            font-size: 48px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .stat-card .label {
            color: #666;
            font-size: 14px;
            margin-top: 10px;
        }
        
        .section {
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        
        .section h2 {
            color: #333;
            font-size: 22px;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .manager-section {
            margin-bottom: 30px;
        }
        
        .manager-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        
        .manager-icon {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 15px;
            font-weight: bold;
            color: white;
        }
        
        .manager-icon.brew { background: #fbb040; }
        .manager-icon.pip { background: #3776ab; }
        .manager-icon.npm { background: #cb3837; }
        .manager-icon.cargo { background: #dea584; }
        .manager-icon.gem { background: #cc342d; }
        .manager-icon.go { background: #00add8; }
        
        .manager-name {
            font-size: 18px;
            font-weight: 600;
            color: #333;
        }
        
        .manager-count {
            margin-left: auto;
            background: #e9ecef;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 14px;
            color: #666;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        
        th {
            background: #f8f9fa;
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
            color: #555;
            font-size: 14px;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
            color: #333;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        .package-name {
            font-weight: 500;
        }
        
        .version {
            color: #667eea;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
            font-size: 13px;
        }
        
        .time {
            color: #999;
            font-size: 13px;
        }
        
        .footer {
            text-align: center;
            color: white;
            padding: 20px;
            font-size: 14px;
            opacity: 0.8;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #999;
        }
        
        .empty-state svg {
            width: 80px;
            height: 80px;
            margin-bottom: 20px;
            opacity: 0.5;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📦 包安装监控报告</h1>
            <div class="date">{{ date }} | 生成时间: {{ generated_at }}</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="number">{{ total_packages }}</div>
                <div class="label">今日安装包数</div>
            </div>
            <div class="stat-card">
                <div class="number">{{ manager_count }}</div>
                <div class="label">包管理器</div>
            </div>
            <div class="stat-card">
                <div class="number">{{ total_unique }}</div>
                <div class="label">历史总包数</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 今日安装详情</h2>
            
            {% if packages %}
                {% for manager, manager_packages in packages_by_manager.items() %}
                <div class="manager-section">
                    <div class="manager-header">
                        <div class="manager-icon {{ manager[:3] }}">
                            {{ manager[0]|upper }}
                        </div>
                        <div class="manager-name">{{ manager }}</div>
                        <div class="manager-count">{{ manager_packages|length }} 个包</div>
                    </div>
                    
                    <table>
                        <thead>
                            <tr>
                                <th>包名</th>
                                <th>版本</th>
                                <th>安装时间</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for pkg in manager_packages %}
                            <tr>
                                <td class="package-name">{{ pkg.name }}</td>
                                <td class="version">{{ pkg.version }}</td>
                                <td class="time">{{ pkg.time }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% endfor %}
            {% else %}
                <div class="empty-state">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                        <circle cx="12" cy="7" r="4"></circle>
                    </svg>
                    <p>今日暂无安装记录</p>
                </div>
            {% endif %}
        </div>
        
        <div class="footer">
            由 Package Monitor 自动生成 | {{ generated_at }}
        </div>
    </div>
</body>
</html>
"""


class ReportGenerator:
    """Generate HTML reports from package data"""
    
    def __init__(self, reports_dir: str):
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)
    
    def generate(self, date_str: str, packages: List[Dict], total_unique: int = 0) -> str:
        """Generate HTML report for a specific date"""
        
        # Group packages by manager
        packages_by_manager = {}
        for pkg in packages:
            manager = pkg['manager']
            if manager not in packages_by_manager:
                packages_by_manager[manager] = []
            packages_by_manager[manager].append(pkg)
        
        # Render template
        template = Template(REPORT_TEMPLATE)
        html = template.render(
            date=date_str,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_packages=len(packages),
            manager_count=len(packages_by_manager),
            total_unique=total_unique,
            packages=packages,
            packages_by_manager=packages_by_manager
        )
        
        # Save to file
        filename = f"report_{date_str}.html"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return filepath
