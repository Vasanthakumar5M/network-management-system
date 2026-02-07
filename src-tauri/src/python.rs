// Python process management

use std::process::{Child, Command, Stdio};
use std::path::PathBuf;
use anyhow::Result;

/// Get the project root directory
pub fn get_project_root() -> PathBuf {
    std::env::current_exe()
        .unwrap()
        .parent()
        .unwrap()
        .parent()
        .unwrap()
        .parent()
        .unwrap()
        .to_path_buf()
}

/// Get the Python virtual environment path
pub fn get_python_path() -> PathBuf {
    let root = get_project_root();
    root.join("network_monitor_env").join("Scripts").join("python.exe")
}

/// Start a Python script as a background process
pub fn start_python_script(script_path: &str, args: &[&str]) -> Result<Child> {
    let python = get_python_path();
    let root = get_project_root();
    let full_path = root.join(script_path);

    let child = Command::new(&python)
        .arg(&full_path)
        .args(args)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()?;

    Ok(child)
}

/// Kill all Python processes
pub fn kill_python_processes(processes: &mut Vec<Child>) {
    for process in processes.iter_mut() {
        let _ = process.kill();
    }
    processes.clear();
}
