use std::{
    fs,
    os::unix::{fs::PermissionsExt, process::CommandExt},
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

fn ready_file(path: &Path, executable: bool) -> bool {
    fs::metadata(path).is_ok_and(|m| {
        // Staging extracts this user's files into this user's application data directory.
        m.is_file() && m.len() > 0 && (!executable || m.permissions().mode() & 0o100 != 0)
    })
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
        || !ready_file(&contents.join("Resources/web/index.html"), false)
        || !ready_file(&contents.join("MacOS/jzs-engine"), true)
    {
        return None;
    }
    let binary = contents.join("MacOS/juzhongshi");
    (ready_file(&binary, true)
        && fs::canonicalize(&binary).ok()? != std::env::current_exe().ok()?)
    .then_some(binary)
}

pub fn activate(root: &Path) {
    if let Some(path) = active_executable(root) {
        // exec retains the Finder-launched process and its single-instance identity.
        // If the OS cannot load the staged application, this installation starts normally.
        let _ = Command::new(path).args(std::env::args_os().skip(1)).exec();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::{SystemTime, UNIX_EPOCH};

    #[test]
    fn damaged_staged_app_leaves_original_as_entry() {
        let stamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let root =
            std::env::temp_dir().join(format!("jzs-update-test-{}-{stamp}", std::process::id()));
        let updates = root.join("updates");
        let bundle = updates.join("versions/999999.0.0/macos-arm64/局中事.app/Contents");
        let macos = bundle.join("MacOS");
        let web = bundle.join("Resources/web");
        fs::create_dir_all(&macos).unwrap();
        fs::create_dir_all(&web).unwrap();
        fs::write(updates.join("macos-arm64.active"), "999999.0.0\n").unwrap();
        fs::write(bundle.join("Resources/VERSION"), "999999.0.0\n").unwrap();
        let index = web.join("index.html");
        fs::write(&index, "fixture").unwrap();
        let launcher = macos.join("juzhongshi");
        let engine = macos.join("jzs-engine");
        for binary in [&launcher, &engine] {
            fs::write(binary, "fixture").unwrap();
            fs::set_permissions(binary, fs::Permissions::from_mode(0o700)).unwrap();
        }
        assert_eq!(active_executable(&root), Some(launcher));
        fs::set_permissions(&engine, fs::Permissions::from_mode(0o600)).unwrap();
        assert!(active_executable(&root).is_none());
        fs::set_permissions(&engine, fs::Permissions::from_mode(0o700)).unwrap();
        fs::write(&index, "").unwrap();
        assert!(active_executable(&root).is_none());
        fs::remove_dir_all(root).unwrap();
    }
}
