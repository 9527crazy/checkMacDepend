## 状态: 草稿
创建: 2026-05-29
负责人: 
相关: docs/design/0003-menu-bar-extra.md, src-tauri/src/main.rs

---

# 需求三则：包来源追踪、状态检测、菜单栏摘要

## 背景

当前 `PackageInfo` 仅记录 `manager / name / version / time`，表格展示四列。用户反馈：

1. 不知道包装在哪个目录、由谁安装的
2. 不知道已记录的包是否还在磁盘上
3. 打开主窗口才能看到当天新增，菜单栏只显示简要文字

本次需求围绕这三个痛点展开设计。

---

## 需求一：表格增加来源列

### 1.1 目标

在主表格和 HTML 报告中新增两列：

| 新增列 | 含义 | 示例 |
|--------|------|------|
| **来源目录** (source_dir) | 包安装到的根目录 | `/opt/homebrew/Cellar`、`~/.local/lib/python3.11/site-packages` |
| **安装方式** (install_method) | 是谁/什么工具下载安装的 | `brew install`、`pip install`、`cargo install`、`brew cask` |

### 1.2 数据模型变更

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
struct PackageInfo {
    manager: String,        // homebrew / pip / npm / cargo / gem / go
    name: String,
    version: String,
    #[serde(default)]
    time: String,           // 扫描时间 (YYYY-MM-DD HH:MM)
    #[serde(default)]
    source_dir: String,     // 新增：包安装根目录
    #[serde(default)]
    install_method: String, // 新增：安装方式描述
}
```

> Schema 版本升至 `3`，旧数据自动迁移（新增字段默认空字符串）。

### 1.3 各管理器采集逻辑

| 管理器 | source_dir 来源 | install_method |
|--------|----------------|----------------|
| **homebrew** | `brew --cellar` 返回的路径 | 判断 `brew list --cask` 是否命中 → `brew install` / `brew install --cask` |
| **pip** | `python3 -c "import site; print(site.getsitepackages())"` 取第一个 | 固定 `pip install` |
| **npm** | `npm root -g` | 固定 `npm install -g` |
| **cargo** | `cargo install --list` 解析路径或 `$HOME/.cargo/bin` | 固定 `cargo install` |
| **gem** | `gem environment gemdir` + `/gems/<name>-<ver>` | 固定 `gem install` |
| **go** | `$GOPATH/bin` | 固定 `go install` |

### 1.4 UI 变更

主表格从 4 列扩展为 6 列：

```
管理器 | 包名 | 版本 | 来源目录 | 安装方式 | 时间
```

- 来源目录列：单行超长截断，悬停 tooltip 显示完整路径
- 安装方式列：使用小标签 (badge) 样式
- 列宽分配：管理器 80px | 包名 auto | 版本 100px | 来源目录 220px | 安装方式 120px | 时间 130px

### 1.5 HTML 报告变更

报告表格同步增加两列，样式保持一致。

---

## 需求二：包状态检测

### 2.1 目标

新增一列 **状态**，指示该包当前是否仍在磁盘上。

### 2.2 状态定义

| 状态值 | 含义 | UI 表现 |
|--------|------|---------|
| `installed` | 包目录存在且可访问 | 绿色圆点 + "已安装" |
| `missing` | 包目录不存在 | 红色圆点 + "已移除" |
| `unknown` | 无法判断（无路径信息） | 灰色圆点 + "未知" |

### 2.3 检测逻辑

扫描时对每个包执行一次 `Path::new(source_dir).exists()` 检查：

```rust
fn check_package_status(source_dir: &str, name: &str) -> String {
    if source_dir.is_empty() {
        return "unknown".to_string();
    }
    let path = PathBuf::from(source_dir).join(name);
    if path.exists() {
        "installed".to_string()
    } else {
        "missing".to_string()
    }
}
```

- 检测在 `scan_all_packages_with_log` 中每个包采集完毕后立即执行
- 结果写入 `PackageInfo` 新字段 `status`
- 仅做文件系统 `exists()` 检查，不做深度校验（如 ELF 可执行性），控制扫描耗时

### 2.4 数据模型变更

```rust
struct PackageInfo {
    // ... 现有字段 ...
    #[serde(default)]
    source_dir: String,
    #[delegate(default)]
    install_method: String,
    #[serde(default)]
    status: String,         // 新增：installed / missing / unknown
}
```

### 2.5 UI 变更

表格新增状态列，位于管理器之后：

```
管理器 | 状态 | 包名 | 版本 | 来源目录 | 安装方式 | 时间
```

状态列使用圆点 + 文字组合：

```html
<td class="status">
  <span class="status-dot installed"></span>
  已安装
