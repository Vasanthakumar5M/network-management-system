// Tauri command handlers

use crate::python::{
    kill_python_processes, start_python_script, run_python_script,
    query_database, run_blocking_command, run_stealth_command, run_alert_command
};
use crate::state::AppState;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use tauri::State;
use std::fs;
use std::path::PathBuf;

// ============================================
// Data Types
// ============================================

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Device {
    pub id: String,
    pub mac: String,
    pub ip: String,
    pub hostname: Option<String>,
    pub vendor: Option<String>,
    pub device_type: String,
    pub first_seen: String,
    pub last_seen: String,
    pub is_online: bool,
    pub is_monitored: bool,
    pub has_certificate: bool,
    pub total_bytes: u64,
    pub blocked_requests: u32,
    pub alerts: u32,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct TrafficEntry {
    pub id: String,
    pub timestamp: String,
    pub device_id: Option<String>,
    pub device_ip: String,
    pub method: String,
    pub url: String,
    pub host: String,
    pub path: Option<String>,
    pub status_code: Option<u16>,
    pub content_type: Option<String>,
    pub request_size: u64,
    pub response_size: u64,
    pub duration: u32,
    pub is_blocked: bool,
    pub has_alert: bool,
    pub category: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Alert {
    pub id: String,
    pub timestamp: String,
    pub device_id: Option<String>,
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
    pub top_domains: Vec<TopDomain>,
    pub traffic_by_hour: Vec<HourlyTraffic>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TopDomain {
    pub domain: String,
    pub count: u64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HourlyTraffic {
    pub hour: u32,
    pub requests: u64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Settings {
    pub theme: String,
    pub stealth_enabled: bool,
    pub device_profile: String,
    pub blocking_enabled: bool,
    pub notifications_enabled: bool,
    pub network_interface: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct BlockRule {
    pub id: String,
    pub rule_type: String,
    pub value: String,
    pub enabled: bool,
    pub reason: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct BlockCategory {
    pub id: String,
    pub name: String,
    pub enabled: bool,
    pub severity: String,
}

// ============================================
// Helper Functions
// ============================================

fn get_config_path() -> PathBuf {
    crate::python::get_project_root().join("config")
}

fn load_settings() -> Result<Settings, String> {
    let path = get_config_path().join("settings.json");
    
    if !path.exists() {
        return Ok(Settings {
            theme: "dark".to_string(),
            stealth_enabled: true,
            device_profile: "hp_printer".to_string(),
            blocking_enabled: true,
            notifications_enabled: true,
            network_interface: None,
        });
    }
    
    let content = fs::read_to_string(&path)
        .map_err(|e| format!("Failed to read settings: {}", e))?;
    
    serde_json::from_str(&content)
        .map_err(|e| format!("Failed to parse settings: {}", e))
}

fn save_settings(settings: &Settings) -> Result<(), String> {
    let path = get_config_path().join("settings.json");
    
    fs::create_dir_all(get_config_path())
        .map_err(|e| format!("Failed to create config dir: {}", e))?;
    
    let content = serde_json::to_string_pretty(settings)
        .map_err(|e| format!("Failed to serialize settings: {}", e))?;
    
    fs::write(&path, content)
        .map_err(|e| format!("Failed to write settings: {}", e))
}

fn parse_devices(json: Value) -> Vec<Device> {
    if let Some(devices) = json.get("devices").and_then(|d| d.as_array()) {
        devices.iter().filter_map(|d| {
            Some(Device {
                id: d.get("id")?.as_str()?.to_string(),
                mac: d.get("mac_address").or(d.get("mac"))?.as_str()?.to_string(),
                ip: d.get("ip_address").or(d.get("ip"))?.as_str()?.to_string(),
                hostname: d.get("hostname").and_then(|h| h.as_str()).map(|s| s.to_string()),
                vendor: d.get("manufacturer").or(d.get("vendor")).and_then(|v| v.as_str()).map(|s| s.to_string()),
                device_type: d.get("device_type").and_then(|t| t.as_str()).unwrap_or("unknown").to_string(),
                first_seen: d.get("first_seen").and_then(|t| t.as_str()).unwrap_or("").to_string(),
                last_seen: d.get("last_seen").and_then(|t| t.as_str()).unwrap_or("").to_string(),
                is_online: d.get("is_online").and_then(|b| b.as_bool()).unwrap_or(false),
                is_monitored: d.get("is_monitored").and_then(|b| b.as_bool()).unwrap_or(true),
                has_certificate: d.get("has_certificate").and_then(|b| b.as_bool()).unwrap_or(false),
                total_bytes: d.get("total_bytes").and_then(|n| n.as_u64()).unwrap_or(0),
                blocked_requests: d.get("blocked_requests").and_then(|n| n.as_u64()).unwrap_or(0) as u32,
                alerts: d.get("alerts").and_then(|n| n.as_u64()).unwrap_or(0) as u32,
            })
        }).collect()
    } else {
        vec![]
    }
}

fn parse_traffic(json: Value) -> Vec<TrafficEntry> {
    if let Some(traffic) = json.get("traffic").and_then(|t| t.as_array()) {
        traffic.iter().filter_map(|t| {
            Some(TrafficEntry {
                id: t.get("id")?.as_str()?.to_string(),
                timestamp: t.get("timestamp")?.as_str()?.to_string(),
                device_id: t.get("device_id").and_then(|d| d.as_str()).map(|s| s.to_string()),
                device_ip: t.get("device_ip").and_then(|d| d.as_str()).unwrap_or("").to_string(),
                method: t.get("method").and_then(|m| m.as_str()).unwrap_or("GET").to_string(),
                url: t.get("url").and_then(|u| u.as_str()).unwrap_or("").to_string(),
                host: t.get("host").and_then(|h| h.as_str()).unwrap_or("").to_string(),
                path: t.get("path").and_then(|p| p.as_str()).map(|s| s.to_string()),
                status_code: t.get("status_code").and_then(|s| s.as_u64()).map(|n| n as u16),
                content_type: t.get("content_type").or(t.get("response_body_type")).and_then(|c| c.as_str()).map(|s| s.to_string()),
                request_size: t.get("request_size").and_then(|n| n.as_u64()).unwrap_or(0),
                response_size: t.get("response_size").and_then(|n| n.as_u64()).unwrap_or(0),
                duration: t.get("duration_ms").or(t.get("duration")).and_then(|n| n.as_u64()).unwrap_or(0) as u32,
                is_blocked: t.get("blocked").and_then(|b| b.as_bool()).unwrap_or(false),
                has_alert: t.get("alerts").and_then(|a| a.as_array()).map(|a| !a.is_empty()).unwrap_or(false),
                category: t.get("category").and_then(|c| c.as_str()).map(|s| s.to_string()),
            })
        }).collect()
    } else {
        vec![]
    }
}

fn parse_alerts(json: Value) -> Vec<Alert> {
    if let Some(alerts) = json.get("alerts").and_then(|a| a.as_array()) {
        alerts.iter().filter_map(|a| {
            Some(Alert {
                id: a.get("id")?.as_str()?.to_string(),
                timestamp: a.get("timestamp")?.as_str()?.to_string(),
                device_id: a.get("device_id").or(a.get("source_device")).and_then(|d| d.as_str()).map(|s| s.to_string()),
                severity: a.get("severity")?.as_str()?.to_string(),
                category: a.get("category")?.as_str()?.to_string(),
                title: a.get("title")?.as_str()?.to_string(),
                description: a.get("description").and_then(|d| d.as_str()).unwrap_or("").to_string(),
                url: a.get("url").and_then(|u| u.as_str()).map(|s| s.to_string()),
                matched_keywords: a.get("matched_keyword").and_then(|k| k.as_str()).map(|s| vec![s.to_string()]),
                is_read: a.get("acknowledged").and_then(|b| b.as_bool()).unwrap_or(false),
                is_resolved: a.get("acknowledged").and_then(|b| b.as_bool()).unwrap_or(false),
            })
        }).collect()
    } else {
        vec![]
    }
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
    let settings = load_settings()?;
    let interface = settings.network_interface.unwrap_or_else(|| "Wi-Fi".to_string());

    // Start ARP gateway with interface
    match start_python_script("python/arp/arp_gateway.py", &["--interface", &interface]) {
        Ok(child) => processes.push(child),
        Err(e) => return Err(format!("Failed to start ARP gateway: {}", e)),
    }

    // Start HTTPS proxy
    match start_python_script("python/https/transparent_proxy.py", &["--action", "start"]) {
        Ok(child) => processes.push(child),
        Err(e) => {
            kill_python_processes(&mut processes);
            return Err(format!("Failed to start HTTPS proxy: {}", e));
        }
    }

    // Start DNS capture with interface
    match start_python_script("python/dns/dns_capture.py", &["--interface", &interface]) {
        Ok(child) => processes.push(child),
        Err(e) => {
            kill_python_processes(&mut processes);
            return Err(format!("Failed to start DNS capture: {}", e));
        }
    }

    *is_monitoring = true;
    
    // Update start time
    let mut start_time = state.start_time.lock().unwrap();
    *start_time = Some(std::time::Instant::now());
    
    log::info!("Monitoring started with {} processes", processes.len());

    Ok(())
}

#[tauri::command]
pub async fn stop_monitoring(state: State<'_, AppState>) -> Result<(), String> {
    let mut is_monitoring = state.is_monitoring.lock().unwrap();
    let mut processes = state.python_processes.lock().unwrap();

    kill_python_processes(&mut processes);
    *is_monitoring = false;
    
    // Clear start time
    let mut start_time = state.start_time.lock().unwrap();
    *start_time = None;

    log::info!("Monitoring stopped");
    Ok(())
}

#[tauri::command]
pub async fn get_status(state: State<'_, AppState>) -> Result<MonitoringStatus, String> {
    let is_monitoring = state.is_monitoring.lock().unwrap();
    let profile = state.current_profile.lock().unwrap();
    let start_time = state.start_time.lock().unwrap();
    
    let uptime = start_time.as_ref()
        .map(|t| t.elapsed().as_secs())
        .unwrap_or(0);

    Ok(MonitoringStatus {
        is_running: *is_monitoring,
        arp_spoofing: *is_monitoring,
        https_proxy: *is_monitoring,
        dns_capture: *is_monitoring,
        stealth_mode: true,
        current_profile: profile.clone(),
        uptime,
        errors: vec![],
    })
}

// ============================================
// Device Commands
// ============================================

#[tauri::command]
pub async fn get_devices() -> Result<Vec<Device>, String> {
    let result = query_database("devices", &[])?;
    
    if result.get("success").and_then(|s| s.as_bool()).unwrap_or(false) {
        Ok(parse_devices(result))
    } else {
        let error = result.get("error").and_then(|e| e.as_str()).unwrap_or("Unknown error");
        Err(error.to_string())
    }
}

#[tauri::command]
pub async fn scan_devices() -> Result<Vec<Device>, String> {
    let result = run_python_script("python/arp/device_scanner.py", &["--scan"])?;
    
    if result.get("success").and_then(|s| s.as_bool()).unwrap_or(false) {
        Ok(parse_devices(result))
    } else {
        let error = result.get("error").and_then(|e| e.as_str()).unwrap_or("Unknown error");
        Err(error.to_string())
    }
}

#[tauri::command]
pub async fn set_device_monitoring(device_id: String, enabled: bool) -> Result<(), String> {
    log::info!("Set device {} monitoring to {}", device_id, enabled);
    
    let enabled_str = if enabled { "1" } else { "0" };
    let result = run_python_script(
        "python/database/db_manager.py",
        &["--action", "update-device", "--device", &device_id, "--monitored", enabled_str]
    )?;
    
    if result.get("success").and_then(|s| s.as_bool()).unwrap_or(false) {
        Ok(())
    } else {
        let error = result.get("error").and_then(|e| e.as_str()).unwrap_or("Unknown error");
        Err(error.to_string())
    }
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
    let mut args: Vec<(&str, String)> = vec![
        ("--limit", limit.unwrap_or(100).to_string()),
    ];
    
    if let Some(ref did) = device_id {
        args.push(("--device", did.clone()));
    }
    
    let args_refs: Vec<(&str, &str)> = args.iter().map(|(k, v)| (*k, v.as_str())).collect();
    let result = query_database("traffic", &args_refs)?;
    
    if result.get("success").and_then(|s| s.as_bool()).unwrap_or(false) {
        Ok(parse_traffic(result))
    } else {
        let error = result.get("error").and_then(|e| e.as_str()).unwrap_or("Unknown error");
        Err(error.to_string())
    }
}

#[tauri::command]
pub async fn search_traffic(query: String) -> Result<Vec<TrafficEntry>, String> {
    log::info!("Searching traffic for: {}", query);
    
    let result = query_database("search", &[("--query", &query)])?;
    
    if result.get("success").and_then(|s| s.as_bool()).unwrap_or(false) {
        // Search results are in "results" not "traffic"
        if let Some(results) = result.get("results").and_then(|r| r.as_array()) {
            let traffic: Vec<TrafficEntry> = results.iter().filter_map(|t| {
                Some(TrafficEntry {
                    id: t.get("id")?.as_str()?.to_string(),
                    timestamp: t.get("timestamp")?.as_str()?.to_string(),
                    device_id: t.get("device_id").and_then(|d| d.as_str()).map(|s| s.to_string()),
                    device_ip: t.get("device_ip").and_then(|d| d.as_str()).unwrap_or("").to_string(),
                    method: t.get("method").and_then(|m| m.as_str()).unwrap_or("GET").to_string(),
                    url: t.get("url").and_then(|u| u.as_str()).unwrap_or("").to_string(),
                    host: t.get("host").and_then(|h| h.as_str()).unwrap_or("").to_string(),
                    path: t.get("path").and_then(|p| p.as_str()).map(|s| s.to_string()),
                    status_code: t.get("status_code").and_then(|s| s.as_u64()).map(|n| n as u16),
                    content_type: t.get("content_type").and_then(|c| c.as_str()).map(|s| s.to_string()),
                    request_size: t.get("request_size").and_then(|n| n.as_u64()).unwrap_or(0),
                    response_size: t.get("response_size").and_then(|n| n.as_u64()).unwrap_or(0),
                    duration: t.get("duration_ms").and_then(|n| n.as_u64()).unwrap_or(0) as u32,
                    is_blocked: t.get("blocked").and_then(|b| b.as_bool()).unwrap_or(false),
                    has_alert: t.get("alerts").and_then(|a| a.as_array()).map(|a| !a.is_empty()).unwrap_or(false),
                    category: t.get("category").and_then(|c| c.as_str()).map(|s| s.to_string()),
                })
            }).collect();
            Ok(traffic)
        } else {
            Ok(vec![])
        }
    } else {
        let error = result.get("error").and_then(|e| e.as_str()).unwrap_or("Unknown error");
        Err(error.to_string())
    }
}

#[tauri::command]
pub async fn get_traffic_details(entry_id: String) -> Result<TrafficEntry, String> {
    let result = run_python_script(
        "python/database/db_manager.py",
        &["--action", "get-traffic", "--id", &entry_id]
    )?;
    
    if result.get("success").and_then(|s| s.as_bool()).unwrap_or(false) {
        let entries = parse_traffic(result);
        entries.into_iter().next().ok_or_else(|| "Traffic entry not found".to_string())
    } else {
        let error = result.get("error").and_then(|e| e.as_str()).unwrap_or("Unknown error");
        Err(error.to_string())
    }
}

// ============================================
// Alert Commands
// ============================================

#[tauri::command]
pub async fn get_alerts(unread_only: Option<bool>) -> Result<Vec<Alert>, String> {
    let result = run_alert_command("list", &[])?;
    
    if result.get("success").and_then(|s| s.as_bool()).unwrap_or(false) {
        let mut alerts = parse_alerts(result);
        
        // Filter unread if requested
        if unread_only.unwrap_or(false) {
            alerts.retain(|a| !a.is_read);
        }
        
        Ok(alerts)
    } else {
        let error = result.get("error").and_then(|e| e.as_str()).unwrap_or("Unknown error");
        Err(error.to_string())
    }
}

#[tauri::command]
pub async fn mark_alert_read(alert_id: String) -> Result<(), String> {
    log::info!("Marking alert as read: {}", alert_id);
    
    let result = run_alert_command("acknowledge", &[("--id", &alert_id)])?;
    
    if result.get("success").and_then(|s| s.as_bool()).unwrap_or(false) {
        Ok(())
    } else {
        let error = result.get("error").and_then(|e| e.as_str()).unwrap_or("Unknown error");
        Err(error.to_string())
    }
}

#[tauri::command]
pub async fn resolve_alert(alert_id: String) -> Result<(), String> {
    log::info!("Resolving alert: {}", alert_id);
    
    let result = run_alert_command("acknowledge", &[("--id", &alert_id)])?;
    
    if result.get("success").and_then(|s| s.as_bool()).unwrap_or(false) {
        Ok(())
    } else {
        let error = result.get("error").and_then(|e| e.as_str()).unwrap_or("Unknown error");
        Err(error.to_string())
    }
}

#[tauri::command]
pub async fn delete_alert(alert_id: String) -> Result<(), String> {
    log::info!("Deleting alert: {}", alert_id);
    
    let result = run_alert_command("delete", &[("--id", &alert_id)])?;
    
    if result.get("success").and_then(|s| s.as_bool()).unwrap_or(false) {
        Ok(())
    } else {
        let error = result.get("error").and_then(|e| e.as_str()).unwrap_or("Unknown error");
        Err(error.to_string())
    }
}

#[tauri::command]
pub async fn mark_all_alerts_read() -> Result<(), String> {
    let result = run_alert_command("acknowledge-all", &[])?;
    
    if result.get("success").and_then(|s| s.as_bool()).unwrap_or(false) {
        Ok(())
    } else {
        let error = result.get("error").and_then(|e| e.as_str()).unwrap_or("Unknown error");
        Err(error.to_string())
    }
}

// ============================================
// Stats Commands
// ============================================

#[tauri::command]
pub async fn get_stats() -> Result<DashboardStats, String> {
    let result = query_database("stats", &[])?;
    
    if result.get("success").and_then(|s| s.as_bool()).unwrap_or(false) {
        let stats = result.get("stats").unwrap_or(&result);
        
        // Parse top domains
        let top_domains: Vec<TopDomain> = if let Some(domains) = stats.get("top_domains").and_then(|d| d.as_object()) {
            domains.iter().map(|(k, v)| TopDomain {
                domain: k.clone(),
                count: v.as_u64().unwrap_or(0),
            }).collect()
        } else {
            vec![]
        };
        
        Ok(DashboardStats {
            total_devices: stats.get("device_count").and_then(|n| n.as_u64()).unwrap_or(0) as u32,
            online_devices: stats.get("online_devices").and_then(|n| n.as_u64()).unwrap_or(0) as u32,
            total_requests: stats.get("traffic_count").and_then(|n| n.as_u64()).unwrap_or(0),
            blocked_requests: stats.get("blocked_count").and_then(|n| n.as_u64()).unwrap_or(0),
            total_alerts: stats.get("alert_count").and_then(|n| n.as_u64()).unwrap_or(0) as u32,
            unresolved_alerts: stats.get("unresolved_alerts").and_then(|n| n.as_u64()).unwrap_or(0) as u32,
            total_bandwidth: stats.get("bytes_in").and_then(|n| n.as_u64()).unwrap_or(0)
                + stats.get("bytes_out").and_then(|n| n.as_u64()).unwrap_or(0),
            top_domains,
            traffic_by_hour: vec![], // TODO: Implement hourly aggregation
        })
    } else {
        // Return empty stats on error (database might not exist yet)
        Ok(DashboardStats {
            total_devices: 0,
            online_devices: 0,
            total_requests: 0,
            blocked_requests: 0,
            total_alerts: 0,
            unresolved_alerts: 0,
            total_bandwidth: 0,
            top_domains: vec![],
            traffic_by_hour: vec![],
        })
    }
}

// ============================================
// Blocking Commands
// ============================================

#[tauri::command]
pub async fn add_block_rule(rule_type: String, value: String) -> Result<(), String> {
    log::info!("Adding block rule: {} - {}", rule_type, value);
    
    let action = match rule_type.as_str() {
        "domain" => "block",
        "category" => "block-category",
        "keyword" => "add-keyword",
        _ => return Err(format!("Unknown rule type: {}", rule_type)),
    };
    
    let arg_name = match rule_type.as_str() {
        "domain" => "--domain",
        "category" => "--category",
        "keyword" => "--keyword",
        _ => "--domain",
    };
    
    let result = run_blocking_command(action, &[(arg_name, &value)])?;
    
    if result.get("success").and_then(|s| s.as_bool()).unwrap_or(false) {
        Ok(())
    } else {
        let error = result.get("error").and_then(|e| e.as_str()).unwrap_or("Unknown error");
        Err(error.to_string())
    }
}

#[tauri::command]
pub async fn remove_block_rule(rule_type: String, value: String) -> Result<(), String> {
    log::info!("Removing block rule: {} - {}", rule_type, value);
    
    let action = match rule_type.as_str() {
        "domain" => "unblock",
        "category" => "unblock-category",
        "keyword" => "remove-keyword",
        _ => return Err(format!("Unknown rule type: {}", rule_type)),
    };
    
    let arg_name = match rule_type.as_str() {
        "domain" => "--domain",
        "category" => "--category",
        "keyword" => "--keyword",
        _ => "--domain",
    };
    
    let result = run_blocking_command(action, &[(arg_name, &value)])?;
    
    if result.get("success").and_then(|s| s.as_bool()).unwrap_or(false) {
        Ok(())
    } else {
        let error = result.get("error").and_then(|e| e.as_str()).unwrap_or("Unknown error");
        Err(error.to_string())
    }
}

#[tauri::command]
pub async fn toggle_category(category_id: String, enabled: bool) -> Result<(), String> {
    log::info!("Toggle category {} to {}", category_id, enabled);
    
    let action = if enabled { "block-category" } else { "unblock-category" };
    let result = run_blocking_command(action, &[("--category", &category_id)])?;
    
    if result.get("success").and_then(|s| s.as_bool()).unwrap_or(false) {
        Ok(())
    } else {
        let error = result.get("error").and_then(|e| e.as_str()).unwrap_or("Unknown error");
        Err(error.to_string())
    }
}

#[tauri::command]
pub async fn get_block_config() -> Result<Value, String> {
    run_blocking_command("config", &[])
}

#[tauri::command]
pub async fn check_domain(domain: String) -> Result<Value, String> {
    run_blocking_command("check", &[("--domain", &domain)])
}

// ============================================
// Settings Commands
// ============================================

#[tauri::command]
pub async fn get_settings() -> Result<Settings, String> {
    load_settings()
}

#[tauri::command]
pub async fn update_settings(settings: Settings) -> Result<(), String> {
    log::info!("Updating settings: {:?}", settings);
    save_settings(&settings)
}

#[tauri::command]
pub async fn change_stealth_profile(
    profile_id: String,
    state: State<'_, AppState>,
) -> Result<(), String> {
    let settings = load_settings()?;
    let interface = settings.network_interface.unwrap_or_else(|| "Wi-Fi".to_string());
    
    // Apply the profile
    let result = run_stealth_command("apply", &interface, Some(&profile_id))?;
    
    if result.get("success").and_then(|s| s.as_bool()).unwrap_or(false) {
        // Update state
        let mut profile = state.current_profile.lock().unwrap();
        *profile = profile_id.clone();
        
        // Save to settings
        let mut settings = load_settings()?;
        settings.device_profile = profile_id;
        save_settings(&settings)?;
        
        log::info!("Changed stealth profile successfully");
        Ok(())
    } else {
        let error = result.get("message").or(result.get("error"))
            .and_then(|e| e.as_str())
            .unwrap_or("Unknown error");
        Err(error.to_string())
    }
}

#[tauri::command]
pub async fn get_stealth_profiles() -> Result<Value, String> {
    run_python_script("python/stealth/mac_changer.py", &["--list-profiles"])
}

// ============================================
// Certificate Commands
// ============================================

#[tauri::command]
pub async fn generate_certificate(profile: String) -> Result<String, String> {
    log::info!("Generating certificate with profile: {}", profile);
    
    let result = run_python_script(
        "python/https/cert_generator.py",
        &["--action", "generate", "--profile", &profile],
    )?;
    
    if result.get("success").and_then(|s| s.as_bool()).unwrap_or(false) {
        let cert_path = result.get("cert_path")
            .and_then(|p| p.as_str())
            .unwrap_or("certs/ca.crt");
        Ok(format!("Certificate generated: {}", cert_path))
    } else {
        let error = result.get("error").and_then(|e| e.as_str()).unwrap_or("Unknown error");
        Err(error.to_string())
    }
}

#[tauri::command]
pub async fn start_cert_server(state: State<'_, AppState>) -> Result<String, String> {
    let mut processes = state.python_processes.lock().unwrap();
    
    match start_python_script("cert-installer/server.py", &[]) {
        Ok(child) => {
            processes.push(child);
            Ok("Certificate server started on port 8888".to_string())
        }
        Err(e) => Err(format!("Failed to start cert server: {}", e)),
    }
}

#[tauri::command]
pub async fn get_cert_url() -> Result<String, String> {
    // Get local IP
    let result = run_python_script("python/utils/network_utils.py", &["--action", "get-ip"])?;
    
    let ip = result.get("ip")
        .and_then(|i| i.as_str())
        .unwrap_or("192.168.1.1");
    
    Ok(format!("http://{}:8888", ip))
}

// ============================================
// Export Commands
// ============================================

#[tauri::command]
pub async fn export_data(format: String, path: String) -> Result<(), String> {
    log::info!("Exporting data as {} to {}", format, path);
    
    let result = run_python_script(
        "python/database/db_manager.py",
        &["--action", "export", "--format", &format, "--output", &path]
    )?;
    
    if result.get("success").and_then(|s| s.as_bool()).unwrap_or(false) {
        Ok(())
    } else {
        let error = result.get("error").and_then(|e| e.as_str()).unwrap_or("Unknown error");
        Err(error.to_string())
    }
}

// ============================================
// Utility Commands
// ============================================

#[tauri::command]
pub async fn get_network_interfaces() -> Result<Value, String> {
    run_python_script("python/utils/network_utils.py", &["--action", "list-interfaces"])
}

#[tauri::command]
pub async fn check_admin() -> Result<bool, String> {
    #[cfg(windows)]
    {
        use std::process::Command;
        let output = Command::new("net")
            .args(["session"])
            .output()
            .map_err(|e| e.to_string())?;
        Ok(output.status.success())
    }
    
    #[cfg(not(windows))]
    {
        Ok(false)
    }
}

#[tauri::command]
pub async fn cleanup_database(days: u32) -> Result<Value, String> {
    run_python_script(
        "python/database/db_manager.py",
        &["--action", "cleanup", "--days", &days.to_string()]
    )
}
