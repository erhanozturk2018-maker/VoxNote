# Installation (Windows)

There are two ways to install VoxNote:

- **Installer.** Run `VoxNote-Setup-<version>.exe` and follow the wizard. It
  installs for the current user (no administrator rights), offers a desktop
  shortcut and contains everything except the speech model, which is
  downloaded on first start. The installer is not code-signed; see
  [RELEASE.md](RELEASE.md#code-signing) for what that means. To remove VoxNote
  later, use **Windows Settings › Apps › Installed apps**.
- **From source**, described in the rest of this guide. All commands are for
  **PowerShell** on Windows 10 or Windows 11 (64-bit).

- [1. Install Python](#1-install-python)
- [2. Open PowerShell](#2-open-powershell)
- [3. Get the project and go to its folder](#3-get-the-project-and-go-to-its-folder)
- [4. Create a virtual environment](#4-create-a-virtual-environment)
- [5. Activate the environment](#5-activate-the-environment)
- [6. Install the dependencies](#6-install-the-dependencies)
- [7. Optional: NVIDIA GPU acceleration](#7-optional-nvidia-gpu-acceleration)
- [8. CPU mode](#8-cpu-mode)
- [9. Start the application](#9-start-the-application)
- [10. First start: model download and cache](#10-first-start-model-download-and-cache)
- [Updating](#updating)
- [Uninstalling](#uninstalling)
- [Where VoxNote stores its data](#where-voxnote-stores-its-data)

## 1. Install Python

VoxNote is developed and tested with **Python 3.11**. Python 3.10 and 3.12
are expected to work but have not been tested.

1. Download the "Windows installer (64-bit)" for Python 3.11 from
   <https://www.python.org/downloads/windows/>.
2. Run the installer. On the first page, tick **"Add python.exe to PATH"**,
   then choose **Install Now**.

Check the installation:

```powershell
py -3.11 --version
```

The command prints something like `Python 3.11.9`.

## 2. Open PowerShell

Press the Windows key, type `PowerShell`, and open **Windows PowerShell** or
**PowerShell 7**. Administrator rights are not required.

## 3. Get the project and go to its folder

With Git:

```powershell
git clone https://github.com/erhanozturk2018-maker/VoxNote.git
cd VoxNote
```

Without Git, download the project as a ZIP file from the repository page,
extract it, and change into the extracted folder, for example:

```powershell
cd "$HOME\Downloads\VoxNote-main"
```

All following commands are run from this folder.

## 4. Create a virtual environment

A virtual environment keeps VoxNote's packages separate from other Python
programs on the computer.

```powershell
py -3.11 -m venv .venv
```

## 5. Activate the environment

```powershell
.\.venv\Scripts\Activate.ps1
```

The prompt now starts with `(.venv)`. You have to activate the environment
again every time you open a new PowerShell window.

If PowerShell refuses with a message about the *execution policy*, allow
locally created scripts for your user account and try again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Alternatively, skip activation and call the environment's Python directly by
writing `.\.venv\Scripts\python.exe` wherever this guide says `python`.

## 6. Install the dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

This installs:

| Package | Purpose |
| --- | --- |
| PySide6 | Desktop interface (Qt) |
| faster-whisper | Speech recognition |
| ctranslate2 | Inference engine used by faster-whisper |
| onnxruntime | Runs the voice activity detection model (installed by faster-whisper) |
| sounddevice | Microphone access (includes the PortAudio library) |
| numpy | Audio buffers |
| python-docx | Word export |
| reportlab | PDF export |

The download is a few hundred megabytes. After this step VoxNote works in
CPU mode.

## 7. Optional: NVIDIA GPU acceleration

Recognition is considerably faster on a supported NVIDIA graphics card. If
you do not have one, skip this section; VoxNote uses the processor instead.

### Requirements

The engine behind faster-whisper is CTranslate2. From version 4.5 on, its
GPU support needs:

| Requirement | Where it comes from |
| --- | --- |
| An NVIDIA graphics card that supports CUDA 12 | Hardware |
| A current NVIDIA graphics driver | <https://www.nvidia.com/drivers> |
| cuBLAS for CUDA 12 | `nvidia-cublas-cu12` pip package |
| cuDNN 9 for CUDA 12 | `nvidia-cudnn-cu12` pip package |

**You do not need to install the CUDA Toolkit or cuDNN system-wide.** The two
pip packages contain the required runtime libraries, and VoxNote adds their
folders to the DLL search path when it starts
(`register_nvidia_libraries` in `app/transcriber.py`).

If the CUDA Toolkit 12 and cuDNN 9 are already installed system-wide and on
the `PATH`, they are used as well and the pip packages are not needed.

### Install

```powershell
pip install -r requirements-gpu.txt
```

The download is about 1.2 GB and needs roughly the same amount of disk space
again once installed.

### Verify

```powershell
python -c "import ctranslate2; print('CUDA devices:', ctranslate2.get_cuda_device_count()); print(ctranslate2.get_supported_compute_types('cuda'))"
```

A device count of `1` or more and a list containing `float16` mean the
graphics card is visible. Whether inference really works is checked by
VoxNote itself when it loads the model: it runs a short test and, if the GPU
fails, falls back to the CPU and tells you why (Settings › Recognition,
below "Processing device").

After starting VoxNote, the status bar at the bottom right shows the device,
for example:

```
Model: large-v3-turbo · GPU (NVIDIA CUDA, float16)
```

## 8. CPU mode

Without a usable NVIDIA GPU, VoxNote runs the model on the processor with
8-bit integer weights (`int8`). This needs no additional installation.

- It is slower than GPU mode. On a slow processor, recognition can fall
  behind long stretches of continuous speech; the transcript then appears with
  a delay and is completed after you press Stop.
- The status bar shows `Model: large-v3-turbo · CPU (int8)`.
- On a computer without a graphics card, consider the Small model
  (**Settings › Recognition › Speech model**); the large model is slow on a
  processor.
- You can force CPU mode in **Settings › Recognition › Processing device**,
  for example when the graphics card is busy with another program.

## 9. Start the application

With the environment activated:

```powershell
python main.py
```

Or without activating it:

```powershell
.\.venv\Scripts\python.exe main.py
```

To start VoxNote without a console window, use `pythonw`:

```powershell
.\.venv\Scripts\pythonw.exe main.py
```

## 10. First start: model download and cache

The first time VoxNote starts, it downloads the selected Whisper model. The
default is Large v3 Turbo; Medium and Small can be chosen in
**Settings › Recognition**.

- **An internet connection is required for this one download** (about
  1.6 GB for Large v3 Turbo, 1.5 GB for Medium, 0.5 GB for Small). The status bar shows "Downloading speech model…" and the amount
  received so far. Recording is unavailable until the model is ready.
- The models come from the Hugging Face Hub repositories
  `mobiuslabsgmbh/faster-whisper-large-v3-turbo`,
  `Systran/faster-whisper-medium` and `Systran/faster-whisper-small`.
- **The model is stored locally** in the Hugging Face cache, by default:

  ```
  C:\Users\<your name>\.cache\huggingface\hub\models--mobiuslabsgmbh--faster-whisper-large-v3-turbo
  ```

  The location follows the standard Hugging Face environment variables
  (`HF_HOME`, `HF_HUB_CACHE`) if you have set them. **Settings › Recognition ›
  Open Model Folder** opens the actual location.
- **Later starts reuse the cached model** and do not contact the network.
  VoxNote first looks for the model locally and only attempts a download when
  it is missing.
- **Audio is never uploaded.** Recognition happens on your computer.
- If the download fails (no connection, proxy, full disk), VoxNote shows a
  message with a **Try Again** button. See
  [TROUBLESHOOTING.md](TROUBLESHOOTING.md#the-speech-model-cannot-be-downloaded).

To prepare a computer that will be used offline, start VoxNote once while it
is online, or copy the model's `models--…` folder from another computer into
the same cache location.

## Updating

```powershell
git pull
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Uninstalling

1. Delete the project folder (this also removes the virtual environment).
2. Delete VoxNote's own data folders if you no longer want them:

   ```powershell
   Remove-Item -Recurse "$env:APPDATA\VoxNote"
   Remove-Item -Recurse "$env:LOCALAPPDATA\VoxNote"
   ```

3. Optionally delete the cached model (shared with other programs that use
   the Hugging Face cache):

   ```powershell
   Remove-Item -Recurse "$HOME\.cache\huggingface\hub\models--mobiuslabsgmbh--faster-whisper-large-v3-turbo"
   ```

Your exported transcripts are in the save folder you chose (by default
`Documents\VoxNote`) and are not touched by these steps.

## Where VoxNote stores its data

| What | Location |
| --- | --- |
| Settings | `%APPDATA%\VoxNote\settings.json` |
| Log files | `%LOCALAPPDATA%\VoxNote\logs\voxnote.log` |
| Recovery journals of unsaved sessions | `%LOCALAPPDATA%\VoxNote\sessions\` |
| Raw audio (only if enabled in Settings) | `%LOCALAPPDATA%\VoxNote\audio\` |
| Speech model | Hugging Face cache (see above) |
| Transcripts | The save folder chosen in Settings; default `Documents\VoxNote` |

Setting the environment variable `VOXNOTE_HOME` to a folder moves settings,
logs, journals and audio into that folder, which is useful for a portable
installation.
