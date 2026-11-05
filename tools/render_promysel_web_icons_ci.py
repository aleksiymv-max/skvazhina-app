#!/usr/bin/env python3
"""Render the embedded JPEG-only Promysel icon into PNG sizes without apt-get.

The source SVG is a 256x256 image wrapper with one embedded JPEG. The GitHub
Ubuntu runner ships ffmpeg, so converting that JPEG directly avoids slow or
stalled apt repository updates while retaining the original icon artwork.
"""
import base64
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)

def encode_png(image, size, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(image), "-vf", f"scale={size}:{size}:flags=lanczos",
        "-frames:v", "1", str(path),
    ], check=True, timeout=35)
    data = path.read_bytes()
    require(data.startswith(b"\x89PNG\r\n\x1a\n"), f"Not PNG: {path}")
    width, height = struct.unpack(">II", data[16:24])
    require((width, height) == (size, size), f"Wrong size: {path}")

def main():
    require(len(sys.argv) == 2 and sys.argv[1] in ("app", "web"),
            "Usage: render_promysel_web_icons_ci.py app|web")
    require(shutil.which("ffmpeg") is not None,
            "Preinstalled ffmpeg is required; never wait for apt repositories")
    workspace = Path(os.environ.get("GITHUB_WORKSPACE", Path.cwd()))
    svg_path = workspace / "assets/promysel_icon_modern.svg"
    source = svg_path.read_text(encoding="utf-8")
    match = re.search(r'data:image/jpeg;base64,([A-Za-z0-9+/=]+)', source)
    require(match is not None and source.count("<image") == 1
            and "<path" not in source and "<rect" not in source,
            "Icon SVG no longer contains exactly one embedded JPEG; update renderer")
    with tempfile.TemporaryDirectory(prefix="promysel-icons-") as tmp:
        image = Path(tmp) / "promysel.jpg"
        image.write_bytes(base64.b64decode(match.group(1), validate=True))
        require(image.read_bytes().startswith(b"\xff\xd8\xff"),
                "Embedded source is not JPEG")
        if sys.argv[1] == "app":
            encode_png(image, 1024, Path("assets/icon/app_icon.png"))
            shutil.copyfile("assets/icon/app_icon.png",
                            "assets/icon/app_icon_foreground.png")
        else:
            encode_png(image, 192, Path("web/icons/Icon-192.png"))
            encode_png(image, 512, Path("web/icons/Icon-512.png"))
            shutil.copyfile("web/icons/Icon-192.png",
                            "web/icons/Icon-maskable-192.png")
            shutil.copyfile("web/icons/Icon-512.png",
                            "web/icons/Icon-maskable-512.png")
            encode_png(image, 64, Path("web/favicon.png"))
            encode_png(image, 180, Path("web/apple-touch-icon.png"))
    print(f"PASS: preinstalled ffmpeg rendered Promysel {sys.argv[1]} icons; no apt-get")

if __name__ == "__main__":
    main()
