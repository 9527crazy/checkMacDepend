---
title: 菜单栏图标设计
status: 待确认
---

# 菜单栏图标（Menu Bar Extra）

## 概述

在 macOS 菜单栏（右上角）添加一个状态栏图标，用户点击后可以快速查看最近扫描新增的包，无需打开主窗口。

## 图标方案

预览文件：`docs/icons/preview.html`

### 方案1: 简洁盒子
经典包管理器意象，辨识度高。

### 方案2: 打开的包裹
立体感，类似 npm 风格。

### 方案3: 终端
命令行风格，呼应扫描功能。

### 方案4: 网格
模块化，现代感。

### 方案5: 堆叠层
层次感，类似图层概念。

## 点击行为

点击图标显示一个 **Popover**，内容包含：

```
┌─────────────────────────────────┐
│  Package Monitor          [×]   │
├─────────────────────────────────┤
│  上次扫描: 2024-01-15 14:30    │
│  新增包: 5 个                   │
├─────────────────────────────────┤
│  ● homebrew   curl              │
│  ● pip        requests          │
│  ● npm        vite              │
│  ● cargo      ripgrep           │
│  ● go         glow              │
├─────────────────────────────────┤
│  [打开主窗口]        [立即扫描]  │
└─────────────────────────────────┘
```

## 右键菜单

- 打开主窗口
- 立即扫描
- ---
- 退出应用

## 实现方案

### Tauri 2 系统托盘

```rust
// Cargo.toml 添加 feature
tauri = { version = "2", features = ["tray-icon"] }

// main.rs
use tauri::tray::{TrayIconBuilder, MouseButton, MouseButtonState};
use tauri::menu::{MenuBuilder, MenuItemBuilder};
```

### 文件变更

| 文件 | 变更 |
|------|------|
| `src-tauri/Cargo.toml` | 启用 `tray-icon` feature |
| `src-tauri/src/main.rs` | 添加系统托盘初始化、菜单构建、事件处理 |
| `src-tauri/icons/iconTemplate.png` | 托盘图标（PNG 22x22pt） |

### 状态共享

主窗口和托盘之间需要同步：
- `last_scan_at`：上次扫描时间
- `new_packages_count`：新增包数量
- `new_packages_list`：新增包列表

使用 `Arc<Mutex<>>` 共享状态。
