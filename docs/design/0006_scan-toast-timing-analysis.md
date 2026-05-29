# 扫描 Toast 时序问题分析

**文档版本**: 1.0  
**日期**: 2026-05-29  
**状态**: 分析中

---

## 问题描述

点击"立即扫描"按钮后，出现以下两种异常表现：

1. **Toast 不显示**: "正在启动扫描..." toast 有时完全不出现
2. **Toast 同时出现**: "正在启动扫描..." 和 "扫描完成" 两个 toast 同时弹出

期望行为：先看到"正在启动扫描..."，扫描完成后切换为"扫描完成"。

---

## 完整调用流程

### 1. 前端入口

```
用户点击"立即扫描"
    ↓
handleScan()                          ← src/App.vue:417
    │
    ├─ [1] busy = true
    ├─ [2] hasError = false
    ├─ [3] logExpanded = true
    ├─ [4] scanCount = 0
    ├─ [5] statusMessage = "扫描中..."     ← 响应式 ref，触发 Vue 调度
    ├─ [6] showToast("正在启动扫描...", "info")
    │       └─ toasts.value.push({id, message, type})  ← 响应式 ref，触发 Vue 调度
    │       └─ setTimeout(3000ms) 自动清除
    │
    ├─ [7] await scanPackages()
    │       └─ invoke("scan_packages")   ← Tauri IPC，返回 Promise
    │           └─ → Rust 后端执行
    │
    ├─ [8] await refreshState(...)
    │       └─ invoke("get_app_state")   ← Tauri IPC
    │
    ├─ [9] statusMessage = msg
    ├─ [10] showToast(msg, "success")
    │       └─ toasts.value.push({id, message, type})
    │       └─ setTimeout(3000ms) 自动清除
    ├─ [11] saveScanHistory(...)
    ├─ [12] stateLoaded = true
    │
    └─ finally: busy = false
```

### 2. Rust 后端执行

```
scan_packages(app)                    ← src-tauri/src/main.rs:442
    │
    ├─ scanned_at = now_minutes()
    ├─ packages = scan_all_packages_with_log(&app, &scanned_at)
    │       │
    │       ├─ emit_log("开始扫描系统包...")
    │       ├─ for each manager (homebrew/pip/npm/cargo/gem/go):
    │       │     ├─ is_available(command)    ← 执行 which 命令
    │       │     ├─ scan_fn(scanned_at)      ← 执行 brew/pip/npm 等命令
    │       │     │     └─ Command::new().output()  ← 阻塞调用，等待进程结束
    │       │     └─ emit_log("找到 X 个包")
    │       └─ return packages
    │
    ├─ load_storage()                  ← 读取 ~/.pkg-monitor/records.json
    ├─ 对比新旧快照，找出新增包
    ├─ save_storage()                  ← 写入 ~/.pkg-monitor/records.json
    ├─ emit_log("扫描完成！共 X 个包")
    └─ return ScanResult
```

### 3. Tauri 命令执行机制

```rust
#[tauri::command]
fn scan_packages(app: tauri::AppHandle) -> Result<ScanResult, String> {
    // 同步函数，返回 Result
    // Tauri 2 默认行为：同步命令在专用线程池中执行，不阻塞主线程
}
```

- `invoke("scan_packages")` 在 JS 侧返回 Promise
- Rust 函数在 Tauri 的 **命令线程池** 中执行（非主线程）
- JS 事件循环不受 Rust 执行影响
- Promise 在 Rust 函数返回时 resolve

---

## 问题根因分析

### 核心假设：Vue 的 DOM 更新是异步批量的

Vue 3 的响应式系统在修改 ref 后**不会立即更新 DOM**，而是将更新任务加入队列，在当前同步代码执行完毕后的微任务阶段统一刷新。

关键机制：
- 修改 `ref` → 触发 `trigger()` → 调用 `queueJob()` → 调度 `queueFlush()`
- `queueFlush()` 通过 `Promise.resolve().then(flushJobs)` 安排一次微任务刷新
- 多个 ref 在同一同步代码块中修改 → **只触发一次 DOM 刷新**

### 时序推演

#### 场景 A：扫描耗时 > 16ms（正常情况）

