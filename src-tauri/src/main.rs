use std::{
    collections::hash_map::DefaultHasher,
    fs::{self, File, OpenOptions, TryLockError},
    hash::{Hash, Hasher},
    io::{BufRead, BufReader, Write},
    os::unix::fs::OpenOptionsExt,
    path::{Path, PathBuf},
    process::{Child, Command, Stdio},
    sync::{mpsc, Mutex},
    thread,
    time::{Duration, SystemTime, UNIX_EPOCH},
};
use tauri::{Manager, WebviewUrl, WebviewWindow, WebviewWindowBuilder};

#[derive(Default)]
struct Runtime {
    child: Option<Child>,
    port: Option<u16>,
    starting: bool,
    reason: &'static str,
    diagnostic: Option<PathBuf>,
}

type Engine = Mutex<Runtime>;

fn root_path() -> Option<PathBuf> {
    std::env::var_os("JUZHONGSHI_DATA_DIR")
        .map(PathBuf::from)
        .or_else(|| {
            Some(
                PathBuf::from(std::env::var_os("HOME")?).join("Library/Application Support/局中事"),
            )
        })
}

fn stamp() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos()
}

fn recover_url(reason: &str) -> tauri::Url {
    tauri::Url::parse(&format!(
        "tauri://localhost/index.html?reason={reason}&at={}",
        stamp()
    ))
    .unwrap()
}

fn trusted_recovery(url: &tauri::Url) -> bool {
    url.scheme() == "tauri" && url.host_str() == Some("localhost") && url.path() == "/index.html"
}

fn allowed_navigation(runtime: &Runtime, url: &tauri::Url) -> bool {
    if trusted_recovery(url) {
        return runtime.port.is_none();
    }
    url.scheme() == "http"
        && url.host_str() == Some("127.0.0.1")
        && runtime.port.is_some()
        && url.port() == runtime.port
}

fn authorized(window: &WebviewWindow) -> Result<(), String> {
    let origin = window.url().map_err(|_| "无法核验当前页面。")?;
    let engine = window.state::<Engine>();
    let state = engine.lock().map_err(|_| "启动器状态不可用。")?;
    if window.label() != "main"
        || !trusted_recovery(&origin)
        || state.port.is_some()
        || state.starting
    {
        return Err("请在启动恢复页操作。".into());
    }
    Ok(())
}

fn stop(mut child: Child) {
    drop(child.stdin.take());
    for _ in 0..15 {
        if matches!(child.try_wait(), Ok(Some(_))) {
            return;
        }
        thread::sleep(Duration::from_millis(70));
    }
    let _ = child.kill();
    let _ = child.wait();
}

fn failed(app: &tauri::AppHandle, reason: &'static str) {
    let child = {
        let runtime = app.state::<Engine>();
        let Ok(mut s) = runtime.lock() else { return };
        s.port = None;
        s.starting = false;
        s.reason = reason;
        s.child.take()
    };
    if let Some(c) = child {
        stop(c)
    }
    if let Some(w) = app.get_webview_window("main") {
        let _ = w.set_title("局中事 · 启动恢复");
        let _ = w.navigate(recover_url(reason));
    }
}

fn private_file(path: &Path, bytes: &[u8]) -> Result<(), &'static str> {
    let mut f = OpenOptions::new()
        .create_new(true)
        .write(true)
        .mode(0o600)
        .open(path)
        .map_err(|_| "storage")?;
    f.write_all(bytes)
        .and_then(|_| f.sync_all())
        .map_err(|_| "storage")
}

