use std::sync::{Condvar, Mutex};
use std::thread;
use std::time::Duration;

use crate::models::ScanScheduleState;

pub struct SchedulerState {
    pub enabled: bool,
    pub interval_hours: u32,
    pub last_scan_at: Option<String>,
}

impl Default for SchedulerState {
    fn default() -> Self {
        Self {
            enabled: false,
            interval_hours: 24,
            last_scan_at: None,
        }
    }
}

pub type SchedulerHandle = std::sync::Arc<(Mutex<SchedulerState>, Condvar)>;

pub fn create_scheduler() -> SchedulerHandle {
    std::sync::Arc::new((Mutex::new(SchedulerState::default()), Condvar::new()))
}

pub fn get_state(handle: &SchedulerHandle) -> ScanScheduleState {
    let (lock, _) = &**handle;
    let state = lock.lock().unwrap();
    ScanScheduleState {
        enabled: state.enabled,
        interval_hours: state.interval_hours,
        last_scan_at: state.last_scan_at.clone(),
    }
}

pub fn start_scheduler(
    handle: SchedulerHandle,
    app: tauri::AppHandle,
    interval_hours: u32,
) -> Result<ScanScheduleState, String> {
    {
        let (lock, _) = &*handle;
        let mut state = lock.lock().map_err(|e| e.to_string())?;
        state.enabled = true;
        state.interval_hours = interval_hours.max(1);
    }

    let handle_clone = handle.clone();
    let app_clone = app.clone();

    thread::spawn(move || loop {
        let interval;
        {
            let (lock, _) = &*handle_clone;
            let state = lock.lock().unwrap();
            if !state.enabled {
                break;
            }
            interval = state.interval_hours;
        }

        {
            let (lock, cvar) = &*handle_clone;
            let mut state = lock.lock().unwrap();
            state = cvar
                .wait_timeout(state, Duration::from_secs(3600 * interval as u64))
                .unwrap()
                .0;
            if !state.enabled {
                break;
            }
        }

        let _ = crate::commands::scan_and_persist(&app_clone, &handle_clone);
    });

    Ok(get_state(&handle))
}

pub fn stop_scheduler(handle: &SchedulerHandle) -> ScanScheduleState {
    let (lock, cvar) = &**handle;
    let mut state = lock.lock().unwrap();
    state.enabled = false;
    cvar.notify_one();
    ScanScheduleState {
        enabled: false,
        interval_hours: state.interval_hours,
        last_scan_at: state.last_scan_at.clone(),
    }
}

pub fn update_last_scan(handle: &SchedulerHandle, time: &str) {
    let (lock, _) = &**handle;
    let mut state = lock.lock().unwrap();
    state.last_scan_at = Some(time.to_string());
}
