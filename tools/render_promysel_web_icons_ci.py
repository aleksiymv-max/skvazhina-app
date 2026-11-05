#!/usr/bin/env python3
"""Generate Promysel icons with standard JDK ImageIO; no apt or third-party tools."""
import base64
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def main():
    require(len(sys.argv) == 2 and sys.argv[1] in ("app", "web"),
            "Usage: render_promysel_web_icons_ci.py app|web")
    require(shutil.which("java") is not None,
            "GitHub runner needs preinstalled JDK Java to render icons offline")
    root = Path(os.environ.get("GITHUB_WORKSPACE", Path.cwd()))
    source = (root / "assets/promysel_icon_modern.svg").read_text(encoding="utf-8")
    jpeg = re.search(r'data:image/jpeg;base64,([A-Za-z0-9+/=]+)', source)
    require(jpeg is not None and source.count("<image") == 1
            and "<path" not in source and "<rect" not in source,
            "Promysel SVG changed: expected one embedded JPEG without vector overlays")
    mode = sys.argv[1]
    jobs = (
        [(1024, Path("assets/icon/app_icon.png"))]
        if mode == "app" else [
            (192, Path("web/icons/Icon-192.png")),
            (512, Path("web/icons/Icon-512.png")),
            (64, Path("web/favicon.png")),
            (180, Path("web/apple-touch-icon.png")),
        ]
    )
    with tempfile.TemporaryDirectory(prefix="promysel-icon-") as directory:
        jpg = Path(directory) / "icon.jpg"
        jpg.write_bytes(base64.b64decode(jpeg.group(1), validate=True))
        require(jpg.read_bytes().startswith(b"\xff\xd8\xff"),
                "Invalid embedded JPEG")
        cmd = [
            "java", "-Djava.awt.headless=true",
            str(root / "tools/PromyselIconResizer.java"), str(jpg),
        ]
        for size, destination in jobs:
            cmd.extend((str(size), str(destination)))
        subprocess.run(cmd, check=True, timeout=45)
    for size, destination in jobs:
        data = destination.read_bytes()
        require(data.startswith(b"\x89PNG\r\n\x1a\n"), f"Not a PNG: {destination}")
        require(struct.unpack(">II", data[16:24]) == (size, size),
                f"Wrong PNG dimensions: {destination}")
    if mode == "app":
        shutil.copyfile("assets/icon/app_icon.png",
                        "assets/icon/app_icon_foreground.png")
    else:
        shutil.copyfile("web/icons/Icon-192.png", "web/icons/Icon-maskable-192.png")
        shutil.copyfile("web/icons/Icon-512.png", "web/icons/Icon-maskable-512.png")
    print(f"PASS: {mode} icon assets created offline with preinstalled Java; no apt-get")

if __name__ == "__main__":
    main()