fn launch(app: &tauri::AppHandle, root: &Path, archive: Option<&Path>) -> Result<(), &'static str> {
    let exe = std::env::current_exe().map_err(|_| "component")?;
    let macos = exe.parent().ok_or("component")?;
    let web = macos.parent().ok_or("component")?.join("Resources/web");
    if !web.join("index.html").is_file() {
        return Err("component");
    }
    let restored = root.join("已恢复档案");
    let marker = root.join("当前使用恢复档案");
    let data = if archive.is_some() || marker.is_file() {
        restored.as_path()
    } else {
        root
    };
    let mut cmd = Command::new(macos.join("jzs-engine"));
    cmd.args(["--desktop", "--assets"])
        .arg(web)
        .arg("--data-dir")
        .arg(data);
    if let Some(file) = archive {
        cmd.arg("--restore-file").arg(file);
    }
    let mut child = cmd
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|_| "component")?;
    let stdout = child.stdout.take().ok_or("component")?;
    let (sender, receiver) = mpsc::channel();
    thread::spawn(move || {
        let mut line = String::new();
        if BufReader::new(stdout).read_line(&mut line).is_ok() {
            let _ = sender.send(line);
        }
    });
    let check = (|| {
        let line = receiver
            .recv_timeout(Duration::from_secs(30))
            .map_err(|_| "handshake")?;
        if line.trim().is_empty() {
            return Err(if archive.is_some() {
                "archive"
            } else {
                "startup"
            });
        }
        let url = tauri::Url::parse(line.trim()).map_err(|_| "handshake")?;
        if url.scheme() != "http"
            || url.host_str() != Some("127.0.0.1")
            || url.path() != "/"
            || !url.fragment().is_some_and(|f| f.starts_with("session="))
        {
            return Err("handshake");
        }
        let port = url.port().ok_or("handshake")?;
        if archive.is_some() && !marker.is_file() {
            private_file(&marker, b"recovery-v1\n")?;
        }
        Ok((url, port))
    })();
    let (url, port) = match check {
        Ok(x) => x,
        Err(code) => {
            stop(child);
            return Err(code);
        }
    };
    {
        let runtime = app.state::<Engine>();
        let mut s = runtime.lock().map_err(|_| "startup")?;
        s.child = Some(child);
        s.port = Some(port);
        s.starting = false;
        s.reason = "";
    }
    let window = app.get_webview_window("main").ok_or("window")?;
    window.set_title("局中事").map_err(|_| "window")?;
    window.navigate(url).map_err(|_| "window")?;
    Ok(())
}

fn begin(app: tauri::AppHandle, archive: Option<String>) -> Result<(), String> {
    {
        let runtime = app.state::<Engine>();
        let mut s = runtime.lock().map_err(|_| "启动器状态不可用。")?;
        if s.starting || s.child.is_some() {
            return Err("引擎正在运行。".into());
        }
        s.starting = true;
    }
    thread::spawn(move || {
        let result = (|| {
            let root = root_path().ok_or("storage")?;
            fs::create_dir_all(&root).map_err(|_| "storage")?;
            let temp = archive
                .map(|text| {
                    let file =
                        root.join(format!(".import-{}-{}.json", std::process::id(), stamp()));
                    if let Err(code) = private_file(&file, text.as_bytes()) {
                        let _ = fs::remove_file(&file);
                        return Err(code);
                    }
                    Ok(file)
                })
                .transpose()?;
            let result = launch(&app, &root, temp.as_deref());
            if let Some(path) = temp {
                let _ = fs::remove_file(path);
            }
            result
        })();
        if let Err(code) = result {
            failed(&app, code)
        }
    });
    Ok(())
}

#[tauri::command]
fn recover_engine(window: WebviewWindow, archive: Option<String>) -> Result<(), String> {
    authorized(&window)?;
    begin(window.app_handle().clone(), archive)
}

#[tauri::command]
fn save_diagnostic(window: WebviewWindow) -> Result<String, String> {
    authorized(&window)?;
    let root = root_path().ok_or("无法定位诊断目录。")?;
    let dir = root.join("启动诊断");
    fs::create_dir_all(&dir).map_err(|_| "无法写入诊断目录。")?;
    let runtime = window.state::<Engine>();
    let mut s = runtime.lock().map_err(|_| "启动器状态不可用。")?;
    let file = dir.join(format!("启动诊断-{}.txt", stamp()));
    let report = format!(
        "局中事 · 启动诊断\n版本 {}\n架构 {}\n系统 {}\n阶段 {}\n使用独立恢复档案 {}\n",
        env!("CARGO_PKG_VERSION"),
        std::env::consts::ARCH,
        std::env::consts::OS,
        s.reason,
        root.join("当前使用恢复档案").is_file()
    );
    private_file(&file, report.as_bytes()).map_err(|_| "无法写入诊断文件。")?;
    s.diagnostic = Some(file);
    Ok("已保存本次诊断。".into())
}