```
时间轴 →

[T0] 同步执行阶段:
     statusMessage = "扫描中..."        ← ref 触发 Vue 调度
     showToast("正在启动扫描...", "info") ← ref 触发 Vue 调度
     await scanPackages()               ← yield，让出执行权
     ↓
[T1] 微任务队列:
     Vue flushJobs() → DOM 更新 → "正在启动扫描..." toast 渲染到屏幕 ✓
     ↓
[T2] 等待 Rust 后端完成扫描...
     ↓
[T3] scanPackages Promise resolve
     await 续行
     ↓
[T4] 同步执行阶段:
     showToast("扫描完成", "success")    ← ref 触发 Vue 调度
     ↓
[T5] 微任务队列:
     Vue flushJobs() → DOM 更新 → "扫描完成" toast 渲染到屏幕 ✓
```

**结果**: 两个 toast 先后出现，符合预期。✅

#### 场景 B：扫描极快（< 1ms，Promise 在 await 时已 resolved）

```
时间轴 →

[T0] 同步执行阶段:
     statusMessage = "扫描中..."        ← ref 触发 Vue 调度
     showToast("正在启动扫描...", "info") ← ref 触发 Vue 调度
     await scanPackages()               ← Promise 已 resolved
                                          将续行作为微任务入队
     ↓
[T1] 微任务队列 (FIFO):
     [a] Vue flushJobs() → DOM 更新 → "正在启动扫描..." 渲染 ✓
     [b] handleScan 续行
         → showToast("扫描完成", "success") ← ref 触发 Vue 调度
         → await refreshState(...)
         → ...
     ↓
[T2] 微任务队列:
     [c] Vue flushJobs() → DOM 更新 → "扫描完成" 渲染 ✓
```

**结果**: 两个 toast 先后出现，但间隔极短（< 16ms），用户可能感知为"同时出现"。⚠️

#### 场景 C：扫描极快 + Vue flush 被续行抢先（理论可能）

```
时间轴 →

[T0] 同步执行阶段:
     showToast("正在启动扫描...", "info")
     await scanPackages()               ← Promise 已 resolved
     ↓
[T1] 微任务队列:
     [a] Vue flushJobs()               ← Vue 的 flush
     [b] handleScan 续行               ← Promise 的 .then
     如果 [b] 先于 [a] 执行:
         → showToast("扫描完成", "success")
         → 两个 toast 都在 toasts 数组中
         → Vue flush 只触发一次
         → 两个 toast 同时渲染到屏幕
```

**关键问题**: 微任务队列是 FIFO，Vue 的 `queueFlush` 和 Promise 的 `.then` 哪个先入队？

- Vue 的 `queueJob` 在 `showToast` → `toasts.value.push()` 时同步调用
- `queueFlush` 通过 `Promise.resolve().then(flushJobs)` 安排微任务
- `await scanPackages()` 的续行也在 Promise resolve 时安排微任务

如果 `scanPackages()` 的 Promise 在 `showToast` **之前**就已经 resolved（极端情况），那么续行的微任务先入队，Vue flush 后入队。**但这种情况不可能**，因为 `showToast` 在 `await` 之前同步执行，Vue 的 queueFlush 一定先于 await 续行入队。

**所以场景 C 在正常情况下不会发生。**

### 真正的根因

#### 原因 1：扫描极快导致两个 toast 几乎同时渲染

当 Rust 后端扫描极快（如所有包管理器都已缓存），`invoke` 返回的 Promise 可能在 1-5ms 内 resolve。虽然 Vue 会分别渲染两个 toast，但间隔太短（< 16ms），用户看到的效果就是**两个 toast 同时弹出**。

#### 原因 2：TransitionGroup 动画导致视觉重叠

Toast 使用 `TransitionGroup` 渲染，有 250ms 的 enter 动画：

```css
.toast-enter-active { transition: all 0.25s ease; }
.toast-enter-from { opacity: 0; transform: translateX(20px); }
```

当两个 toast 在极短时间内先后添加时：
1. 第一个 toast 开始 enter 动画（从 opacity:0 → 1）
2. 第二个 toast 紧接着也开始 enter 动画
3. 用户看到两个 toast **同时从右侧滑入**

#### 原因 3：3秒自动清除可能干扰

`showToast` 有 `setTimeout(3000ms)` 自动清除。如果扫描耗时 > 3 秒（极端情况），info toast 会在 success toast 出现前被清除。但这不太常见。

---

## 为什么之前尝试的修复不生效

### 尝试 1：800ms 延迟

```js
const scanStart = Date.now();
// ... scan ...
const elapsed = Date.now() - scanStart;
if (elapsed < 800) {
  await new Promise(r => setTimeout(r, 800 - elapsed));
}
showToast(msg, "success");
```

