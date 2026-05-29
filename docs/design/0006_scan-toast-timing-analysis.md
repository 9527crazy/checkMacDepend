# 扫描 Toast 时序问题分析

**文档版本**: 2.0  
**日期**: 2026-05-29  
**状态**: 分析完成

---

## 问题描述

点击"立即扫描"按钮后，出现以下两种异常表现：

1. **Toast 不显示**: "正在启动扫描..." toast 有时完全不出现
2. **Toast 同时出现**: "正在启动扫描..." 和 "扫描完成" 两个 toast 同时弹出

期望行为：先看到"正在启动扫描..."，扫描完成后切换为"扫描完成"。

**关键实验**: 将 `scanPackages()` 调用注释掉后，toast 能正常显示。这排除了 Vue/前端层面的问题。

---

## 根因：Rust 同步命令阻塞主线程

### 问题本质

`scan_packages` 是一个 **同步** `#[tauri::command]`，在 Tauri 2 中会在 **主线程** 上执行。函数内部调用 `Command::new("brew").output()` 等阻塞操作，导致主线程被占用，Webview 无法处理任何事件（包括 Vue 的 DOM 更新）。

### 完整调用链

```
JS: invoke("scan_packages")
    ↓
WKWebView IPC (主线程回调)
    ↓
protocol.rs: handle_ipc_message()        ← 主线程
    ↓
webview/mod.rs: on_message()             ← 主线程
    ↓
manager/mod.rs: run_invoke_handler()     ← 主线程
    ↓
handler 闭包 → wrapper 函数              ← 主线程
    ↓
scan_packages() 同步执行                 ← 主线程被阻塞
    ├─ Command::new("brew").output()     ← 阻塞等待进程结束
    ├─ Command::new("pip3").output()     ← 阻塞
    ├─ Command::new("npm").output()      ← 阻塞
    ├─ load_storage()                    ← 同步文件 IO
    └─ save_storage()                    ← 同步文件 IO
    ↓
结果通过 resolver.respond() 返回         ← 主线程
    ↓
Vue 终于可以更新 DOM → 两个 toast 同时渲染
```

### 为什么 toast 不显示

```
时间轴 →

[T0] 主线程:
     handleScan() 开始执行
     statusMessage = "扫描中..."          ← ref 被修改，Vue 标记需要更新
     showToast("正在启动扫描...", "info")  ← toasts 数组被修改，Vue 标记需要更新
     ↓
[T1] 主线程:
     await scanPackages() → invoke() 发送 IPC
     主线程被 scan_packages() 阻塞        ← ⚠️ 关键：主线程卡死
     │
     │  （Vue 无法更新 DOM，因为主线程在等 Rust 执行完）
     │  （Webview 无法处理任何事件）
     │
     │  ... scan_packages 执行中 ...
     │  ... Command::new("brew").output() 等待 brew 进程 ...
     │  ... load_storage() 读文件 ...
     │  ... save_storage() 写文件 ...
     │
[T2] 主线程:
     scan_packages() 返回结果
     resolve 传回 JS
     ↓
[T3] 主线程:
     handleScan() 续行
     showToast("扫描完成", "success")     ← 第二个 toast 也被添加
     ↓
[T4] 主线程:
     所有同步代码执行完毕
     Vue flush DOM                        ← 一次性渲染两个 toast
     用户看到两个 toast 同时出现
```

**核心问题**: Vue 的 DOM 更新需要主线程空闲。`scan_packages` 在主线程上执行了所有阻塞操作（进程调用 + 文件 IO），Vue 在此期间完全无法更新 DOM。

---

## Tauri 2 命令执行机制

### 同步命令 vs 异步命令

```rust
// 同步命令 → 主线程执行 → 阻塞 UI
#[tauri::command]
fn scan_packages(app: tauri::AppHandle) -> Result<ScanResult, String> {
    // 这里的代码在主线程执行
    // 任何阻塞操作都会冻结 UI
}

// 异步命令 → async_runtime 执行 → 不阻塞 UI
#[tauri::command]
async fn scan_packages(app: tauri::AppHandle) -> Result<ScanResult, String> {
    // 这里的代码在 tokio async_runtime 执行
    // 不阻塞主线程
}
```

### 源码证据

**wrapper.rs** (Tauri 命令宏):

```rust
// 默认执行上下文是 Blocking
execution_context: ExecutionContext::Blocking,

// 如果函数是 async，改为 Async
if function.sig.asyncness.is_some() {
    attrs.execution_context = ExecutionContext::Async;
}
```

