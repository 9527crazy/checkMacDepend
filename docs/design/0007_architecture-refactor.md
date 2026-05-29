# 架构重构设计文档 — 代码拆分方案

**文档版本**: 1.0
**日期**: 2026-05-29
**状态**: 待批准
**前置文档**: 0004_ui-ux-review.md, 0005_ui-audit-2026-05-29.md

---

## 1. 现状分析

### 1.1 后端 (`src-tauri/src/main.rs` — 833 行)

所有逻辑堆在一个文件中，职责混杂：

| 职责 | 行数(约) | 内容 |
|------|----------|------|
| 数据模型 | ~130 | PackageInfo, Snapshot, Metadata, StorageData, ScanSchedule 等 9 个 struct |
| 存储层 | ~60 | storage_dir, records_path, load_storage, save_storage |
| 扫描器 | ~200 | scan_homebrew/pip/npm/cargo/gem/go, available_managers |
| 核心扫描逻辑 | ~120 | scan_packages (Tauri cmd) + scan_packages_internal (定时用)，**两段几乎相同的代码** |
| 定时扫描 | ~60 | start_scheduled_scan, stop_scheduled_scan, **thread::sleep 无法及时停止** |
| 报告生成 | ~80 | render_report (HTML 拼接), generate_report |
| 系统托盘 | ~60 | 菜单构建、托盘事件处理 |
| Tauri 命令注册 | ~30 | main() 函数 |
| 工具函数 | ~30 | now_minutes, now_seconds, today, escape_html, emit_log |

**关键问题：**
- `scan_packages` 和 `scan_packages_internal` 是 ~70 行 copy-paste 代码
- 定时扫描线程用 `thread::sleep`，停止延迟最长等于扫描间隔
- 存储层无文件锁，并发读写可能损坏 JSON
- 无模块划分，无法单独测试任何一层

### 1.2 前端 (`src/App.vue` — 1549 行)

| 职责 | 行数(约) | 内容 |
|------|----------|------|
| 模板 | ~300 | 顶栏、侧边栏(状态/历史/定时/日期)、内容区(表格/空状态)、日志面板、Toast |
| 脚本 | ~250 | 状态管理、扫描、报告、定时、日志、Toast、历史记录、生命周期 |
| 样式 | ~1000 | 全局 CSS，无 scoped，所有类名暴露在全局作用域 |

**关键问题：**
- 单组件干了 8 件事，修改任一功能都要在 1549 行里找代码
- CSS 无 scoped，类名随时可能冲突
- `scanHistory` 直接读写 `localStorage`，无抽象层
- 零测试覆盖

### 1.3 已有的好设计

- `src/services.js`：IPC 层干净，只做 Tauri invoke 封装
- 扫描器按包管理器分离，职责清晰
- 数据结构 `StorageData = records + snapshot + metadata` 三层设计合理
- UI 细节（skeleton、toast、aria-label）已到位

---

## 2. 重构目标

| 目标 | 度量 |
|------|------|
| 单文件不超过 300 行 | 拆分后每个文件 ≤ 300 行 |
| 消除重复代码 | scan_packages 和 scan_packages_internal 合并为一个 |
| 存储安全 | 并发读写不损坏数据 |
| 定时扫描可控 | 停止延迟 < 1 秒 |
| 组件可测试 | 每个组件/composable 可独立测试 |
| CSS 隔离 | 使用 scoped 样式 |

---

## 3. 后端重构方案

### 3.1 模块划分

```
src-tauri/src/
├── main.rs              (~60行)  入口：Builder 配置、托盘、invoke_handler
├── models.rs            (~130行) 所有数据模型：PackageInfo, Snapshot, Metadata, StorageData, ScanSchedule
├── storage.rs           (~80行)  存储层：读写、路径、文件锁
├── scanner/
│   ├── mod.rs           (~40行)  scan_all_packages_with_log, available_managers
│   ├── homebrew.rs      (~25行)  scan_homebrew
│   ├── pip.rs           (~30行)  scan_pip
│   ├── npm.rs           (~25行)  scan_npm
│   ├── cargo.rs         (~25行)  scan_cargo
│   ├── gem.rs           (~25行)  scan_gem
│   └── go.rs            (~30行)  scan_go
├── commands.rs          (~120行) Tauri command 实现：get_app_state, scan_packages, generate_report, schedule 相关
├── scheduler.rs         (~60行)  定时扫描：Condvar 实现，可立即停止
└── report.rs            (~80行)  报告生成：render_report, escape_html
```

### 3.2 核心变更

#### A. 消除重复扫描逻辑

**现状：** `scan_packages`（前端触发）和 `scan_packages_internal`（定时触发）是两段 ~70 行的相同代码。

**方案：** 提取 `scan_and_persist` 函数作为唯一实现：

```rust
// commands.rs
fn scan_and_persist(
    app: &tauri::AppHandle,
    schedule_state: &Arc<Mutex<ScanSchedule>>,
) -> Result<ScanResult, String> {
    // 唯一的扫描 + 比较 + 持久化逻辑
}

#[tauri::command]
fn scan_packages(app: tauri::AppHandle) -> Result<ScanResult, String> {
    // 直接调用 scan_and_persist
}

// scheduler.rs 中定时线程也调用同一个函数
```

