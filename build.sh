#!/bin/bash
# Local build script for Linux
set -e

echo "Installing build dependencies..."
./venv/bin/pip install pyinstaller

echo "Building Linux executable..."
./venv/bin/pyinstaller --noconfirm ConnectKbM.spec

echo ""
echo "Build complete! Output: dist/ConnectKbM/"
echo "Prerequisites: scrcpy, adb (must be installed on the target system)"