**Blocking 路径** — 直接在当前线程（主线程）执行:
```rust
fn body_blocking(...) -> TokenStream2 {
    Ok(quote! {
        let result = $path(#(match #args #match_body),*);
        let kind = (&result).blocking_kind();
        kind.block(result, #resolver);  // → resolver.respond() → 同步返回
        return true;
    })
}
```

**Async 路径** — 在 async_runtime 上执行:
```rust
fn body_async(...) -> TokenStream2 {
    quote! {
        #resolver.respond_async_serialized(async move {
            let result = $path(#(#args?),*);
            // → crate::async_runtime::spawn(task)  ← 不阻塞主线程
        });
        return true;
    }
}
```

**respond_async_serialized** (ipc/mod.rs):
```rust
pub fn respond_async_serialized_inner<F>(self, task: F) {
    crate::async_runtime::spawn(async move {  // ← spawn 到 tokio runtime
        let response = task.await;
        Self::return_result(self.webview, self.responder, response, ...);
    });
}
```

---

## scan_packages 中的阻塞操作

```rust
fn scan_packages(app: tauri::AppHandle) -> Result<ScanResult, String> {
    // 所有操作都在主线程执行
    let packages = scan_all_packages_with_log(&app, &scanned_at);  // 阻塞
    let mut data = load_storage()?;                                 // 阻塞
    save_storage(&data)?;                                           // 阻塞
    // ...
}
```

### scan_all_packages_with_log 中的阻塞调用

```rust
fn scan_all_packages_with_log(...) -> Vec<PackageInfo> {
    for (name, command, scan_fn) in &managers {
        if is_available(command) {                    // ← Command::new("which").output() 阻塞
            let found = scan_fn(scanned_at);          // ← Command::new("brew").output() 阻塞
            packages.extend(found);
        }
    }
    packages
}
```

每个包管理器的扫描都是一次 `Command::new().output()` 调用，等待子进程完成。在 macOS 上：
- `brew list --versions` 可能需要 100ms-2s
- `pip3 list` 可能需要 50ms-500ms
- `npm list -g --depth=0` 可能需要 100ms-1s
- `cargo install --list` 可能需要 200ms-1s

**这些时间全部卡在主线程上，UI 完全冻结。**

---

## 修复方向

### 方案 A：将 scan_packages 改为 async 命令（推荐）

```rust
#[tauri::command]
async fn scan_packages(app: tauri::AppHandle) -> Result<ScanResult, String> {
    let scanned_at = now_minutes();
    let scanned_date = today();

    // 将阻塞操作放到 spawn_blocking 中
    let packages = tokio::task::spawn_blocking(move || {
        scan_all_packages_with_log(&app_handle, &scanned_at)
    }).await.map_err(|e| e.to_string())?;

    // 文件 IO 也放到 spawn_blocking
    let mut data = tokio::task::spawn_blocking(|| {
        load_storage()
    }).await.map_err(|e| e.to_string())??;

    // ... 对比逻辑 ...

    tokio::task::spawn_blocking(move || {
        save_storage(&data)
    }).await.map_err(|e| e.to_string())??;

    Ok(ScanResult { ... })
}
```

### 方案 B：在同步命令内部使用线程

```rust
#[tauri::command]
fn scan_packages(app: tauri::AppHandle) -> Result<ScanResult, String> {
    // 不能直接用 spawn_blocking，因为是同步函数
    // 可以用 std::thread::spawn + channel，但复杂度高
    // 不推荐
}
```

### 方案 C：前端不显示"正在扫描"toast

最简单的临时方案，但不解决根本问题：
```js
// 不弹 info toast，只依赖状态栏
statusMessage.value = "扫描中...";
// showToast("正在启动扫描...", "info");  // 注释掉
```

---

## 推荐

**方案 A** 是正确的修复：
- 解决根本问题（主线程阻塞）
- 符合 Tauri 2 的 async 命令设计模式
- UI 在扫描期间保持响应
- toast 时序自然正确

需要确保 `tokio` 依赖已启用（Tauri 2 已包含 tokio）。

---

## 参考

- Tauri 2 命令系统: https://v2.tauri.app/develop/calling-rust/
- Tauri 2 async commands: `#[tauri::command]` on `async fn`
- 源码: `tauri-macros-2.6.2/src/command/wrapper.rs`
- 源码: `tauri-2.11.2/src/ipc/mod.rs` (respond_async_serialized)
- 源码: `tauri-2.11.2/src/webview/mod.rs` (on_message)