</td>
```

CSS：

```css
.status-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 6px;
}
.status-dot.installed { background: #34C759; }
.status-dot.missing   { background: #FF3B30; }
.status-dot.unknown   { background: #C7C7CC; }
```

### 2.6 HTML 报告变更

报告表格同步增加状态列，使用相同的圆点样式。

### 2.7 向后兼容

- 旧版 records.json 中的包无 `status` 字段，前端显示为 "未知"
- 首次升级后自动在下次扫描时填充状态

---

## 需求三：菜单栏摘要表格

### 3.1 目标

在 macOS 菜单栏图标点击弹出的 popover 中，展示一个精简表格，内容对应报告的统计摘要部分：

- 今日新增包列表（数量 + 前 5 条）
- 历史累计总数

用户无需打开主窗口即可快速了解安装变化。

### 3.2 Popover 布局更新

```
┌──────────────────────────────────────┐
│  Package Monitor                     │
│  上次扫描: 2026-05-29 14:30         │
├──────────────────────────────────────┤
│  ┌──────────┬──────────┬──────────┐  │
│  │ 今日新增 │ 历史总数 │ 状态异常 │  │
│  │    5     │   142    │    2     │  │
│  └──────────┴──────────┴──────────┘  │
├──────────────────────────────────────┤
│  今日新增包                           │
│  ● homebrew  curl        已安装      │
│  ● pip       requests    已安装      │
│  ● npm       vite        已安装      │
│  ● cargo     ripgrep     已安装      │
│  ● go        glow        已安装      │
│  ... (共 5 个)                       │
├──────────────────────────────────────┤
│  状态异常 (2)                        │
│  ● pip   old-pkg       已移除       │
│  ● npm   deprecated    已移除       │
├──────────────────────────────────────┤
│  [打开主窗口]          [立即扫描]    │
└──────────────────────────────────────┘
```

### 3.3 数据流

```mermaid
graph LR
    A[扫描完成] --> B[更新 records.json]
    B --> C[emit menu-bar-update 事件]
    C --> D[前端接收并缓存]
    D --> E[菜单栏 popover 渲染]
```

- 扫描完成后，`scan_packages_internal` 通过 `app.emit("menu-bar-update", payload)` 发送最新数据
- 前端监听该事件，更新 popover 内容
- 托盘点击时直接读取缓存数据，无需等待

### 3.4 Payload 结构

```typescript
interface MenuBarPayload {
  last_scan_at: string
  today_count: number
  today_packages: PackageInfo[]   // 今日新增，最多展示前 10 条
  history_total: number           // 历史累计包总数
  missing_count: number           // 状态异常数
  missing_packages: PackageInfo[] // 状态异常列表，最多展示前 5 条
}
```

### 3.5 实现约束

- Tauri 2 的 `TrayIcon` 仅支持原生菜单（`Menu`），不支持自定义 HTML popover
- 实现方案：使用 **子窗口（webview window）** 作为 popover，设置 `decorations: false`、`always_on_top: true`、`skip_taskbar: true`，点击托盘图标时在图标下方弹出

```rust
// 创建 popover 窗口
let popover = app.get_webview_window("popover").unwrap_or_else(|| {
    WebviewWindowBuilder::new(app, "popover", WebviewUrl::App("popover.html".into()))
        .title("Package Monitor")
        .inner_size(340, 420)
        .decorations(false)
        .always_on_top(true)
        .skip_taskbar(true)
        .resizable(false)
        .build().unwrap()
});
```

- 点击 popover 外部时自动关闭（监听失焦事件）
- 主窗口显示时隐藏 popover，避免重叠

### 3.6 文件变更清单

| 文件 | 变更 |
|------|------|
| `src-tauri/src/main.rs` | `PackageInfo` 新增字段、扫描函数补充采集逻辑、菜单栏更新事件 |
| `src/App.vue` | 表格增加来源列、状态列、样式调整 |
| `src/popover.vue` | 新增：菜单栏 popover 页面 |
| `src-tauri/tauri.conf.json` | 新增 `popover` 窗口配置 |
| `src/router.ts` | 新增 popover 路由（如使用 SPA） |

---

## Schema 迁移策略

### 版本 2 → 3

```rust
fn migrate_schema_v2_to_v3(data: &mut StorageData) {
    for (_date, packages) in data.records.iter_mut() {
        for pkg in packages.iter_mut() {
            if pkg.source_dir.is_empty() && pkg.status.is_empty() {
                // 旧数据：根据 manager 填充默认值
                pkg.status = "unknown".to_string();
            }
        }
    }
    data.metadata.schema_version = 3;
}
```

- 迁移在 `load_storage` 中自动执行
- 旧数据不丢失，新字段填充默认值
- 下次扫描时覆盖为真实值

---

## 实施优先级

| 优先级 | 需求 | 工作量 | 说明 |
|--------|------|--------|------|
| P1 | 需求一：来源列 | 中 | 需修改 6 个扫描函数 + 前端表格 |
| P1 | 需求二：状态检测 | 小 | 依赖需求一的 source_dir，改动集中在扫描函数 |
| P2 | 需求三：菜单栏摘要 | 大 | 需新建 popover 窗口 + 数据流 + Tauri 窗口管理 |

建议实施顺序：需求一 → 需求二 → 需求三（前两者有数据依赖，后者独立但工作量最大）。

---

*文档版本：1.0*
*最后更新：2026-05-29*
