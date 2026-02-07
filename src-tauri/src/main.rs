// Network Monitor - Tauri Backend
// Main entry point for the Rust backend

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod python;
mod state;

use state::AppState;
use std::sync::Mutex;
use tauri::Manager;

fn main() {
    env_logger::init();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(AppState {
            is_monitoring: Mutex::new(false),
            python_processes: Mutex::new(Vec::new()),
            current_profile: Mutex::new(String::from("hp_printer")),
            start_time: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![
            // Monitoring
            commands::start_monitoring,
            commands::stop_monitoring,
            commands::get_status,
            // Devices
            commands::get_devices,
            commands::scan_devices,
            commands::set_device_monitoring,
            // Traffic
            commands::get_traffic,
            commands::search_traffic,
            commands::get_traffic_details,
            // Alerts
            commands::get_alerts,
            commands::mark_alert_read,
            commands::resolve_alert,
            commands::delete_alert,
            commands::mark_all_alerts_read,
            // Stats
            commands::get_stats,
            // Blocking
            commands::add_block_rule,
            commands::remove_block_rule,
            commands::toggle_category,
            commands::get_block_config,
            commands::check_domain,
            // Settings
            commands::get_settings,
            commands::update_settings,
            // Stealth
            commands::change_stealth_profile,
            commands::get_stealth_profiles,
            // Certificates
            commands::generate_certificate,
            commands::start_cert_server,
            commands::get_cert_url,
            // Export
            commands::export_data,
            // Utilities
            commands::get_network_interfaces,
            commands::check_admin,
            commands::cleanup_database,
        ])
        .setup(|app| {
            let window = app.get_webview_window("main").unwrap();
            
            // Set window title
            window.set_title("Network Monitor")?;
            
            log::info!("Network Monitor started");
            
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                // Hide to tray instead of closing
                window.hide().unwrap();
                api.prevent_close();
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
