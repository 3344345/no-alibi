use std::{
    fs,
    os::unix::process::CommandExt,
    path::{Path, PathBuf},
    process::Command,
};

pub const PLATFORM: &str = "macos-arm64";
pub const VERSION: &str = include_str!("../../VERSION");

fn version(text: &str) -> Option<[u32; 3]> {
    fn part(s: &str) -> Option<u32> {
        if s.is_empty()
            || s.len() > 6
            || (s.len() > 1 && s.starts_with('0'))
            || !s.bytes().all(|c| c.is_ascii_digit())
        {
            return None;
        }
        s.parse().ok()
    }
    let mut chunks = text.split('.');
    let values = [
        part(chunks.next()?)?,
        part(chunks.next()?)?,
        part(chunks.next()?)?,
    ];
    chunks.next().is_none().then_some(values)
}

fn active_executable(root: &Path) -> Option<PathBuf> {
    let updates = root.join("updates");
    let pointer = fs::read_to_string(updates.join(format!("{PLATFORM}.active"))).ok()?;
    let number = pointer.trim_end_matches(['\r', '\n']);
    if version(number)? <= version(VERSION.trim())? {
        return None;
    }
    let contents = updates
        .join("versions")
        .join(number)
        .join(PLATFORM)
        .join("局中事.app/Contents");
    let marker = fs::read_to_string(contents.join("Resources/VERSION")).ok()?;
    if marker.trim_end_matches(['\r', '\n']) != number
        || !contents.join("Resources/web/index.html").is_file()
        || !contents.join("MacOS/jzs-engine").is_file()
    {
        return None;
    }
    let binary = contents.join("MacOS/juzhongshi");
    (binary.is_file() && fs::canonicalize(&binary).ok()? != std::env::current_exe().ok()?)
        .then_some(binary)
}

pub fn activate(root: &Path) {
    if let Some(path) = active_executable(root) {
        // exec retains the Finder-launched process and its single-instance identity.
        // If the OS cannot load the staged application, this installation starts normally.
        let _ = Command::new(path).args(std::env::args_os().skip(1)).exec();
    }
}