**问题**: `setTimeout` 创建的是宏任务，不是微任务。在等待 setTimeout 期间，Vue 已经完成了 info toast 的渲染。但 setTimeout 的回调执行时，info toast 可能已经被 Vue 的 TransitionGroup 移除了（如果 Vue 的批量更新把两个 toast 的添加和之前的某个移除操作合并在了一起）。

实际上这个方案逻辑上应该有效，但用户反馈 info toast 不显示了。可能原因：
- `await new Promise(r => setTimeout(r, 800 - elapsed))` 在 `elapsed >= 800` 时不等待，直接执行
- 如果 `scanPackages()` 耗时 > 800ms，elapsed >= 800，不会等待，info toast 短暂显示后被 success toast 替代
- 如果 `scanPackages()` 耗时 < 800ms，等待到 800ms 后弹 success toast

但用户说 info toast 不显示了，这说明可能有更深层的问题。

### 尝试 2：nextTick + dismissToast

```js
const scanToastId = showToast("正在启动扫描...", "info");
await nextTick();
// ...
dismissToast(scanToastId);
showToast(msg, "success");
```

**问题**: `nextTick` 确保了 Vue 完成一次 DOM 更新，info toast 应该已经渲染。然后 `dismissToast` 移除 info toast，再添加 success toast。但用户说 info toast 完全不显示了。

**可能原因**: `dismissToast(scanToastId)` 在同一个同步代码块中执行，Vue 可能把 `showToast("info")` 和 `dismissToast(infoId)` 合并为一次更新——先添加再移除，结果是 info toast 从未渲染到屏幕。

**这是 Vue 批量更新的典型陷阱**：在同一微任务/同步代码块中添加和移除同一个元素，Vue 会优化为"从未添加过"。

---

## 修复方向

### 方案 A：显示状态 toast，扫描完成后**更新内容**而非新建

不使用两个独立的 toast，而是在扫描开始时创建一个持久的 status toast，扫描完成后更新其 message 和 type：

```js
async function handleScan() {
  const statusToastId = showToast("正在扫描...", "info");
  try {
    const result = await scanPackages();
    // 更新现有 toast 的内容
    updateToast(statusToastId, msg, "success");
  } catch (error) {
    updateToast(statusToastId, `扫描失败: ${error}`, "error");
  }
}
```

需要新增 `updateToast(id, message, type)` 函数。

### 方案 B：扫描期间显示状态 toast，完成后延迟替换

```js
async function handleScan() {
  showToast("正在扫描...", "info");
  const result = await scanPackages();
  // 等待至少 800ms，确保用户看到"正在扫描"
  const minDisplayTime = 800;
  const scanDuration = Date.now() - scanStart;
  if (scanDuration < minDisplayTime) {
    await new Promise(r => setTimeout(r, minDisplayTime - scanDuration));
  }
  // 先清除旧 toast，再添加新 toast（分两次微任务）
  toasts.value = toasts.value.filter(t => t.type !== "info");
  await nextTick();
  showToast("扫描完成", "success");
}
```

### 方案 C：使用状态栏 + 单一 toast

将"正在扫描"放在底部状态栏（已有 `statusMessage`），只在完成/失败时弹 toast：

```js
async function handleScan() {
  statusMessage.value = "扫描中...";  // 状态栏已显示
  // 不弹 info toast
  try {
    const result = await scanPackages();
    showToast("扫描完成", "success");  // 只在完成时弹
  } catch (error) {
    showToast("扫描失败", "error");
  }
}
```

这是最简单的方案，但减少了用户感知。

---

## 推荐方案

**方案 A（更新 toast 内容）**最符合交互设计原则：
- 系统状态可见性：始终有一个 toast 显示当前状态
- 反馈及时性：扫描开始立即有反馈，完成后平滑过渡
- 无闪烁：不会出现两个 toast 同时弹出的问题
- 无多余延迟：不需要人为等待

需要实现：
1. `showToast` 返回 toast id
2. 新增 `updateToast(id, message, type)` 函数
3. `handleScan` 中使用单一 toast 管理生命周期

---

## 参考

- Vue 3 响应式系统: https://vuejs.org/guide/extras/reactivity-in-depth.html
- Vue TransitionGroup: https://vuejs.org/guide/built-ins/transition-group.html
- Tauri 2 命令系统: https://v2.tauri.app/develop/calling-rust/
