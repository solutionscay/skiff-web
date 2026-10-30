#!/usr/bin/env python3
"""Render tools/social-preview.html to social-preview.png (1280x640) with
headless Chrome. Fonts come from Google Fonts, so it needs the network.

    python3 tools/social-preview.py

After a change, bump ?v= on og:image in tools/build.py and run build.py."""
import os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "social-preview.html")
OUT = os.path.join(ROOT, "social-preview.png")

chrome = next((c for c in ("google-chrome", "chromium", "chromium-browser", "chrome") if shutil.which(c)), None)
if not chrome:
    sys.exit("no Chrome or Chromium on PATH")
subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                "--window-size=1280,640", "--virtual-time-budget=10000", "--force-device-scale-factor=1",
                "--screenshot=" + OUT, "file://" + SRC], check=True, stderr=subprocess.DEVNULL)
print("wrote: social-preview.png")
