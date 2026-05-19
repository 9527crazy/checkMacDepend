# Package Monitor - 包安装监控工具

一个 macOS 桌面应用，用于监控和展示每天安装的第三方包。

## 功能特性

- 📦 支持主流包管理器：Homebrew、pip、npm、cargo、gem、go
- 📅 按日期浏览历史安装记录
- 🔍 实时搜索过滤
- 📊 生成美观的 HTML 报告
- 💾 JSON 格式存储，便于查看和备份

## 安装

```bash
# 进入项目目录
cd pkg-monitor

# 安装依赖
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 使用说明

1. **启动扫描**：点击"立即扫描"按钮，工具会自动检测系统中已安装的包
2. **浏览历史**：左侧日期列表可切换不同日期查看
3. **搜索过滤**：在搜索框中输入关键词实时过滤
4. **生成报告**：点击"生成报告"按钮，自动生成 HTML 报告并在浏览器中打开

## 数据存储

- 配置文件：`~/.pkg-monitor/config.json`
- 安装记录：`~/.pkg-monitor/records.json`
- HTML 报告：`~/.pkg-monitor/reports/`

## 配置选项

编辑 `~/.pkg-monitor/config.json`：

```json
{
  "scan_interval_hours": 24,
  "auto_scan_on_startup": true,
  "show_notifications": true,
  "enabled_managers": ["homebrew", "pip", "npm", "cargo", "gem", "go"]
}
```

## 支持的包管理器

| 包管理器 | 说明 |
|---------|------|
| Homebrew | macOS 包管理器 |
| pip/pip3 | Python 包管理器 |
| npm | Node.js 包管理器 |
| cargo | Rust 包管理器 |
| gem | Ruby 包管理器 |
| go | Go 语言工具 |

## 系统要求

- macOS 10.15+
- Python 3.8+
- tkinter（通常随 Python 一起安装）
