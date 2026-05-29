mod commands;
mod models;
mod report;
mod scanner;
mod scheduler;
mod storage;

use chrono::Local;
use tauri::Emitter;
use tauri::Manager;
use tauri::menu::{MenuBuilder, MenuItemBuilder, PredefinedMenuItem};
use tauri::tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent};

use models::ScanLogPayload;
use scheduler::SchedulerHandle;

fn now_minutes() -> String {
    Local::now().format("%Y-%m-%d %H:%M").to_string()
}

fn now_seconds() -> String {
    Local::now().format("%H:%M:%S").to_string()
}

fn today() -> String {
    Local::now().format("%Y-%m-%d").to_string()
}

fn emit_log(app: &tauri::AppHandle, level: &str, message: &str) {
    let _ = app.emit(
        "scan-log",
        ScanLogPayload {
            timestamp: now_seconds(),
            level: level.to_string(),
            message: message.to_string(),
        },
    );
}

fn setup_tray(app: &tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    let show_item = MenuItemBuilder::new("打开主窗口")
        .id("show")
        .build(app)?;
    let scan_item = MenuItemBuilder::new("立即扫描")
        .id("scan")
        .build(app)?;
    let quit_item = MenuItemBuilder::new("退出")
        .id("quit")
        .build(app)?;

    let menu = MenuBuilder::new(app)
        .item(&show_item)
        .item(&scan_item)
        .item(&PredefinedMenuItem::separator(app)?)
        .item(&quit_item)
        .build()?;

    let _tray = TrayIconBuilder::new()
        .icon(app.default_window_icon().unwrap().clone())
        .menu(&menu)
        .tooltip("Package Monitor - 包安装监控")
        .on_menu_event(move |app, event| match event.id().as_ref() {
            "show" => {
                if let Some(window) = app.get_webview_window("main") {
                    let _ = window.show();
                    let _ = window.set_focus();
                }
            }
            "scan" => {
                if let Some(window) = app.get_webview_window("main") {
                    let _ = window.show();
                    let _ = window.set_focus();
                    let _ = window.emit("request-scan", ());
                }
            }
            "quit" => {
                app.exit(0);
            }
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
                let app = tray.app_handle();
                if let Some(window) = app.get_webview_window("main") {
                    let _ = window.show();
                    let _ = window.set_focus();
                }
            }
        })
        .build(app)?;

    Ok(())
}

fn main() {
    let schedule_handle: SchedulerHandle = scheduler::create_scheduler();

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(schedule_handle)
        .invoke_handler(tauri::generate_handler![
            commands::get_app_state,
            commands::scan_packages,
            commands::generate_report,
            commands::get_scan_schedule,
            commands::start_scheduled_scan,
            commands::stop_scheduled_scan,
            commands::toggle_devtools
        ])
        .setup(|app| {
            setup_tray(app)?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Package Monitor");
}
