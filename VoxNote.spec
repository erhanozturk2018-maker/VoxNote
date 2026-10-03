# PyInstaller build description for VoxNote.
#
#     pip install pyinstaller
#     pyinstaller --noconfirm --clean VoxNote.spec
#
# The result is the folder dist/VoxNote with VoxNote.exe inside. See
# docs/RELEASE.md for the complete release procedure.
#
# The NVIDIA runtime libraries are added when requirements-gpu.txt is
# installed in the build environment; otherwise a CPU-only bundle is built.

import glob
import os
import site

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

datas = [("assets", "assets")]
binaries = []
hiddenimports = collect_submodules("app.i18n.locales")

# Native libraries and data files that PyInstaller cannot discover by itself.
for package in ("ctranslate2", "onnxruntime", "faster_whisper"):
    package_datas, package_binaries, package_imports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_imports

for package in ("_sounddevice_data", "reportlab", "docx"):
    datas += collect_data_files(package)

# cuBLAS / cuDNN from the nvidia-* wheels, kept in nvidia/<package>/bin so
# that app.transcriber.register_nvidia_libraries finds them.
gpu_libraries = 0
for site_dir in site.getsitepackages():
    for dll in glob.glob(os.path.join(site_dir, "nvidia", "*", "bin", "*.dll")):
        package = os.path.basename(os.path.dirname(os.path.dirname(dll)))
        binaries.append((dll, os.path.join("nvidia", package, "bin")))
        gpu_libraries += 1
print(f"VoxNote.spec: bundling {gpu_libraries} NVIDIA runtime libraries")

excludes = [
    "tkinter",
    "pytest",
    "pypdf",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtMultimedia",
    "PySide6.Qt3DCore",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtPdf",
    "PySide6.QtOpenGL",
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VoxNote",
    icon="assets/voxnote.ico",
    console=False,
    upx=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    upx=False,
    name="VoxNote",
)
