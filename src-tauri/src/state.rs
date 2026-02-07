// Application state management

use std::process::Child;
use std::sync::Mutex;
use std::time::Instant;

pub struct AppState {
    pub is_monitoring: Mutex<bool>,
    pub python_processes: Mutex<Vec<Child>>,
    pub current_profile: Mutex<String>,
    pub start_time: Mutex<Option<Instant>>,
}
