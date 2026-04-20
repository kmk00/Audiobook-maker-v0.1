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
    let api_cmd = "call C:\\Users\\Lukasz\\miniconda3\\Scripts\\activate.bat ABApi && cd /d C:\\Users\\Lukasz\\Desktop\\Audiobook\\project\\backend && uvicorn main:app --port 8000";
    
    let xtts_cmd = "call C:\\Users\\Lukasz\\miniconda3\\Scripts\\activate.bat Audiobook3.10 && cd /d C:\\Users\\Lukasz\\Desktop\\Audiobook\\project\\backend && uvicorn workers.xtts_worker:app --port 8001";
    
    let qwen_cmd = "call C:\\Users\\Lukasz\\miniconda3\\Scripts\\activate.bat ABqwen3.12 && cd /d C:\\Users\\Lukasz\\Desktop\\Audiobook\\project\\backend && uvicorn workers.qwen_worker:app --port 8002";
    
    let omni_cmd = "call C:\\Users\\Lukasz\\miniconda3\\Scripts\\activate.bat ABOmnivoice && cd /d C:\\Users\\Lukasz\\Desktop\\Audiobook\\project\\backend && uvicorn workers.omnivoice_worker:app --port 8003";

    let mut children = Vec::new();

    if let Some(c) = spawn_worker(api_cmd) { children.push(c); }
    if let Some(c) = spawn_worker(xtts_cmd) { children.push(c); }
    if let Some(c) = spawn_worker(qwen_cmd) { children.push(c); }
    if let Some(c) = spawn_worker(omni_cmd) { children.push(c); }

    let app_state = AppState {
        children: Mutex::new(children),
    };

    let app = tauri::Builder::default()
        .manage(app_state)
        .build(tauri::generate_context!())
        .expect("error while running tauri application");

    app.run(move |app_handle, event| {
        match event {
            RunEvent::ExitRequested { .. } => {
                let state = app_handle.state::<AppState>();
                let mut children = state.children.lock().unwrap();
                for mut child in children.drain(..) {
                    let _ = child.kill();
                    let _ = child.wait();
                }
                println!("Wszystkie mikroserwisy zostały zamknięte.");
            }
            _ => {}
        }
    });
}
