# Package Monitor

一个 macOS 桌面应用，用于扫描 Homebrew、pip、npm、cargo、gem、go 等包管理器，并记录每次扫描后新增安装的第三方包。

当前主版本已迁移为 Tauri + JavaScript + Vue 3。旧的 Python/Tkinter 文件仍保留在仓库中，方便对照迁移逻辑。

## 技术栈

- Tauri 2
- Vue 3
- Vite
- JavaScript
- Rust

## 环境要求

- Node.js 18+
- npm
- Rust/Cargo
- macOS

安装 Rust：

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

## 安装依赖

```bash
npm install
```

## 开发启动

```bash
npm run tauri:dev
```

只启动前端调试页面：

```bash
npm run dev
```

## 打包

```bash
npm run tauri:build
```

## 数据存储

- 安装记录：`~/.pkg-monitor/records.json`
- HTML 报告：`~/.pkg-monitor/reports/`

## 功能

- 扫描当前系统中已安装的第三方包
- 首次扫描建立基线，后续扫描只记录新增安装包
- 按日期查看历史新增记录
- 搜索包名或包管理器
- 生成并打开 HTML 报告