#### B. 存储层加文件锁

**现状：** `load_storage`/`save_storage` 无锁，并发可能损坏 JSON。

**方案：** 使用 `fs2::FileExt`（需添加 `fs2 = "0.4"` 依赖）：

```rust
// storage.rs
fn with_file_lock<F, R>(path: &PathBuf, f: F) -> Result<R, String>
where
    F: FnOnce(&mut File) -> Result<R, String>,
{
    let file = OpenOptions::new().read(true).write(true).create(true).open(path)?;
    file.lock_exclusive()?;  // 排他锁
    let result = f(&mut file);
    file.unlock()?;
    result
}
```

#### C. 定时扫描用 Condvar 替代 thread::sleep

**现状：** `thread::sleep(Duration::from_secs(3600 * hours))` — 停止延迟最长等于扫描间隔。

**方案：** 用 `Condvar` + `timeout` 实现可中断等待：

```rust
// scheduler.rs
struct SchedulerState {
    enabled: bool,
    interval_hours: u32,
    last_scan_at: Option<String>,
}

fn start_scheduler(
    condvar: Arc<(Mutex<SchedulerState>, Condvar)>,
    app: tauri::AppHandle,
) {
    std::thread::spawn(move || {
        loop {
            let (lock, cvar) = &*condvar;
            let mut state = lock.lock().unwrap();
            // 可中断等待：最长等 interval，但被 notify 后立即醒来
            state = cvar.wait_timeout(state, Duration::from_secs(3600 * state.interval_hours as u64))
                .unwrap().0;
            if !state.enabled {
                break; // 立即退出
            }
            // 执行扫描...
        }
    });
}

fn stop_scheduler(condvar: &Arc<(Mutex<SchedulerState>, Condvar)>) {
    let (lock, cvar) = &**condvar;
    let mut state = lock.lock().unwrap();
    state.enabled = false;
    cvar.notify_one(); // 立即唤醒线程
}
```

#### D. 系统托盘提取

托盘构建和事件处理移到 `main.rs` 中一个独立的 `setup_tray` 函数，不与其他逻辑混杂。`main.rs` 本身只负责组装和启动。

---

## 4. 前端重构方案

### 4.1 组件拆分

```
src/
├── main.js                    (不变)
├── services.js                (不变，已足够干净)
├── App.vue                    (~80行)  Shell：布局骨架，组装子组件
├── composables/
│   ├── useScan.js             (~60行)  扫描逻辑：handleScan, busy, hasError, logEntries
│   ├── useSchedule.js         (~40行)  定时扫描：schedule, start/stop
│   ├── useToast.js            (~25行)  Toast 通知：toasts, showToast, dismissToast
│   └── useStorage.js          (~20行)  localStorage 封装：scanHistory 读写
├── components/
│   ├── TopBar.vue             (~40行)  顶栏：标题、扫描按钮、报告按钮
│   ├── Sidebar.vue            (~20行)  侧边栏容器
│   ├── StatusOverview.vue     (~50行)  状态概览卡片
│   ├── ScanHistory.vue        (~30行)  最近扫描列表
│   ├── ScheduleControl.vue    (~50行)  定时扫描控件
│   ├── DateList.vue           (~40行)  日期列表
│   ├── PackageTable.vue       (~60行)  包表格 + 搜索
│   ├── EmptyState.vue         (~30行)  空状态/无搜索结果
│   ├── LogPanel.vue           (~50行)  扫描日志面板
│   └── ToastContainer.vue     (~40行)  Toast 通知容器
└── styles/
    └── variables.css          (~30行)  CSS 变量定义（:root）
```

### 4.2 核心变更

#### A. App.vue 变为纯 Shell

```vue
<!-- App.vue ~80行 -->
<template>
  <main class="app-shell">
    <TopBar @scan="handleScan" @report="handleReport" :busy="busy" :canReport="!!selectedDate" />
    <section class="workspace">
      <Sidebar>
        <StatusOverview :state="state" :selectedCount="selectedPackages.length" />
        <ScanHistory :history="scanHistory" />
        <ScheduleControl v-model:schedule="schedule" v-model:interval="scheduleInterval" />
        <DateList :dates="dates" v-model:selected="selectedDate" />
      </Sidebar>
      <section class="content">
        <PackageTable :packages="filteredPackages" :loading="!stateLoaded" />
        <LogPanel v-model:expanded="logExpanded" :entries="logEntries" />
      </section>
    </section>
    <StatusBar :message="statusMessage" :error="hasError" :total="state.total_count" />
    <ToastContainer :toasts="toasts" @dismiss="dismissToast" />
  </main>
</template>
```

#### B. Composables 提取业务逻辑

