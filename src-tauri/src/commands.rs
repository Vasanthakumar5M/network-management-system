// Tauri command handlers

use crate::python::{kill_python_processes, start_python_script};
use crate::state::AppState;
use serde::{Deserialize, Serialize};
use tauri::State;

// ============================================
// Data Types
// ============================================

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Device {
    pub id: String,
    pub mac: String,
    pub ip: String,
    pub hostname: String,
    pub vendor: String,
    pub device_type: String,
    pub first_seen: String,
    pub last_seen: String,
    pub is_online: bool,
    pub is_monitored: bool,
    pub total_bytes: u64,
    pub blocked_requests: u32,
    pub alerts: u32,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct TrafficEntry {
    pub id: String,
    pub timestamp: String,
    pub device_id: String,
    pub device_ip: String,
    pub method: String,
    pub url: String,
    pub host: String,
    pub path: String,
    pub status_code: u16,
    pub content_type: String,
    pub request_size: u64,
    pub response_size: u64,
    pub duration: u32,
    pub is_blocked: bool,
    pub has_alert: bool,
    pub category: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Alert {
    pub id: String,
    pub timestamp: String,
    pub device_id: String,
    pub severity: String,
    pub category: String,
    pub title: String,
    pub description: String,
    pub url: Option<String>,
    pub matched_keywords: Option<Vec<String>>,
    pub is_read: bool,
    pub is_resolved: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct MonitoringStatus {
    pub is_running: bool,
    pub arp_spoofing: bool,
    pub https_proxy: bool,
    pub dns_capture: bool,
    pub stealth_mode: bool,
    pub current_profile: String,
    pub uptime: u64,
    pub errors: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DashboardStats {
    pub total_devices: u32,
    pub online_devices: u32,
    pub total_requests: u64,
    pub blocked_requests: u64,
    pub total_alerts: u32,
    pub unresolved_alerts: u32,
    pub total_bandwidth: u64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Settings {
    pub theme: String,
    pub stealth_enabled: bool,
    pub device_profile: String,
    pub blocking_enabled: bool,
    pub notifications_enabled: bool,
}

// ============================================
// Monitoring Commands
// ============================================

#[tauri::command]
pub async fn start_monitoring(state: State<'_, AppState>) -> Result<(), String> {
    let mut is_monitoring = state.is_monitoring.lock().unwrap();
    
    if *is_monitoring {
        return Err("Monitoring is already running".to_string());
    }

    let mut processes = state.python_processes.lock().unwrap();

    // Start ARP gateway
    match start_python_script("python/arp/arp_gateway.py", &[]) {
        Ok(child) => processes.push(child),
        Err(e) => return Err(format!("Failed to start ARP gateway: {}", e)),
    }

    // Start HTTPS proxy
    match start_python_script("python/https/transparent_proxy.py", &[]) {
        Ok(child) => processes.push(child),
        Err(e) => {
            kill_python_processes(&mut processes);
            return Err(format!("Failed to start HTTPS proxy: {}", e));
        }
    }

    // Start DNS capture
    match start_python_script("python/dns/dns_capture.py", &[]) {
        Ok(child) => processes.push(child),
        Err(e) => {
            kill_python_processes(&mut processes);
            return Err(format!("Failed to start DNS capture: {}", e));
        }
    }

    *is_monitoring = true;
    log::info!("Monitoring started with {} processes", processes.len());

    Ok(())
}

#[tauri::command]
pub async fn stop_monitoring(state: State<'_, AppState>) -> Result<(), String> {
    let mut is_monitoring = state.is_monitoring.lock().unwrap();
    let mut processes = state.python_processes.lock().unwrap();

    kill_python_processes(&mut processes);
    *is_monitoring = false;

    log::info!("Monitoring stopped");
    Ok(())
}

#[tauri::command]
pub async fn get_status(state: State<'_, AppState>) -> Result<MonitoringStatus, String> {
    let is_monitoring = state.is_monitoring.lock().unwrap();
    let profile = state.current_profile.lock().unwrap();

    Ok(MonitoringStatus {
        is_running: *is_monitoring,
        arp_spoofing: *is_monitoring,
        https_proxy: *is_monitoring,
        dns_capture: *is_monitoring,
        stealth_mode: true,
        current_profile: profile.clone(),
        uptime: 0,
        errors: vec![],
    })
}

// ============================================
// Device Commands
// ============================================

#[tauri::command]
pub async fn get_devices() -> Result<Vec<Device>, String> {
    // TODO: Query database for devices
    Ok(vec![])
}

#[tauri::command]
pub async fn set_device_monitoring(device_id: String, enabled: bool) -> Result<(), String> {
    log::info!("Set device {} monitoring to {}", device_id, enabled);
    // TODO: Update database
    Ok(())
}

// ============================================
// Traffic Commands
// ============================================

#[tauri::command]
pub async fn get_traffic(
    limit: Option<u32>,
    offset: Option<u32>,
    device_id: Option<String>,
) -> Result<Vec<TrafficEntry>, String> {
    // TODO: Query database for traffic
    Ok(vec![])
}

#[tauri::command]
pub async fn search_traffic(query: String) -> Result<Vec<TrafficEntry>, String> {
    log::info!("Searching traffic for: {}", query);
    // TODO: Full-text search
    Ok(vec![])
}

// ============================================
// Alert Commands
// ============================================

#[tauri::command]
pub async fn get_alerts(unread_only: Option<bool>) -> Result<Vec<Alert>, String> {
    // TODO: Query database for alerts
    Ok(vec![])
}

#[tauri::command]
pub async fn resolve_alert(alert_id: String) -> Result<(), String> {
    log::info!("Resolving alert: {}", alert_id);
    // TODO: Update database
    Ok(())
}

#[tauri::command]
pub async fn delete_alert(alert_id: String) -> Result<(), String> {
    log::info!("Deleting alert: {}", alert_id);
    // TODO: Delete from database
    Ok(())
}

// ============================================
// Stats Commands
// ============================================

#[tauri::command]
pub async fn get_stats() -> Result<DashboardStats, String> {
    // TODO: Aggregate stats from database
    Ok(DashboardStats {
        total_devices: 0,
        online_devices: 0,
        total_requests: 0,
        blocked_requests: 0,
        total_alerts: 0,
        unresolved_alerts: 0,
        total_bandwidth: 0,
    })
}

// ============================================
// Blocking Commands
// ============================================

#[tauri::command]
pub async fn add_block_rule(rule_type: String, value: String) -> Result<(), String> {
    log::info!("Adding block rule: {} - {}", rule_type, value);
    // TODO: Add to database
    Ok(())
}

#[tauri::command]
pub async fn remove_block_rule(rule_id: String) -> Result<(), String> {
    log::info!("Removing block rule: {}", rule_id);
    // TODO: Remove from database
    Ok(())
}

#[tauri::command]
pub async fn toggle_category(category_id: String, enabled: bool) -> Result<(), String> {
    log::info!("Toggle category {} to {}", category_id, enabled);
    // TODO: Update database
    Ok(())
}

// ============================================
// Settings Commands
// ============================================

#[tauri::command]
pub async fn get_settings() -> Result<Settings, String> {
    Ok(Settings {
        theme: "dark".to_string(),
        stealth_enabled: true,
        device_profile: "hp_printer".to_string(),
        blocking_enabled: true,
        notifications_enabled: true,
    })
}

#[tauri::command]
pub async fn update_settings(settings: Settings) -> Result<(), String> {
    log::info!("Updating settings: {:?}", settings);
    // TODO: Save to config file
    Ok(())
}

#[tauri::command]
pub async fn change_stealth_profile(
    profile_id: String,
    state: State<'_, AppState>,
) -> Result<(), String> {
    let mut profile = state.current_profile.lock().unwrap();
    *profile = profile_id.clone();
    log::info!("Changed stealth profile to: {}", profile_id);
    // TODO: Actually change MAC and hostname
    Ok(())
}

// ============================================
// Certificate Commands
// ============================================

#[tauri::command]
pub async fn generate_certificate(profile: String) -> Result<String, String> {
    log::info!("Generating certificate with profile: {}", profile);
    
    match start_python_script(
        "python/https/cert_generator.py",
        &["--profile", &profile],
    ) {
        Ok(mut child) => {
            let _ = child.wait();
            Ok("Certificate generated successfully".to_string())
        }
        Err(e) => Err(format!("Failed to generate certificate: {}", e)),
    }
}

#[tauri::command]
pub async fn start_cert_server() -> Result<String, String> {
    match start_python_script("cert-installer/server.py", &[]) {
        Ok(_) => Ok("Certificate server started on port 8888".to_string()),
        Err(e) => Err(format!("Failed to start cert server: {}", e)),
    }
}

// ============================================
// Export Commands
// ============================================

#[tauri::command]
pub async fn export_data(format: String, path: String) -> Result<(), String> {
    log::info!("Exporting data as {} to {}", format, path);
    // TODO: Export database to file
    Ok(())
}
