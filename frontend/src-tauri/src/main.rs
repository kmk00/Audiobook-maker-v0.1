// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Command, Child};
use std::sync::Mutex;
use tauri::{Manager, RunEvent, WindowEvent};

struct AppState {
    children: Mutex<Vec<Child>>,
}

fn spawn_worker(command: &str) -> Option<Child> {
    println!("Uruchamianie: {}", command);
    
    let child = Command::new("cmd")
        .args(["/C", command])
        // .creation_flags(0x08000000)
        .spawn()
        .map_err(|e| println!("Błąd uruchamiania procesu: {}", e))
        .ok()?;
        
    Some(child)
}

fn main() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
