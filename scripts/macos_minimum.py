"""Set the release bundle's macOS floor from its actual arm64 executables and libraries."""

from pathlib import Path
import plistlib
import sys
from tempfile import TemporaryDirectory

from PyInstaller.archive.readers import CArchiveReader
from PyInstaller.utils.osx import get_binary_architectures, macosx_version_min


def deployment_version(path):
    _, architectures = get_binary_architectures(str(path))
    if architectures != ["arm64"]:
        raise ValueError(f"Expected an arm64 release component: {path.name}")
    return macosx_version_min(str(path))


def update(bundle):
    contents = bundle / "Contents"
    info_path = contents / "Info.plist"
    info = plistlib.loads(info_path.read_bytes())
    launcher = contents / "MacOS" / info["CFBundleExecutable"]
    engine = contents / "MacOS" / "jzs-engine"
    versions = [
        tuple(map(int, info["LSMinimumSystemVersion"].split("."))),
        deployment_version(launcher),
        deployment_version(engine),
    ]
    archive = CArchiveReader(str(engine))
    with TemporaryDirectory() as folder:
        component = Path(folder) / "component"
        for name, entry in archive.toc.items():
            if entry[-1] == "b":
                component.write_bytes(archive.extract(name))
                versions.append(deployment_version(component))

    major, minor, *patch = max(versions)
    minimum = f"{major}.{minor}"
    if patch and patch[0]:
        minimum += f".{patch[0]}"
    info["LSMinimumSystemVersion"] = minimum
    info_path.write_bytes(plistlib.dumps(info, sort_keys=False))
    print(f"Apple Silicon · macOS 最低二进制版本 {minimum}")


if __name__ == "__main__":
    update(Path(sys.argv[1]))
