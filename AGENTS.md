# AGENTS.md

## 项目概述

Package Monitor 是一个 macOS 桌面应用，用于扫描 Homebrew、pip、npm、cargo、gem、go 等包管理器，记录每次扫描后新增安装的第三方包。

## 技术栈

- **后端**: Rust (Tauri 2)
- **前端**: Vue 3 + Vite + JavaScript
- **打包**: Tauri CLI

## 目录结构

```
├── src-tauri/          # Rust 后端
│   └── src/main.rs     # 主入口，包含扫描逻辑和 Tauri 命令
├── src/                # Vue 前端
│   ├── App.vue         # 主组件
│   ├── main.js         # 前端入口
│   ├── services.js     # 服务层
│   └── styles.css      # 全局样式
├── docs/               # 项目文档
│   ├── requirements/   # 需求文档
│   ├── design/         # 设计文档
│   ├── adr/            # 架构决策记录
│   ├── runbooks/       # 操作手册
│   └── meetings/       # 会议记录
├── tests/              # 测试
└── old_docs/           # 旧文档（归档）
```

## 开发规范

### Rust 后端

- 使用 `#[tauri::command]` 定义前端可调用的命令
- 扫描逻辑在 `src-tauri/src/main.rs` 中实现
- 使用 Tauri 事件系统（`app.emit()`）向前端发送实时日志
- 错误处理使用 `Result<T, String>` 类型

### Vue 前端

- 组件放在 `src/` 目录下
- 使用 Vue 3 Composition API
- 通过 `invoke()` 调用 Tauri 命令
- 监听 Tauri 事件实现实时更新

### 文档规范

- 文档放在 `docs/` 对应子目录
- 使用 `NNNN_slug.md` 命名格式
- 每份文档包含标准头部（状态、创建日期、更新日期）
- 详细规范见 docs/README.md

## 常用命令

```bash
# 开发模式（前端 + 后端）
npm run tauri:dev

# 仅前端调试
npm run dev

# 打包
npm run tauri:build
```

## 数据存储

- 安装记录: `~/.pkg-monitor/records.json`
- HTML 报告: `~/.pkg-monitor/reports/`

## 注意事项

- 首次扫描建立基线，不记录全量包
- 后续扫描只记录新增安装的包
- 扫描使用 30 秒超时，避免包管理器命令卡住
- 旧的 Python/Tkinter 文件保留在仓库中，仅供参考，不要修改
