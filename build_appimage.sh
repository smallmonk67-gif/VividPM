#!/bin/bash
set -e

# Configuration
APP_NAME="VividPM"
PYTHON_VERSION="3.12"
PLATFORM="x86_64-unknown-linux-gnu"
PYTHON_BUILD_TAG="20260510"
PYTHON_URL="https://github.com/astral-sh/python-build-standalone/releases/download/${PYTHON_BUILD_TAG}/cpython-3.12.13+${PYTHON_BUILD_TAG}-${PLATFORM}-install_only.tar.gz"

echo "🚀 Starting AppImage Build Process..."

# 1. Clean and Create Build Directory
BUILD_ROOT="$(pwd)/AppImageBuild"
DOWNLOAD_CACHE="$(pwd)/.build_cache"
APP_DIR="${BUILD_ROOT}/AppDir"

mkdir -p "${DOWNLOAD_CACHE}"
rm -rf "${BUILD_ROOT}"
mkdir -p "${APP_DIR}/usr"

# 2. Download AppImageTool
echo "📥 Checking appimagetool..."
if [ ! -f "${DOWNLOAD_CACHE}/appimagetool" ]; then
    wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage -O "${DOWNLOAD_CACHE}/appimagetool"
    chmod +x "${DOWNLOAD_CACHE}/appimagetool"
fi
cp "${DOWNLOAD_CACHE}/appimagetool" "${BUILD_ROOT}/appimagetool"

# 3. Download Portable Python
echo "📥 Checking portable Python..."
if [ ! -f "${DOWNLOAD_CACHE}/python.tar.gz" ]; then
    wget -q "${PYTHON_URL}" -O "${DOWNLOAD_CACHE}/python.tar.gz"
fi
tar -xzf "${DOWNLOAD_CACHE}/python.tar.gz" -C "${APP_DIR}/usr" --strip-components=1

# 4. Install Dependencies
echo "📦 Installing Python dependencies into AppDir..."
"${APP_DIR}/usr/bin/python3" -m pip install --upgrade pip
"${APP_DIR}/usr/bin/python3" -m pip install -r requirements.txt

# 5. Copy Application Code
echo "📂 Copying application code..."
cp -r vivid_gui "${APP_DIR}/usr/"
cp icon.png "${APP_DIR}/vividpm.png"

# 6. Create AppRun script
echo "📝 Creating AppRun..."
cat <<EOF > "${APP_DIR}/AppRun"
#!/bin/bash
HERE="\$(dirname "\$(readlink -f "\${0}")")"
export PATH="\${HERE}/usr/bin:\${PATH}"
export LD_LIBRARY_PATH="\${HERE}/usr/lib:\${LD_LIBRARY_PATH}"
export PYTHONPATH="\${HERE}/usr/vivid_gui:\${PYTHONPATH}"

exec "\${HERE}/usr/bin/python3" -m vivid_gui.main "\$@"
EOF
chmod +x "${APP_DIR}/AppRun"

# 7. Create Desktop File
echo "📝 Creating Desktop file..."
cat <<EOF > "${APP_DIR}/vividpm.desktop"
[Desktop Entry]
Name=Vivid Package Manager
Exec=vividpm
Icon=vividpm
Type=Application
Categories=Utility;System;
Comment=The ultimate multi-platform package manager
Terminal=false
EOF

# 8. Create Symlinks (standard AppDir requirements)
ln -s vividpm.png "${APP_DIR}/.DirIcon"

# 9. Build the AppImage
echo "🔨 Bundling into AppImage..."
export ARCH=x86_64
"${BUILD_ROOT}/appimagetool" "${APP_DIR}" "${BUILD_ROOT}/${APP_NAME}-x86_64.AppImage"

# 10. Final Cleanup
mv "${BUILD_ROOT}/${APP_NAME}-x86_64.AppImage" .
echo "✨ DONE! Created ${APP_NAME}-x86_64.AppImage"
