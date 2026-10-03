# Preparing a Release

This document describes how to turn VoxNote into a distributable Windows
application, and what still has to be done before it should be offered to the
public.

> **Status.** For VoxNote 0.2.0 the executable and the installer were built
> and tried on the development computer only (see [Status](#status)). They are
> **not code-signed** and have not been tested on any other computer.

- [Status](#status)
- [Release readiness](#release-readiness)
- [Versioning](#versioning)
- [Release checklist](#release-checklist)
- [Building the release](#building-the-release)
- [GPU libraries in a packaged build](#gpu-libraries-in-a-packaged-build)
- [Model distribution and cache strategy](#model-distribution-and-cache-strategy)
- [Application icon](#application-icon)
- [Code signing](#code-signing)
- [Installer](#installer)
- [Clean-machine testing](#clean-machine-testing)
- [Licenses of bundled components](#licenses-of-bundled-components)

## Status

What was actually done for version 0.2.0, on one computer (Windows 11, NVIDIA
RTX 3060 Laptop GPU, Smart App Control switched on):

| Step | Result |
| --- | --- |
| `pyinstaller VoxNote.spec` | Built `dist\VoxNote` (about 2.4 GB including the NVIDIA libraries) |
| Start `dist\VoxNote\VoxNote.exe` | Window opened, the model loaded on the GPU, the log was written, the Silero VAD model was found |
| Compile `installer\VoxNote.iss` with Inno Setup 6.7 | Built `VoxNote-Setup-0.2.0.exe` (about 1.1 GB) in under two minutes |
| Silent installation into a test folder | Succeeded; Start menu and desktop shortcuts were created |
| Start the installed copy | Worked as above and closed with exit code 0 |
| Run the uninstaller | **Blocked by Smart App Control**, because `unins000.exe` is unsigned. The test installation had to be removed by hand. |

Not done: recording with the packaged build, a normal (interactive) run of
the wizard, installation on a second computer, and any test on Windows 10 or
without an NVIDIA card.

## Release readiness

Running locally on the developer's computer does not make an application
ready for worldwide distribution. Open items:

| Area | Remaining work | Priority |
| --- | --- | --- |
| Code signing | Sign the executable, the installer and the uninstaller. Without a signature, Smart App Control blocked the uninstaller on the development computer, and SmartScreen warns about the download | Required |
| Packaged-build testing | Run the manual checklist with the installed application, not only from source | Required |
| Clean-machine tests | Windows 10 and 11, with and without NVIDIA GPU, without Python installed | Required |
| Hardware coverage | Other GPUs (older GTX, RTX 40/50 series), CPU-only machines, different microphones and audio drivers | Required |
| Real-speech testing | Complete the manual checklist in [TESTING.md](TESTING.md) with several speakers and languages | Required |
| License review | Confirm obligations of all bundled components, in particular PySide6 (LGPL) | Required |
| Translations | Review of the Turkish, German, French, Italian and Russian texts by native speakers | Recommended |
| Accessibility | Screen-reader and high-contrast testing | Recommended |
| Installer | Test the interactive wizard, upgrading over an older version, and uninstalling | Required |
| Installer size | Offer a CPU-only installer without the 1.5 GB of NVIDIA libraries | Recommended |
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

The installer takes its version from `APP_VERSION` when it is built with
`tools\build_release.ps1`.

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

## Building the release

One script does everything:

```powershell
.\.venv\Scripts\Activate.ps1
pip install pyinstaller
.\tools\build_release.ps1
```

It runs the tests, regenerates the icon and installer artwork, builds the
application folder with PyInstaller and, if Inno Setup 6 is installed,
compiles the installer. `-SkipTests` and `-SkipInstaller` leave out a step.

| Output | Content |
| --- | --- |
| `dist\VoxNote\VoxNote.exe` | The application with its files in `dist\VoxNote\_internal`. The folder can be copied or zipped as a portable version. |
| `dist\installer\VoxNote-Setup-<version>.exe` | The installer |

Inno Setup can be installed with:

```powershell
winget install -e --id JRSoftware.InnoSetup
```

### The PyInstaller part

[PyInstaller](https://pyinstaller.org/) bundles the Python interpreter, the
packages and the application into a folder that runs without a Python
installation. The build is described in `VoxNote.spec`:

```powershell
pyinstaller --noconfirm --clean VoxNote.spec
```

What the spec file takes care of:

| Item | Reason |
| --- | --- |
| One-folder mode, no console window | A one-file build would unpack gigabytes to a temporary folder on every start. |
| `assets` | Icon and interface images, found through `app/resources.py` (`sys._MEIPASS`). |
| `collect_all("faster_whisper")` | Includes the Silero VAD model file that `app/vad_processor.py` loads from the package folder. Without it the less accurate energy-based detector is used and the log says so. |
| `collect_all("ctranslate2")`, `collect_all("onnxruntime")` | Native inference libraries and their DLLs. |
| `_sounddevice_data` | The PortAudio DLL. |
| `reportlab`, `docx` data files | Resource files and the default Word template. |
| `collect_submodules("app.i18n.locales")` | The interface translations are imported dynamically and would otherwise be missing. |
| `nvidia/*/bin/*.dll` | The cuBLAS, cuDNN and NVRTC libraries, when `requirements-gpu.txt` is installed in the build environment. |
| Excluded Qt modules | Unused parts of Qt (WebEngine, QML, 3D, …) are left out. |

For a release, build from a fresh virtual environment so the bundle contains
only what the application needs, and pin the dependency versions that were
tested.

## GPU libraries in a packaged build

Decide between two variants:

`VoxNote.spec` decides this automatically from what is installed in the
build environment.

**A. CPU-only bundle (small).** Build from an environment without
`requirements-gpu.txt`. On a computer with an NVIDIA GPU, VoxNote uses the
GPU only if cuBLAS and cuDNN are available through a system-wide CUDA
installation; otherwise it falls back to the CPU and says so.

**B. GPU-enabled bundle (about 1.5 GB larger).** Install
`requirements-gpu.txt` into the build environment. The spec file then copies
the DLLs into `nvidia\<package>\bin` inside the bundle, which is where
`register_nvidia_libraries` (`app/transcriber.py`) looks for them. This is
the variant that was built and tried for 0.2.0.

The same bundle still runs on computers without an NVIDIA GPU.

Offering both variants as separate downloads keeps the common download small.
Redistribution of the NVIDIA libraries is subject to NVIDIA's license terms;
read them before publishing variant B.

## Model distribution and cache strategy

The speech models (0.5 to 1.6 GB each) are not part of the repository or of
the installer.
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
  `assets/voxnote.png` (256 × 256) and `assets/voxnote.ico`.
- At runtime, `main.py` sets it as the window icon via `app/resources.py`.
- For the executable, `VoxNote.spec` embeds it (`icon="assets/voxnote.ico"`);
  the installer uses it as `SetupIconFile`.
- Windows displays icons at several sizes. The `.ico` contains nine images
  from 16 to 256 pixels, each rendered from the vector drawing rather than
  scaled down, with thicker strokes in the small sizes.
- The same script draws the two pictures of the setup wizard.
- To replace the artwork, change `draw()` in `tools/make_icon.py` or put your
  own `voxnote.ico` and `voxnote.png` into `assets`.

## Code signing

Unsigned executables are a real obstacle on current Windows versions:

- **Smart App Control** (Windows 11) blocks unsigned programs and libraries
  without established reputation. Its decisions are made per file: on the
  development computer it allowed the unsigned installer and `VoxNote.exe`
  but blocked the unsigned uninstaller. During development this even
  affected an unsigned library inside the Python environment
  (see [TROUBLESHOOTING.md](TROUBLESHOOTING.md#windows-blocked-the-speech-recognition-engine)).
- **SmartScreen** shows a warning for downloads without reputation.
- Antivirus products are more suspicious of unsigned PyInstaller bundles.

For a public release, sign `VoxNote.exe` and the installer with a code
signing certificate, using `signtool` from the Windows SDK:

```powershell
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /a dist\VoxNote\VoxNote.exe
```

Inno Setup can sign the installer and the uninstaller itself during
compilation (`SignTool=` and `SignedUninstaller=yes` in the `[Setup]`
section), which is what fixes the blocked uninstaller.

Third-party DLLs inside the bundle (CTranslate2, onnxruntime, PortAudio)
keep their own signature status. Test the signed build on a computer with
Smart App Control switched on.

## Installer

The installer is defined in `installer/VoxNote.iss` for
[Inno Setup 6](https://jrsoftware.org/isinfo.php).

| Property | Value |
| --- | --- |
| Scope | Current user only (`PrivilegesRequired=lowest`); no administrator rights |
| Default location | `%LOCALAPPDATA%\Programs\VoxNote` |
| Shortcuts | Start menu entry; desktop shortcut (a ticked option in the wizard) |
| Wizard languages | English, Turkish, German, French, Italian, Russian |
| Artwork | `assets/installer-side.bmp`, `assets/installer-small.bmp` and `assets/voxnote.ico`, all generated by `tools/make_icon.py` |
| License page | Shows `LICENSE` |
| After installation | Offers to start VoxNote |
| Uninstall | Removes the program files. Settings, transcripts, logs and downloaded models are kept. |
| Updates | The fixed `AppId` makes a newer installer replace the existing installation. |
| Compression | LZMA2; the speech model is not included and is downloaded on first start |

Compile it on its own with:

```powershell
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" /DAppVersion=0.2.0 installer\VoxNote.iss
```

Useful command-line options of the finished installer:

```powershell
VoxNote-Setup-0.2.0.exe /SILENT
VoxNote-Setup-0.2.0.exe /VERYSILENT /TASKS=""
```

The second form installs without any window and without the desktop
shortcut. Note that `/NOICONS` only suppresses the Start menu folder question
of the wizard; shortcuts are controlled through `/TASKS`.

**Known problem on computers with Smart App Control:** the uninstaller that
Inno Setup generates (`unins000.exe`) is unsigned and was blocked on the
development computer. Until the build is signed, VoxNote has to be removed
by hand there; see
[TROUBLESHOOTING.md](TROUBLESHOOTING.md#the-uninstaller-is-blocked).

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
3. Check the device shown in the status bar and in Settings › Recognition.
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