```javascript
// composables/useScan.js
import { ref } from "vue";
import { listen } from "@tauri-apps/api/event";
import { scanPackages } from "../services";

export function useScan({ onStateRefresh }) {
  const busy = ref(false);
  const hasError = ref(false);
  const logEntries = ref([]);
  const scanCount = ref(0);
  const statusMessage = ref("就绪");

  async function handleScan() {
    busy.value = true;
    hasError.value = false;
    scanCount.value = 0;
    statusMessage.value = "扫描中...";
    try {
      const result = await scanPackages();
      await onStateRefresh(result.scanned_at.slice(0, 10));
      statusMessage.value = result.is_initial_scan
        ? `首次扫描完成，${result.scanned_count} 个包`
        : `扫描完成，新增 ${result.new_count} 个包`;
    } catch (error) {
      hasError.value = true;
      statusMessage.value = `扫描失败: ${error}`;
    } finally {
      busy.value = false;
    }
  }

  // setupLogListener 供 onMounted 调用
  function setupLogListener() { /* ... */ }

  return { busy, hasError, logEntries, scanCount, statusMessage, handleScan, setupLogListener };
}
```

#### C. CSS scoped 化

- 所有组件使用 `<style scoped>`
- 全局变量保留在 `styles/variables.css`，在 `main.js` 中 import
- 每个组件只包含自己的样式，不污染全局

#### D. localStorage 抽象

```javascript
// composables/useStorage.js
const STORAGE_KEY = "scan-history";
const MAX_ITEMS = 5;

export function useScanHistory() {
  const history = ref(load());

  function load() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); }
    catch { return []; }
  }

  function save(count) {
    const timeStr = formatNow();
    history.value.unshift({ time: timeStr, count });
    if (history.value.length > MAX_ITEMS) history.value.length = MAX_ITEMS;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history.value));
  }

  return { history, save };
}
```

---

## 5. 实施顺序

按依赖关系和风险排序，每步完成后应用可编译运行：

| 步骤 | 内容 | 风险 | 验证方式 |
|------|------|------|----------|
| 1 | 后端：提取 `models.rs`，main.rs 改 `mod` 引用 | 低 | `cargo build` 通过 |
| 2 | 后端：提取 `storage.rs` + 文件锁 | 中 | 并发扫描测试 |
| 3 | 后端：提取 `scanner/` 模块 | 低 | `cargo build` + 各扫描器测试 |
| 4 | 后端：合并重复扫描逻辑 + 提取 `commands.rs` | 中 | 前端触发扫描正常 |
| 5 | 后端：提取 `scheduler.rs` (Condvar) | 中 | 定时扫描启停测试 |
| 6 | 后端：提取 `report.rs` | 低 | 生成报告功能正常 |
| 7 | 后端：`main.rs` 精简为入口 | 低 | 完整功能回归测试 |
| 8 | 前端：提取 `composables/` | 中 | 扫描/报告/定时功能正常 |
| 9 | 前端：拆分组件 | 中 | UI 交互全部正常 |
| 10 | 前端：CSS scoped 化 + 变量提取 | 低 | 视觉无变化 |

---

## 6. 新增依赖

| 依赖 | 用途 | 大小 |
|------|------|------|
| `fs2 = "0.4"` | 文件锁，防止并发存储损坏 | ~15KB |

前端无需新增依赖。Vue 3 Composition API 已内置 composable 支持。

---

## 7. 拆分后文件行数预估

| 文件 | 预估行数 |
|------|----------|
| `main.rs` | ~60 |
| `models.rs` | ~130 |
| `storage.rs` | ~80 |
| `scanner/mod.rs` | ~40 |
| `scanner/homebrew.rs` | ~25 |
| `scanner/pip.rs` | ~30 |
| `scanner/npm.rs` | ~25 |
| `scanner/cargo.rs` | ~25 |
| `scanner/gem.rs` | ~25 |
| `scanner/go.rs` | ~30 |
| `commands.rs` | ~120 |
| `scheduler.rs` | ~60 |
| `report.rs` | ~80 |
| **Rust 合计** | **~730** |
| | |
| `App.vue` | ~80 |
| `composables/useScan.js` | ~60 |
| `composables/useSchedule.js` | ~40 |
| `composables/useToast.js` | ~25 |
| `composables/useStorage.js` | ~20 |
| 10 个组件 | ~410 |
| `styles/variables.css` | ~30 |
| **Vue 合计** | **~665** |

**总行数：1395 → 1395**（代码量不变，只是从 2 个文件拆到 ~25 个文件）

---

## 8. 风险与回退

- **每步可独立验证**：拆模块时只改 import，不改逻辑，cargo build 即可验证
- **前端 composables 先提取**：组件拆分在 composable 之后，保证逻辑层先稳定
- **CSS scoped 化最后做**：纯样式变更，不影响逻辑，可快速验证
- **回退方案**：git 分支操作，每步完成后 commit，出问题可 revert 单步

---

## 9. 验收标准

- [ ] `cargo build` 通过，无 warning
- [ ] 所有 Tauri command 正常工作（扫描、报告、定时）
- [ ] 前端所有交互正常（扫描、日期切换、搜索、日志、Toast）
- [ ] 定时扫描：启动后停止，延迟 < 1 秒
- [ ] 并发扫描：同时触发两次扫描，不损坏 records.json
- [ ] 无全局 CSS 类名冲突
- [ ] 单文件最大行数 ≤ 300
