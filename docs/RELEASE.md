# Preparing a Release

This document describes how to turn VoxNote into a distributable Windows
application, and what still has to be done before it should be offered to the
public.

> **Status.** VoxNote 0.1.0 runs from source. **No packaged build has been
> produced or tested yet.** The PyInstaller workflow below is a documented
> starting point, not a verified recipe. Expect to adjust it during the first
> real build.

- [Release readiness](#release-readiness)
- [Versioning](#versioning)
- [Release checklist](#release-checklist)
- [Building with PyInstaller](#building-with-pyinstaller)
- [GPU libraries in a packaged build](#gpu-libraries-in-a-packaged-build)
- [Model distribution and cache strategy](#model-distribution-and-cache-strategy)
- [Application icon](#application-icon)
- [Code signing](#code-signing)
- [Installer](#installer)
- [Clean-machine testing](#clean-machine-testing)
- [Licenses of bundled components](#licenses-of-bundled-components)

## Release readiness

Running locally on the developer's computer does not make an application
ready for worldwide distribution. Open items:

| Area | Remaining work | Priority |
| --- | --- | --- |
| Packaging | Produce and test a PyInstaller build | Required |
| Code signing | Sign the executable; unsigned builds are blocked by Smart App Control and warned about by SmartScreen | Required |
| Clean-machine tests | Windows 10 and 11, with and without NVIDIA GPU, without Python installed | Required |
| Hardware coverage | Other GPUs (older GTX, RTX 40/50 series), CPU-only machines, different microphones and audio drivers | Required |
| Real-speech testing | Complete the manual checklist in [TESTING.md](TESTING.md) with several speakers and languages | Required |
| License review | Confirm obligations of all bundled components, in particular PySide6 (LGPL) | Required |
| Translations | Review of the Turkish, German, French, Italian and Russian texts by native speakers | Recommended |
| Accessibility | Screen-reader and high-contrast testing | Recommended |
| Installer | Start menu entry, uninstaller, upgrade behaviour | Recommended |
| Continuous integration | Run the test suite automatically on every change | Recommended |
| Update strategy | Decide how users learn about new versions (the application makes no network requests by design) | Recommended |
| Long sessions | Verify memory use and stability over sessions of an hour or more | Recommended |
| Documentation | Replace rendered screenshots with screenshots of real sessions; add a change log | Recommended |

## Versioning

VoxNote uses [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`.

- While the version is `0.x`, anything may change between minor versions.
- From `1.0.0` on: `MAJOR` for incompatible changes (including a new JSON
  export schema version or a settings format that older versions cannot
  read), `MINOR` for new features, `PATCH` for fixes.

The version is stored in two places that must be changed together:

| File | Field |
| --- | --- |
| `app/__init__.py` | `APP_VERSION` (shown in the window and written into JSON exports) |
| `pyproject.toml` | `version` |

Independent version numbers:

- `JSON_SCHEMA_VERSION` in `app/exporters/json_exporter.py`
  (see [EXPORT_FORMATS.md](EXPORT_FORMATS.md#versioning-policy)),
- `SETTINGS_SCHEMA_VERSION` in `app/settings_manager.py`.

Tag releases in Git as `v0.1.0`, `v0.2.0`, and so on.

## Release checklist

1. All automated tests pass: `python -m pytest`.
2. The manual checklist in [TESTING.md](TESTING.md) has been completed on the
   release build, not only from source.
3. Version numbers updated; change log written.
4. Screenshots regenerated if the interface changed:
   `python tools/make_screenshots.py`.
5. Dependencies pinned to the exact versions that were tested
   (`pip freeze > requirements-lock.txt`) and the build made from that file.
6. Build created in a fresh virtual environment.
7. Build signed.
8. Build tested on clean machines.
9. Git tag created and release notes published.

## Building with PyInstaller

[PyInstaller](https://pyinstaller.org/) bundles the Python interpreter, the
packages and the application into a folder that runs without a Python
installation.

### Prepare a clean build environment

```powershell
py -3.11 -m venv .venv-build
.\.venv-build\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
```

Build from a fresh environment so that the bundle contains only what the
application needs.

### Build

Use the one-folder mode. A one-file build unpacks hundreds of megabytes to a
temporary folder on every start, which is slow and more likely to trigger
antivirus software.

```powershell
pyinstaller --noconfirm --clean --windowed `
  --name VoxNote `
  --icon assets\voxnote.ico `
  --add-data "assets;assets" `
  --collect-data faster_whisper `
  --collect-all ctranslate2 `
  --collect-all onnxruntime `
  --collect-binaries sounddevice `
  --collect-data _sounddevice_data `
  --collect-data reportlab `
  --collect-data docx `
  main.py
```

The result is `dist\VoxNote\VoxNote.exe` with its supporting files in
`dist\VoxNote\_internal`.

What the options are for:

| Option | Reason |
| --- | --- |
| `--windowed` | No console window. |
| `--add-data "assets;assets"` | Icon and interface images, found through `app/resources.py` (`sys._MEIPASS`). |
| `--collect-data faster_whisper` | The Silero VAD model file (`assets/silero_vad_*.onnx`), which `app/vad_processor.py` loads from the package folder. Without it the less accurate energy-based detector is used. |
| `--collect-all ctranslate2` | The native inference library and its DLLs. |
| `--collect-all onnxruntime` | Runtime for the VAD model. |
| `--collect-binaries sounddevice`, `--collect-data _sounddevice_data` | The PortAudio DLL. |
| `--collect-data reportlab`, `--collect-data docx` | Resource files and the default Word template. |

Things to verify in the first build (none of this has been checked yet):

- The interface translations are imported dynamically
  (`importlib.import_module` in `app/i18n/__init__.py`). If a language is
  missing from the build, add
  `--hidden-import app.i18n.locales.tr` (and likewise for `de`, `fr`, `it`,
  `ru`, `en`), or `--collect-submodules app.i18n.locales`.
- The log file reports
  `Silero VAD unavailable, using the energy-based fallback` if the VAD model
  was not bundled.
- PDF, DOCX and every other export format work.
- Start-up time and the size of `dist\VoxNote`.
- Excluding unused Qt modules (`--exclude-module PySide6.QtWebEngineCore`,
  `PySide6.QtQuick`, `PySide6.Qt3DCore`, …) reduces the size considerably.

Once the options are settled, keep the generated `VoxNote.spec` in the
repository and build with `pyinstaller VoxNote.spec`.

## GPU libraries in a packaged build

Decide between two variants:

**A. CPU-only bundle (small).** Build from an environment without
`requirements-gpu.txt`. On a computer with an NVIDIA GPU, VoxNote uses the
GPU only if cuBLAS and cuDNN are available through a system-wide CUDA
installation; otherwise it falls back to the CPU and says so.

**B. GPU-enabled bundle (about 1.5 GB larger).** Install
`requirements-gpu.txt` into the build environment and add the DLLs to the
bundle so that they end up in `nvidia\<package>\bin`, which is where
`register_nvidia_libraries` (`app/transcriber.py`) looks for them:

```powershell
  --add-binary ".venv-build\Lib\site-packages\nvidia\cublas\bin\*.dll;nvidia\cublas\bin" `
  --add-binary ".venv-build\Lib\site-packages\nvidia\cudnn\bin\*.dll;nvidia\cudnn\bin" `
  --add-binary ".venv-build\Lib\site-packages\nvidia\cuda_nvrtc\bin\*.dll;nvidia\cuda_nvrtc\bin" `
```

The same bundle still runs on computers without an NVIDIA GPU.

Offering both variants as separate downloads keeps the common download small.
Redistribution of the NVIDIA libraries is subject to NVIDIA's license terms;
read them before publishing variant B.

## Model distribution and cache strategy

The Whisper `small` model (about 0.5 GB) is not part of the repository.
Options for a release:

| Strategy | Download size | First start | Notes |
| --- | --- | --- | --- |
| **Download on first start** (current behaviour) | smallest | needs internet once | Model lives in the Hugging Face cache and is shared with other tools. |
| **Bundle the model** | +0.5 GB | works offline immediately | Suitable for offline installers. Requires a small code change, see below. |
| **Separate model package** | small + optional 0.5 GB | user copies the model folder | For restricted networks; already possible by copying the cache folder (see [INSTALLATION.md](INSTALLATION.md#10-first-start-model-download-and-cache)). |

To bundle the model, ship the model folder (the directory containing
`model.bin`, `config.json`, `tokenizer.json` and `vocabulary.txt`) with the
application and make `Transcriber.cached_model_path` in `app/transcriber.py`
return that folder when it exists. `WhisperModel` accepts a local directory
path, which is already how the model is loaded.

Whichever strategy is used:

- never download the model again when it is present (the current code checks
  the local cache first, without network access),
- keep the model outside the installation folder if the application may be
  installed into a read-only location such as `Program Files`,
- state the model's license (MIT) in the release notes.

## Application icon

- Source: `tools/make_icon.py` draws the icon with Qt and writes
  `assets/voxnote.png` and `assets/voxnote.ico` (256 × 256).
- At runtime, `main.py` sets it as the window icon via `app/resources.py`.
- For the executable, PyInstaller embeds it with `--icon assets\voxnote.ico`.
- Windows displays icons at several sizes (16, 24, 32, 48, 256 pixels). The
  generated `.ico` currently contains only the 256-pixel image, which Windows
  scales down. For a release, create a multi-size `.ico` with hand-tuned
  small sizes.
- To replace the artwork, change `draw()` in `tools/make_icon.py` or put your
  own `voxnote.ico` and `voxnote.png` into `assets`.

## Code signing

Unsigned executables are a real obstacle on current Windows versions:

- **Smart App Control** (Windows 11) blocks unsigned programs and libraries
  without established reputation outright. During development this even
  affected an unsigned library inside the Python environment
  (see [TROUBLESHOOTING.md](TROUBLESHOOTING.md#windows-blocked-the-speech-recognition-engine)).
- **SmartScreen** shows a warning for downloads without reputation.
- Antivirus products are more suspicious of unsigned PyInstaller bundles.

For a public release, sign `VoxNote.exe` and the installer with a code
signing certificate, using `signtool` from the Windows SDK:

```powershell
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /a dist\VoxNote\VoxNote.exe
```

Third-party DLLs inside the bundle (CTranslate2, onnxruntime, PortAudio)
keep their own signature status. Test the signed build on a computer with
Smart App Control switched on.

## Installer

A folder is not a convenient download. Wrap `dist\VoxNote` with an installer
tool such as [Inno Setup](https://jrsoftware.org/isinfo.php) or
[WiX](https://wixtoolset.org/), or publish it as a ZIP archive for a portable
version (`VOXNOTE_HOME` keeps all data next to the application; see
[INSTALLATION.md](INSTALLATION.md#where-voxnote-stores-its-data)).

The installer should:

- install per user without requiring administrator rights,
- create a Start menu entry,
- register an uninstaller,
- leave the user's settings, transcripts and model cache untouched on
  upgrade, and ask before removing them on uninstall.

## Clean-machine testing

Test the packaged build on computers (or virtual machines) that have never
had Python, the project or the model on them.

Matrix:

| | Windows 10 | Windows 11 |
| --- | --- | --- |
| No NVIDIA GPU | | |
| NVIDIA GPU, current driver | | |
| NVIDIA GPU, old driver (CUDA 12 not supported) | | |
| Smart App Control on | n/a | |
| Standard user without administrator rights | | |
| No internet on first start | | |

For each cell:

1. Install or unpack the build and start it.
2. First start: model download with progress; then retry with the network
   disconnected to see the error message and the **Try Again** button.
3. Check the device shown in the status bar and in Settings › System.
4. Run the recording checklist from [TESTING.md](TESTING.md).
5. Export to all five formats and open each file.
6. Disconnect the network and repeat a recording.
7. Close and restart: settings must persist.
8. Check `%LOCALAPPDATA%\VoxNote\logs\voxnote.log` for errors.
9. Uninstall and check what remains.

Record the results; do not claim compatibility for a configuration that was
not tested.

## Licenses of bundled components

A packaged build redistributes third-party software. Before publishing,
review the current license of each component and include the required
notices.

| Component | License (verify before release) | Note |
| --- | --- | --- |
| Python | PSF License | |
| PySide6 / Qt | LGPL v3 (or commercial) | The LGPL requires, among other things, that users can replace the Qt libraries. The one-folder build keeps them as separate DLLs. Include the license text and a notice. |
| faster-whisper | MIT | |
| CTranslate2 | MIT | |
| Whisper model weights (`Systran/faster-whisper-small`) | MIT | Converted from OpenAI's Whisper model. |
| Silero VAD | MIT | Shipped inside faster-whisper. |
| onnxruntime | MIT | |
| sounddevice / PortAudio | MIT | |
| NumPy | BSD | |
| python-docx | MIT | |
| ReportLab (open-source edition) | BSD | |
| NVIDIA cuBLAS / cuDNN (variant B only) | NVIDIA proprietary license | Check the redistribution terms. |
| System fonts embedded in exported PDFs | Font licenses of the user's system | Fonts are embedded as subsets in the user's own documents; the application does not ship fonts. |

This table is a starting point for the review, not legal advice.
