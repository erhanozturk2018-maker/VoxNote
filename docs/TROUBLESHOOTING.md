# Troubleshooting

- [Reading the log file](#reading-the-log-file)
- [Microphone problems](#microphone-problems)
- [Speech model problems](#speech-model-problems)
- [GPU and CUDA problems](#gpu-and-cuda-problems)
- [Recognition quality](#recognition-quality)
- [File export problems](#file-export-problems)
- [Installation and dependency problems](#installation-and-dependency-problems)
- [Installer problems](#installer-problems)
- [Application behaviour](#application-behaviour)
- [Reporting a problem](#reporting-a-problem)

## Reading the log file

VoxNote writes technical details to a log file. Messages in the application
are kept short on purpose; the log has the full error text.

- Location: `%LOCALAPPDATA%\VoxNote\logs\voxnote.log`
- Open the folder from **Settings › Recognition › Open Log Folder** or
  **Help › About**, or run:

  ```powershell
  notepad "$env:LOCALAPPDATA\VoxNote\logs\voxnote.log"
  ```

- The log never contains audio or transcript text.
- The file is limited to about 1 MB; three older files are kept as
  `voxnote.log.1` to `voxnote.log.3`.

Timing information is logged for every utterance and every session:

```
app.workers [transcribe] Segment 3: 4.10 s of audio recognised in 0.42 s (1 piece(s))
app.workers [transcribe] Session recognition: 12 segment(s), 61.3 s of speech in 7.9 s (real-time factor 0.13)
```

A real-time factor below 1 means recognition is faster than speech. (The
numbers above only illustrate the format; they are not measurements.)

## Microphone problems

### "No microphone was found"

- Connect a microphone and press the refresh button (the circular arrow next
  to the microphone list).
- Check **Windows Settings › System › Sound › Input**: the device must be
  listed and enabled.
- USB and Bluetooth devices can take a few seconds to appear; press the
  refresh button again.

### "The microphone could not be opened"

- **Microphone permission.** Open **Windows Settings › Privacy & security ›
  Microphone** and switch on both *Microphone access* and *Let desktop apps
  access your microphone*.
- **Exclusive use.** Close other programs that may hold the microphone
  exclusively (conferencing or recording software).
- **Device disappeared.** Press the refresh button and select the device
  again, or choose *System default microphone*.

### The level meter does not move / "The microphone delivers only silence"

- The wrong device is selected. Choose another one in the **Microphone** list.
- The microphone is muted by a hardware switch, a headset button or in the
  Windows sound settings.
- Windows blocks microphone access for desktop apps (see above). In that case
  Windows delivers pure silence rather than an error, which VoxNote detects
  after about three seconds.

### "The microphone stopped delivering audio, so recording was stopped"

The device was unplugged, switched off or lost its Bluetooth connection.
Everything spoken before that moment has been transcribed and saved.
Reconnect the device, press the refresh button and start a new recording.

### Nothing is transcribed although the meter moves

- Your voice may be too quiet for the speech detector. Move closer to the
  microphone or raise the input volume in the Windows sound settings.
- Lower **Settings › Recording › Speech sensitivity** (for example to 0.35).
- Enable **Keep the raw audio of each session**, record a short test and
  listen to the WAV file (**Open Audio Folder**) to hear what VoxNote
  receives. Switch the option off again afterwards.

### The first or last word is cut off

Increase **Lead-in** or **Lead-out** in **Settings › Recording** (for
example to 500 ms).

## Speech model problems

### The speech model cannot be downloaded

The model is downloaded from the Hugging Face Hub the first time VoxNote
starts.

- Check the internet connection and press **Try Again**.
- Behind a corporate proxy, set the proxy before starting VoxNote:

  ```powershell
  $env:HTTPS_PROXY = "http://proxy.example.com:8080"
  python main.py
  ```

- If `huggingface.co` is blocked on your network, download the model on
  another computer by starting VoxNote there once, then copy the folder
  `%USERPROFILE%\.cache\huggingface\hub\models--mobiuslabsgmbh--faster-whisper-large-v3-turbo`
  to the same location on the target computer.
- An interrupted download continues with the missing files on the next
  attempt.

### "There is not enough free disk space to download the speech model"

VoxNote requires the size of the model plus 0.5 GB (about 2 GB for the
default model) free on the drive that holds the Hugging Face
cache (normally `C:`). Free some space, or move the cache to another drive
by setting `HF_HOME` before starting:

```powershell
$env:HF_HOME = "D:\hf-cache"
python main.py
```

To make this permanent, define `HF_HOME` as a user environment variable in
Windows.

### "The speech model could not be loaded"

- The cached model may be damaged (for example by an interrupted copy).
  Delete the model folder and start VoxNote again to download it afresh:

  ```powershell
  Remove-Item -Recurse "$HOME\.cache\huggingface\hub\models--mobiuslabsgmbh--faster-whisper-large-v3-turbo"
  ```

- The computer may be out of memory. Close other programs.
- The log file contains the exact error.

### "Windows blocked the speech recognition engine"

Windows 11 **Smart App Control** (and company-managed *application control
policies*) block program files that are neither signed nor known to
Microsoft's reputation service. A freshly published version of CTranslate2,
the engine that runs the model, can be affected until it has built up
reputation. The log then contains:

```
ImportError: DLL load failed while importing _ext: An Application Control policy has blocked this file.
```

This is exactly what happened during development with CTranslate2 4.8.2;
version 4.7.1 loaded normally on the same computer, which is why
`requirements.txt` limits the version. The packaged application contains
4.7.1. What you can do:

1. Install the tested version:

   ```powershell
   pip install "ctranslate2==4.7.1"
   ```

2. If that version is blocked as well on your computer, check **Windows
   Security › App & browser control › Smart App Control**. Whether to change
   this Windows security setting is your decision, or your administrator's on
   a managed computer. VoxNote does not and cannot change it.

### "The speech recognition engine could not be started"

A required package is missing or broken. Reinstall the dependencies:

```powershell
pip install --force-reinstall -r requirements.txt
```

If the log mentions `VCRUNTIME140.dll` or `MSVCP140.dll`, install the
"Microsoft Visual C++ Redistributable (x64)" from Microsoft.

## GPU and CUDA problems

VoxNote never fails because of the graphics card: if the GPU cannot be used
it continues on the CPU. **Settings › Recognition** shows the device in use
and the reason below "Processing device".

### "…no compatible NVIDIA graphics card was found"

- The computer has no NVIDIA GPU, or the NVIDIA driver is not installed.
  Check with:

  ```powershell
  nvidia-smi
  ```

  If the command is not found, install the driver from
  <https://www.nvidia.com/drivers>.
- AMD and Intel graphics are not supported by the recognition engine; CPU
  mode is used.

### "…the graphics card could not be initialised. The NVIDIA libraries (cuBLAS, cuDNN) may be missing"

The GPU was found, but the runtime libraries could not be loaded. The log
shows a line such as
`Library cublas64_12.dll is not found or cannot be loaded`.

- Install the libraries into the same virtual environment:

  ```powershell
  pip install -r requirements-gpu.txt
  ```

- Make sure the versions match: CTranslate2 4.5 and newer need **CUDA 12**
  and **cuDNN 9**. `nvidia-cudnn-cu12` version 8 does not work with them.
- Update the NVIDIA driver; old drivers do not support CUDA 12.

### "…the graphics card ran out of memory"

Another program is using the video memory (a game, a browser with hardware
acceleration, another AI tool).

- Close such programs and restart VoxNote, or
- select **Processor (CPU)** in **Settings › Recognition › Processing
  device**, or
- choose a smaller model in **Settings › Recognition › Speech model**.

If the memory runs out in the middle of a session, VoxNote reloads the model
on the CPU, repeats the affected utterance and continues. You see the notice
"The graphics card could not be used any more…".

The Small and the Large v3 Turbo model ran on the 6 GB graphics card of the
development computer; Medium was not tried.
No exact memory figures are stated here because they have not been measured
systematically.

### Checking what CTranslate2 sees

```powershell
python -c "import ctranslate2; print(ctranslate2.__version__, ctranslate2.get_cuda_device_count(), ctranslate2.get_supported_compute_types('cuda'))"
```

## Recognition quality

### Words are wrong

In order of effect:

1. **Use the Large v3 Turbo model** (**Settings › Recognition › Speech
   model**). It is the default; Small and Medium are less accurate.
2. **Speak in sentences.** A single word on its own gives the model no
   context and is often written wrongly, whatever the model.
3. **Add names and special terms** to **Settings › Recognition › Names and
   special words**, separated by commas (for example `Gesi, Kayseri`). In the
   developer's test, the place name "Gesi" was written "Gizli" by the Small
   model and "Gezi" by the large one, and correctly by both once it was
   listed there.
4. **Use a headset** or a microphone close to your mouth, in a quiet room.

VoxNote does not check pronunciation. A word that is pronounced unclearly is
written as the nearest word the model knows.

### Something I said in another language was written in English or Turkish

Recognition is limited to the languages ticked in **Settings › Recognition ›
Spoken languages**. The main window shows this next to the detected
languages ("· limited to English, Turkish"). Anything said in a language
that is not ticked is forced into one of the ticked ones, which produces
wrong or translated text. Tick the additional language, or untick everything
to allow all languages.

### The wrong language is detected

- **Tick the languages you speak** in **Settings › Recognition › Spoken
  languages**. The model then only chooses between those, which removes
  stray detections such as Arabic, Swedish or Portuguese for short phrases.
- Very short utterances are the usual cause. Speak a full sentence.
- Pause when switching languages so each language gets its own utterance.
- A strong accent can make the model lean towards another language.

### Text appears although nobody spoke

VoxNote only sends audio to the recogniser when the speech detector fires,
and it drops results that the model itself marks as "no speech". If noise is
still transcribed (music, television or other voices are speech-like):

- raise **Speech sensitivity** to 0.6–0.75,
- raise **Shortest speech** to 400–500 ms,
- move the microphone away from the noise source.

### Sentences are split in the middle

Increase **Pause that ends a segment** (for example to 1200 ms).

### The transcript appears late

- In CPU mode recognition can take as long as the speech itself, or longer
  with the large model. Choose the Small model on computers without a
  supported graphics card.
- An utterance is recognised only when it ends. Lowering **Pause that ends a
  segment** makes utterances end sooner, so text appears earlier.

### "Speech recognition could not keep up, so recording was stopped"

More than 20 minutes of speech were waiting to be recognised. Recording is
stopped to limit memory use; everything captured is still transcribed. This
only happens on slow hardware with long continuous speech. Use GPU mode or
record in shorter sessions.

## File export problems

### "The save folder cannot be written to"

- Choose another folder with **Change…**, then press **Save**.
- Windows *Controlled folder access* (ransomware protection) can block
  writing to Documents. Either allow Python in **Windows Security › Virus &
  threat protection › Ransomware protection**, or choose a folder outside
  the protected locations.
- Network drives and removable drives may be disconnected.

### "The file could not be saved"

- The disk may be full.
- For **Save As…**: the target file may be open in another program (Word
  locks open documents). Close it or choose another name.
- The transcript stays in the window; use **Save** or **Save As…** again.

### "No font that supports all characters was found, so the PDF was not created"

PDF export embeds a TrueType font from the system. On Windows it uses Segoe
UI, Arial or Tahoma, and additional system fonts for Chinese, Japanese,
Korean and other scripts. If none can be loaded:

- choose another format, or
- point VoxNote at a font file that covers your language:

  ```powershell
  $env:VOXNOTE_PDF_FONT = "C:\Fonts\NotoSans-Regular.ttf"
  python main.py
  ```

  The file must be a TrueType font (`.ttf`); OpenType fonts with PostScript
  outlines (`.otf`) are not supported by the PDF library.

### Some characters in the PDF are boxes or in the wrong order

- Boxes: no installed font contains these characters. Install a font for the
  language or set `VOXNOTE_PDF_FONT`.
- Arabic, Hebrew and Indic scripts are not shaped correctly in PDF. This is a
  limitation of the PDF library. Use DOCX, Markdown, TXT or JSON.

### "The saved file is no longer at its location"

The file was moved, renamed or deleted after saving. Use **Save As…** to
write it again; the transcript is still in memory until you start the next
recording or close VoxNote.

## Installation and dependency problems

### `Activate.ps1 cannot be loaded because running scripts is disabled`

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Or call `.\.venv\Scripts\python.exe main.py` without activating.

### `py` or `python` is not recognised

Python is not installed or not on the `PATH`. Reinstall Python and tick
"Add python.exe to PATH".

### `pip install` fails with a build error

Usually the Python version is too new for one of the packages and no
pre-built package exists yet. Use Python 3.11.

### `ModuleNotFoundError` when starting

The virtual environment is not active or the dependencies were installed
into another Python. Activate `.venv` and run
`pip install -r requirements.txt` again.

### "Audio recording is not available on this computer"

The `sounddevice` package could not load its PortAudio library. Reinstall it:

```powershell
pip install --force-reinstall sounddevice
```

## Installer problems

### Windows warns about the installer or refuses to run it

`VoxNote-Setup-<version>.exe` is not code-signed. SmartScreen may show
"Windows protected your PC"; Smart App Control blocks it outright ("An
Application Control policy has blocked this file") and offers no way to run
it anyway. Whether to run an unsigned program is your decision where Windows
leaves you one. Alternatives:

- Run VoxNote from source ([INSTALLATION.md](INSTALLATION.md)); no unsigned
  program of ours is involved.
- If you have the project folder with its virtual environment, create
  shortcuts that start VoxNote through Python:
  `.\tools\install_local.ps1 -FromSource`
  (see [RELEASE.md](RELEASE.md#local-installation-without-the-installer)).
  Copying the built `VoxNote.exe` to another folder is not reliable: Smart
  App Control may block the copy even though the original runs.

The permanent fix is a signed release; the options are listed in
[RELEASE.md](RELEASE.md#distribution-without-security-warnings).

### The uninstaller is blocked

On a computer with Smart App Control switched on, removing VoxNote through
**Windows Settings › Apps** can fail with "An Application Control policy has
blocked this file", because the uninstaller is unsigned. Remove VoxNote by
hand instead:

1. Close VoxNote.
2. Delete the installation folder, by default
   `%LOCALAPPDATA%\Programs\VoxNote`.
3. Delete the desktop shortcut and the `VoxNote` folder in the Start menu
   (`%APPDATA%\Microsoft\Windows\Start Menu\Programs\VoxNote`).
4. The entry in the list of installed apps can be removed by deleting the
   registry key
   `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Uninstall\{6B0C2F4E-5C0A-4B55-9A77-3E1E1B0C7D21}_is1`.

Your settings, transcripts and downloaded models are not affected.

## Application behaviour

### "Start Recording" is disabled

Hover over the button: the tooltip gives the reason. Either the speech model
is still loading (see the status bar), it failed to load (a message with
**Try Again** is shown), or a session is still being processed.

### The settings were reset

If `settings.json` is damaged, VoxNote starts with the defaults and keeps the
damaged file as `settings.json.corrupt` in `%APPDATA%\VoxNote`.

### Resetting everything

Close VoxNote and delete its data folders:

```powershell
Remove-Item -Recurse "$env:APPDATA\VoxNote"
Remove-Item -Recurse "$env:LOCALAPPDATA\VoxNote"
```

This removes settings, logs, unsaved recovery data and retained audio. It
does not remove exported transcripts or the speech model.

## Reporting a problem

Include:

1. what you did and what happened,
2. the VoxNote version (shown next to the name in the main window),
3. Windows version, and graphics card if the problem concerns the GPU,
4. the relevant part of `voxnote.log`.

The log contains no transcript text, but it does contain folder paths, which
may include your Windows user name. Remove them if you prefer.
