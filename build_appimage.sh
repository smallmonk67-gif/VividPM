#!/bin/bash
set -e

# Configuration
APP_NAME="VividPM"
PYTHON_VERSION="3.12"
PLATFORM="x86_64-unknown-linux-gnu"
PYTHON_BUILD_TAG="20260510"
PYTHON_URL="https://github.com/astral-sh/python-build-standalone/releases/download/${PYTHON_BUILD_TAG}/cpython-3.12.13+${PYTHON_BUILD_TAG}-${PLATFORM}-install_only.tar.gz"

echo "🚀 Starting Corrected AppImage Build Process..."

# 1. Setup Build and Cache Directory
BUILD_ROOT="$(pwd)/AppImageBuild"
DOWNLOAD_CACHE="$(pwd)/.build_cache"
APP_DIR="${BUILD_ROOT}/AppDir"

mkdir -p "${DOWNLOAD_CACHE}"
rm -rf "${BUILD_ROOT}"
mkdir -p "${APP_DIR}/usr"

# 2. Download/Cache AppImageTool
if [ ! -f "${DOWNLOAD_CACHE}/appimagetool" ]; then
    echo "📥 Downloading appimagetool..."
    wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage -O "${DOWNLOAD_CACHE}/appimagetool"
    chmod +x "${DOWNLOAD_CACHE}/appimagetool"
fi
cp "${DOWNLOAD_CACHE}/appimagetool" "${BUILD_ROOT}/appimagetool"

# 3. Download/Cache Portable Python
if [ ! -f "${DOWNLOAD_CACHE}/python.tar.gz" ]; then
    echo "📥 Downloading portable Python..."
    wget -q "${PYTHON_URL}" -O "${DOWNLOAD_CACHE}/python.tar.gz"
fi
tar -xzf "${DOWNLOAD_CACHE}/python.tar.gz" -C "${APP_DIR}/usr" --strip-components=1

# 4. Install Dependencies
echo "📦 Installing Python dependencies..."
"${APP_DIR}/usr/bin/python3" -m pip install -r requirements.txt

# 5. Copy Application Code
echo "📂 Copying application code..."
cp -r vivid_gui "${APP_DIR}/usr/"
cp icon.png "${APP_DIR}/vividpm.png"

# 6. Create FIXED AppRun script
echo "📝 Creating FIXED AppRun..."
cat <<EOF > "${APP_DIR}/AppRun"
#!/bin/bash
HERE="\$(dirname "\$(readlink -f "\${0}")")"
export PATH="\${HERE}/usr/bin:\${PATH}"
export LD_LIBRARY_PATH="\${HERE}/usr/lib:\${LD_LIBRARY_PATH}"
# Point PYTHONPATH to the parent of the package
export PYTHONPATH="\${HERE}/usr:\${PYTHONPATH}"

exec "\${HERE}/usr/bin/python3" -m vivid_gui.main "\$@"
EOF
chmod +x "${APP_DIR}/AppRun"

# 7. Create Desktop File
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

# 8. Finalize AppDir
ln -s vividpm.png "${APP_DIR}/.DirIcon"

# 9. Build
echo "🔨 Bundling..."
export ARCH=x86_64
"${BUILD_ROOT}/appimagetool" "${APP_DIR}" "${BUILD_ROOT}/VividPM_Linux_x86_64_v2.0.0.Appimage"

# 10. Move to releases
mkdir -p releases
mv "${BUILD_ROOT}/VividPM_Linux_x86_64_v2.0.0.Appimage" releases/
echo "✨ FIXED! Created releases/VividPM_Linux_x86_64_v2.0.0.Appimage"
