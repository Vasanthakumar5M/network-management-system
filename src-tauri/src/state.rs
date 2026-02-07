// Application state management

use std::process::Child;
use std::sync::Mutex;

pub struct AppState {
    pub is_monitoring: Mutex<bool>,
    pub python_processes: Mutex<Vec<Child>>,
    pub current_profile: Mutex<String>,
}