#[tauri::command]
fn reveal_diagnostic(window: WebviewWindow) -> Result<(), String> {
    authorized(&window)?;
    let runtime = window.state::<Engine>();
    let s = runtime.lock().map_err(|_| "启动器状态不可用。")?;
    let file = s.diagnostic.as_ref().ok_or("请先导出诊断。")?;
    Command::new("/usr/bin/open")
        .arg("-R")
        .arg(file)
        .spawn()
        .map_err(|_| "无法打开访达。")?;
    Ok(())
}

fn claim_instance(identifier: &str) -> std::io::Result<Option<File>> {
    // The lock survives the entire run and the OS releases it even after a crash.
    // A second process leaves a focus request without starting a second engine.
    let path = std::env::temp_dir().join(format!("{identifier}.instance"));
    let mut file = OpenOptions::new()
        .create(true)
        .read(true)
        .append(true)
        .mode(0o600)
        .open(path)?;
    match file.try_lock() {
        Ok(()) => {
            file.set_len(0)?;
            Ok(Some(file))
        }
        Err(TryLockError::WouldBlock) => {
            file.write_all(b".")?;
            Ok(None)
        }
        Err(TryLockError::Error(error)) => Err(error),
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut context = tauri::generate_context!();
    // Explicit data directories are separate player profiles. Each profile still has a single launcher.
    if let Some(path) = std::env::var_os("JUZHONGSHI_DATA_DIR") {
        let path = PathBuf::from(path);
        let _ = fs::create_dir_all(&path);
        let mut hash = DefaultHasher::new();
        path.canonicalize().unwrap_or(path).hash(&mut hash);
        context.config_mut().identifier =
            format!("games.juzhongshi.profile.{:016x}", hash.finish());
    }
    let Some(instance) = claim_instance(&context.config().identifier)? else {
        return Ok(());
    };
    let focus_requests = instance.try_clone()?;
    let app = tauri::Builder::default()
        .manage(Engine::default())
        .invoke_handler(tauri::generate_handler![
            recover_engine,
            save_diagnostic,
            reveal_diagnostic
        ])
        .setup(move |app| {
            let handle = app.handle().clone();
            let nav = handle.clone();
            WebviewWindowBuilder::new(
                app,
                "main",
                WebviewUrl::App("index.html?reason=starting".into()),
            )
            .title("局中事")
            .inner_size(1240., 820.)
            .min_inner_size(720., 520.)
            .on_navigation(move |url| {
                let s = nav.state::<Engine>();
                let allowed = s.lock().is_ok_and(|v| allowed_navigation(&v, url));
                allowed
            })
            .build()?;
            begin(handle.clone(), None).map_err(std::io::Error::other)?;
            thread::spawn(move || loop {
                thread::sleep(Duration::from_millis(350));
                let Some(window) = handle.get_webview_window("main") else {
                    break;
                };
                if focus_requests.metadata().is_ok_and(|stat| stat.len() > 0) {
                    let _ = focus_requests.set_len(0);
                    let _ = window.unminimize();
                    let _ = window.show();
                    let _ = window.set_focus();
                }
                let died = {
                    let runtime = handle.state::<Engine>();
                    let mut s = runtime.lock().unwrap();
                    s.child
                        .as_mut()
                        .is_some_and(|c| matches!(c.try_wait(), Ok(Some(_))))
                };
                if died {
                    failed(&handle, "exited");
                }
            });
            Ok(())
        })
        .build(context)
        .expect("无法创建游戏窗口");
    app.run(|app, event| {
        if matches!(event, tauri::RunEvent::Exit) {
            if let Ok(mut s) = app.state::<Engine>().lock() {
                if let Some(c) = s.child.take() {
                    stop(c);
                }
            }
        }
    });
    Ok(())
}
