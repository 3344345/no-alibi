"""Make the signed update.json that accompanies the three desktop downloads."""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys
import tarfile
from tempfile import NamedTemporaryFile
from zipfile import ZipFile

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from game.update_trust import PUBLIC_KEY_B64, VERSION
from game.updater import PACKAGES


def packaged_version(path, marker):
    if path.suffix == ".zip":
        with ZipFile(path, metadata_encoding="utf-8") as archive:
            raw = archive.read(marker)
    else:
        with tarfile.open(path, "r:gz") as archive:
            raw = archive.extractfile(marker).read(32)
    return raw.decode("ascii").strip()


def sign(directory, key_file):
    if (ROOT / "VERSION").read_text().strip() != VERSION:
        raise ValueError("仓库 VERSION 与游戏内版本不一致")
    private = serialization.load_pem_private_key(key_file.read_bytes(), password=None)
    if not isinstance(private, Ed25519PrivateKey) or (
        private.public_key().public_bytes_raw() != base64.b64decode(PUBLIC_KEY_B64)
    ):
        raise ValueError("此签名密钥与玩家版本中保存的公钥不匹配")
    assets = {}
    for platform, (name, marker, *_) in PACKAGES.items():
        path = directory / name.replace("no-alibi-", "局中事-", 1)
        if packaged_version(path, marker) != VERSION:
            raise ValueError(f"{path.name} 尚未构建为 {VERSION}")
        with path.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        assets[platform] = {"name": name, "size": path.stat().st_size, "sha256": digest}
    manifest = {"schema": 1, "version": VERSION, "tag": "v" + VERSION, "assets": assets}
    wire = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    signature = base64.b64encode(private.sign(wire)).decode("ascii")
    with NamedTemporaryFile(dir=directory, mode="w", encoding="utf-8", delete=False) as out:
        json.dump({"manifest": manifest, "signature": signature}, out, indent=2)
        out.write("\n")
    Path(out.name).replace(directory / "update.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-dir", type=Path, default=ROOT / "release")
    parser.add_argument("--key", type=Path,
                        default=Path.home() / "Library/Application Support/局中事发行/update-ed25519.pem")
    args = parser.parse_args()
    sign(args.release_dir, args.key)
    print("已生成", args.release_dir / "update.json")
