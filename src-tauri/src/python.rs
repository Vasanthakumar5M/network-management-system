// Python process management and IPC

use std::io::{BufRead, BufReader, Write};
use std::process::{Child, Command, Stdio};
use std::path::PathBuf;
use anyhow::Result;
use serde_json::Value;

/// Get the project root directory
pub fn get_project_root() -> PathBuf {
    // In development, use the manifest directory
    if let Ok(manifest_dir) = std::env::var("CARGO_MANIFEST_DIR") {
        return PathBuf::from(manifest_dir).parent().unwrap().to_path_buf();
    }
    
    // In production, relative to exe
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

/// Get the Python executable path
pub fn get_python_path() -> PathBuf {
    let root = get_project_root();
    let venv_python = root.join("network_monitor_env").join("Scripts").join("python.exe");
    
    // If venv exists, use it
    if venv_python.exists() {
        return venv_python;
    }
    
    // Fallback to system Python
    PathBuf::from("python")
}

/// Start a Python script as a background process
pub fn start_python_script(script_path: &str, args: &[&str]) -> Result<Child> {
    let python = get_python_path();
    let root = get_project_root();
    let full_path = root.join(script_path);

    log::info!("Starting Python script: {:?} with args: {:?}", full_path, args);

    let child = Command::new(&python)
        .arg(&full_path)
        .args(args)
        .current_dir(&root)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .stdin(Stdio::piped())
        .spawn()?;

    Ok(child)
}

/// Run a Python script and get JSON output
pub fn run_python_script(script_path: &str, args: &[&str]) -> Result<Value, String> {
    let python = get_python_path();
    let root = get_project_root();
    let full_path = root.join(script_path);

    log::info!("Running Python script: {:?} with args: {:?}", full_path, args);

    let output = Command::new(&python)
        .arg(&full_path)
        .args(args)
        .current_dir(&root)
        .output()
        .map_err(|e| format!("Failed to run Python script: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Python script failed: {}", stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    
    // Find the last JSON line in output (scripts may output multiple JSON objects)
    let json_str = stdout
        .lines()
        .filter(|line| line.starts_with('{') || line.starts_with('['))
        .last()
        .ok_or_else(|| "No JSON output from Python script".to_string())?;

    serde_json::from_str(json_str)
        .map_err(|e| format!("Failed to parse JSON: {} - Output: {}", e, json_str))
}

/// Run a database query script and return results
pub fn query_database(action: &str, args: &[(&str, &str)]) -> Result<Value, String> {
    let mut script_args = vec!["--action", action];
    
    for (key, value) in args {
        script_args.push(key);
        script_args.push(value);
    }
    
    run_python_script("python/database/db_manager.py", &script_args)
}

/// Run a blocking engine command
pub fn run_blocking_command(action: &str, args: &[(&str, &str)]) -> Result<Value, String> {
    let mut script_args = vec!["--action", action];
    
    for (key, value) in args {
        script_args.push(key);
        script_args.push(value);
    }
    
    run_python_script("python/blocking/blocker.py", &script_args)
}

/// Run a stealth command (MAC/hostname change)
pub fn run_stealth_command(action: &str, interface: &str, profile: Option<&str>) -> Result<Value, String> {
    let mut args = vec!["--interface", interface];
    
    match action {
        "apply" => {
            if let Some(p) = profile {
                args.push("--profile");
                args.push(p);
            } else {
                args.push("--random");
            }
        }
        "restore" => {
            args.push("--restore");
        }
        "show" => {
            args.push("--show");
        }
        _ => return Err(format!("Unknown stealth action: {}", action)),
    }
    
    run_python_script("python/stealth/mac_changer.py", &args)
}

/// Run alert engine command
pub fn run_alert_command(action: &str, args: &[(&str, &str)]) -> Result<Value, String> {
    let mut script_args = vec!["--action", action];
    
    for (key, value) in args {
        script_args.push(key);
        script_args.push(value);
    }
    
    run_python_script("python/alerts/alert_engine.py", &script_args)
}

/// Send a command to a running Python process via stdin
pub fn send_command_to_process(process: &mut Child, command: &Value) -> Result<(), String> {
    if let Some(ref mut stdin) = process.stdin {
        let json = serde_json::to_string(command)
            .map_err(|e| format!("Failed to serialize command: {}", e))?;
        writeln!(stdin, "{}", json)
            .map_err(|e| format!("Failed to write to process: {}", e))?;
        stdin.flush()
            .map_err(|e| format!("Failed to flush: {}", e))?;
        Ok(())
    } else {
        Err("Process has no stdin".to_string())
    }
}

/// Read a line of JSON from a process stdout
pub fn read_process_output(process: &mut Child) -> Result<Value, String> {
    if let Some(ref mut stdout) = process.stdout {
        let mut reader = BufReader::new(stdout);
        let mut line = String::new();
        reader.read_line(&mut line)
            .map_err(|e| format!("Failed to read from process: {}", e))?;
        
        serde_json::from_str(&line)
            .map_err(|e| format!("Failed to parse JSON: {}", e))
    } else {
        Err("Process has no stdout".to_string())
    }
}

/// Kill all Python processes
pub fn kill_python_processes(processes: &mut Vec<Child>) {
    for process in processes.iter_mut() {
        let _ = process.kill();
    }
    processes.clear();
}

/// Check if Python is available
pub fn check_python() -> Result<String, String> {
    let python = get_python_path();
    
    let output = Command::new(&python)
        .args(["--version"])
        .output()
        .map_err(|e| format!("Failed to run Python: {}", e))?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
    } else {
        Err("Python not available".to_string())
    }
}
