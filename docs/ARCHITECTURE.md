# Architecture

This document explains how VoxNote is built and why. It is written for a
developer who is new to the code base.

- [Design goals](#design-goals)
- [Overview](#overview)
- [Components](#components)
- [State machine](#state-machine)
- [Threading](#threading)
- [Audio capture](#audio-capture)
- [Voice activity detection](#voice-activity-detection)
- [Buffering](#buffering)
- [Transcription](#transcription)
- [Language detection](#language-detection)
- [Export pipeline](#export-pipeline)
- [Crash recovery](#crash-recovery)
- [Settings persistence](#settings-persistence)
- [Interface and localisation](#interface-and-localisation)
- [Error handling and logging](#error-handling-and-logging)
- [Resource management](#resource-management)
- [Extending the application](#extending-the-application)
- [Decisions and trade-offs](#decisions-and-trade-offs)

## Design goals

1. **Local first.** Audio and text never leave the computer.
2. **Faithful.** The transcript is what the recogniser heard; nothing rewrites it.
3. **Do not lose the user's work.** Buffered speech is processed on Stop, a
   failed save keeps the transcript, a crash can be recovered from.
4. **Responsive.** Nothing that can block runs on the GUI thread.
5. **Simple.** Plain Python modules, no database, no plugin system, no
   dependency-injection framework, no server.

## Overview

```
                    GUI thread                         background threads
        ┌──────────────────────────────┐
        │ MainWindow / SettingsDialog  │
        └──────────────┬───────────────┘
                       │ calls, Qt signals
        ┌──────────────▼───────────────┐      ┌────────────────────────────┐
        │ RecordingController          │─────▶│ ModelLoadWorker            │
        │ (state machine, session)     │      │   Transcriber.load()       │
        └───┬───────────┬──────────┬───┘      └────────────────────────────┘
            │           │          │
            │   ┌───────▼────────┐ │   PortAudio callback thread
            │   │ AudioRecorder  │─┼──▶ puts raw blocks into ──┐
            │   └────────────────┘ │                           │ capture queue (bounded)
            │                      │   ┌───────────────────────▼────┐
            │                      │   │ CaptureWorker              │
            │                      │   │   Resampler -> VadProcessor│
            │                      │   └───────────────────────┬────┘
            │                      │                           │ segment queue
            │                      │   ┌───────────────────────▼────┐
            │                      │   │ TranscribeWorker           │
            │                      │   │   Transcriber + Language-  │
            │                      │   │   Tracker                  │
            │                      │   └───────────────────────┬────┘
            │   ┌──────────────────▼┐                          │ Qt signal
            │   │ SessionJournal    │◀─── recognised segments ─┘
            │   └───────────────────┘
        ┌───▼────────────────────────┐        ┌────────────────────────────┐
        │ ExportWorker               │───────▶│ export_manager + exporters │
        └────────────────────────────┘        └────────────────────────────┘
```

## Components

| Module | Responsibility | Depends on Qt |
| --- | --- | --- |
| `main.py` | Start-up: logging, theme, settings, controller, window | yes |
| `app/main_window.py` | Main window; shows state, never does blocking work | yes |
| `app/settings_dialog.py` | Settings form with validation; language chooser | yes |
| `app/help_dialog.py` | Introduction, questions and answers, About page | yes |
| `app/content_panel.py` | Pop-up for document layout and content | yes |
| `app/dock.py` | Sliding bar at the screen edge | yes |
| `app/global_hotkeys.py` | System-wide hotkey through the Windows API | yes |
| `app/single_instance.py` | One instance per user; later launches activate the first | yes |
| `app/icons.py` | Vector icons rendered in the theme colours | yes |
| `app/theme.py` | Colour tokens and style sheet (light and dark) | yes |
| `app/recording_controller.py` | State machine; owns the model, the session and the workers | yes (signals) |
| `app/workers.py` | Background threads | yes (signals) |
| `app/audio_recorder.py` | Device list, microphone stream, resampler | no |
| `app/vad_processor.py` | Silero detector and the segmentation state machine | no |
| `app/transcriber.py` | Model download, device selection, recognition | no |
| `app/language_tracker.py` | Language decision per utterance, session language list | no |
| `app/transcript_models.py` | `Session` and `TranscriptSegment` data classes | no |
| `app/session_journal.py` | Crash-recovery journal | no |
| `app/export_manager.py` | Directory checks, file naming, atomic writes | no |
| `app/exporters/` | One class per file format | no |
| `app/filename_template.py` | Template expansion and file name sanitising | no |
| `app/settings_manager.py` | `Settings` data class and JSON persistence | no |
| `app/i18n/` | Interface strings | no |
| `app/language_names.py` | English names of Whisper's language codes | no |
| `app/paths.py` | Per-user directories | no |
| `app/logging_config.py` | Log file | no |

The engine modules (everything marked "no") can be used and tested without a
GUI. `tools/transcribe_file.py` does exactly that.

## State machine

`RecordingController.state` is one of:

```
            start()                stop()             all speech recognised
  READY ───────────▶ RECORDING ───────────▶ PROCESSING ───────────┬────────▶ SAVING
    ▲                    │                                        │            │
    │                    │ microphone error                       │ no speech  │ ok / failed
    │                    ▼                                        ▼            ▼
    └──────────────── ERROR ◀──────────────────────────────── COMPLETED ◀──────┘
                        │                                         │
                        └────────── start(), save(), save_as() ───┘
```

- Allowed transitions are listed in `_TRANSITIONS`; anything else is logged
  and ignored.
- `start()` works only when the model is loaded and the state is `READY`,
  `COMPLETED` or `ERROR`. A second `start()` while recording returns `False`
  and does nothing, which is what prevents duplicate sessions.
- `stop()` works only in `RECORDING`.
- The window derives every enabled/disabled control from the state in one
  method (`MainWindow._update_controls`).

Model loading is tracked separately (`model_state`: `checking`,
`downloading`, `initializing`, `ready`, `failed`) because it is independent
of recording.

## Threading

| Thread | Created by | Work |
| --- | --- | --- |
| GUI (main) thread | Qt | Widgets, controller logic, journal writes |
| PortAudio callback | sounddevice | Copies each audio block into the capture queue |
| `model-loader` | `ModelLoadWorker` | Download and initialise the model, load the VAD model |
| `capture` | `CaptureWorker` | Resample, measure level, run the VAD, emit segments |
| `transcribe` | `TranscribeWorker` | Run Whisper on each segment |
| `export` | `ExportWorker` | Write the output file |

Workers are `QObject`s that run their `run()` method on a Python daemon
thread. They report through Qt signals. Because the worker objects live in
the GUI thread, Qt delivers their signals there through the event queue, so
**no widget is ever touched from a background thread** and no locks are
needed in the GUI code.

Daemon threads were chosen over `QThread` so that an operation that cannot
be interrupted (a model download) can never keep the process alive or crash
it on exit.

Shared state is minimal:

- two `queue.Queue` objects (thread-safe by design),
- `Backlog`, a counter protected by a lock,
- `Transcriber`, whose `load` and `transcribe` are serialised by a lock,
- `LanguageTracker`, used only by the transcription thread during a session.

**Ordering guarantee on Stop.** `CaptureWorker` emits `finished` (with the
total number of samples) *before* it puts the end marker into the segment
queue. The controller therefore always knows the session duration before the
transcription worker can report that it is done.

## Audio capture

`AudioRecorder` opens a `sounddevice.InputStream` in callback mode.

- **Device selection.** On Windows, PortAudio lists every microphone once per
  host API (MME, DirectSound, WASAPI, WDM-KS). Only WASAPI devices are shown,
  so each microphone appears once and with its full name. The selected device
  is stored by name, because device indexes change when hardware is plugged
  in. A stored device that is missing falls back to the system default.
- **Sample rate.** Whisper and Silero VAD need 16 kHz mono. The stream is
  opened at 16 kHz when the driver allows it (WASAPI shared mode with
  automatic conversion). Otherwise it is opened at the device's native rate
  and `Resampler` converts it: a 63-tap windowed-sinc low-pass filter
  followed by linear interpolation, with filter and phase state carried
  across blocks so there are no discontinuities.
- **Callback.** The callback only mixes to mono and calls `put_nowait`. It
  never blocks, allocates little, and does no signal processing. If the queue
  is full the block is counted as dropped instead of blocking the audio
  driver.
- **Disconnection.** If PortAudio ends the stream by itself, or no block
  arrives for three seconds, `CaptureWorker` reports a stall and the
  controller stops the session normally, keeping everything recorded so far.
- **Silent input.** If the first three seconds are exact digital silence
  (which is what Windows delivers when microphone access is denied), a notice
  explains the likely cause.

## Voice activity detection

`VadProcessor` turns a continuous stream into utterances.

**Detector.** `SileroDetector` runs the Silero VAD ONNX model that ships
inside the faster-whisper package, using onnxruntime on the CPU. It is fed
one 512-sample frame (32 ms) at a time and keeps the model's recurrent state
and a 64-sample context between frames, which makes it a true streaming
detector. No PyTorch and no extra download are required. If the model file
cannot be loaded, `EnergyDetector` (signal energy over an adaptive noise
floor) is used and a warning is logged.

faster-whisper also offers `vad_filter=True`, which applies the same model to
a complete recording. It cannot be used for live segmentation, so VoxNote
drives the model itself and passes `vad_filter=False` to the recogniser.

**Segmentation rules** (all durations configurable, see `VadConfig`):

| Parameter | Default | Effect |
| --- | --- | --- |
| `threshold` | 0.5 | A frame at or above this probability is speech. |
| release threshold | threshold − 0.15 | A frame below this is silence. Frames in between extend whatever is happening (hysteresis). |
| `pre_roll_ms` | 300 | Audio before the first speech frame that is prepended to the segment. |
| `silence_ms` | 1200 | Continuous silence that ends the segment. Shorter values split long sentences at breathing pauses. |
| `post_roll_ms` | 300 | Trailing silence kept at the end of the segment. |
| `min_speech_ms` | 250 | Segments with fewer speech frames are discarded. |
| `max_segment_s` | 28 | Upper limit of a segment. |

Long speech: once a segment reaches 80 % of the maximum, a pause of only
200 ms ends it, so the cut falls between words whenever possible. At 100 %
the segment is cut regardless, and the next segment starts at the very next
sample.

**No duplicates.** Every frame has an absolute sample position. Pre-roll
frames are only used if they lie after the end of the previously emitted
segment, and a forced cut continues exactly where the previous segment ended.
Segments therefore never overlap, which is verified by
`tests/test_vad_processor.py`.

## Buffering

The question "where does audio wait?" has three answers, all in memory:

| Buffer | Type | Bound | Content |
| --- | --- | --- | --- |
| Capture queue | `queue.Queue(maxsize=1024)` | 1024 driver blocks | Raw blocks between the audio callback and `CaptureWorker`. Normally nearly empty. |
| Pre-roll | `collections.deque(maxlen=n)` | `pre_roll_ms` | The last few frames of non-speech audio. |
| Segment queue | `queue.Queue` plus `Backlog` counter | 20 minutes of speech | Complete utterances waiting for the recogniser. |

Why memory and not a file or a database:

- 16 kHz mono float32 audio is 64 kB per second. An utterance of 28 s is
  1.8 MB; the worst-case backlog of 20 minutes is about 77 MB.
- Silence is dropped before it reaches the segment queue, so only speech
  occupies memory.
- Writing audio to disk would contradict the privacy goal that raw audio is
  not retained.
- A database would add a dependency and a failure mode without a benefit:
  there is nothing to query.

What happens at the limits:

- **Capture queue full** (the capture thread stalled): blocks are dropped and
  counted, a notice is shown, memory does not grow.
- **Backlog limit reached** (recognition much slower than speech): recording
  stops automatically with a notice and everything already captured is
  transcribed. Audio is never silently discarded to make room.

On **Stop**, the stream is closed first, then `CaptureWorker` drains the
capture queue, flushes the utterance in progress, and only then ends. The
transcription worker processes every queued segment before the session is
finalised. Nothing that was buffered is thrown away.

Text, unlike audio, does go to disk immediately: see
[Crash recovery](#crash-recovery).

## Transcription

`Transcriber` wraps `faster_whisper.WhisperModel`.

**Loading** (`Transcriber.load`, on the `model-loader` thread):

1. Register the DLL folders of the `nvidia-*` pip packages
   (`register_nvidia_libraries`), so CTranslate2 finds cuBLAS and cuDNN
   without a system-wide CUDA installation.
2. Import the engine. An import failure is mapped to
   `engine_blocked_by_policy` (Windows application control) or
   `engine_import_failed`.
3. Look for the model in the local cache with `local_files_only=True`. No
   network access happens when it is found.
4. Otherwise check free disk space and download the model.
5. Try device candidates in order: `cuda/float16`, `cuda/int8_float16`,
   `cuda/float32` (only those the GPU reports as supported), then `cpu/int8`.
6. After constructing a model, **run one second of silence through it.**
   CTranslate2 loads some GPU libraries lazily, so a missing cuBLAS or cuDNN
   only fails on first use. The warm-up makes that failure happen during
   loading, where falling back to the next candidate is still possible.

The resulting `DeviceInfo` (device, compute type, and the reason if the GPU
is not used) is shown in the status bar and in Settings.

The model is loaded once and reused for all sessions. It is reloaded only
when the user changes the model or the processing device.

**Models.** `app.MODELS` lists the selectable models (`small`, `medium`,
`large-v3-turbo`) with their approximate download size, which is used for the
disk-space check. `large-v3-turbo` is the default: in the developer's tests it
recognised short Turkish and English utterances that `small` got wrong, at
roughly twice the processing time on the GPU.

**Recognising** (`Transcriber.transcribe`, on the `transcribe` thread), for
each utterance:

1. `model.detect_language(audio)` returns a probability for every language.
2. `LanguageTracker.decide` picks the language (see below).
3. `model.transcribe(audio, language=<decision>, task="transcribe", …)`.

Options and their reasons:

| Option | Value | Reason |
| --- | --- | --- |
| `task` | `transcribe` | Never translate. |
| `language` | decided per utterance | Allows language switches inside a session. |
| `condition_on_previous_text` | `False` | Whisper's own carry-over inside one call causes repetition loops. Context is passed explicitly instead, see below. |
| `initial_prompt` | end of the previous utterance | Lets the model continue a sentence that a pause split in two. Only used when the previous utterance was in the same language. |
| `no_speech_threshold` | off (`None`) | The streaming VAD already decided that somebody spoke; the recogniser must not skip the audio as "no speech". |
| `vad_filter` | `False` | Segmentation was already done by the streaming VAD. |
| `beam_size` | 5 | faster-whisper default. |
| `temperature` | 0.0 | Deterministic beam search only; see below. |
| `hotwords` | the user's vocabulary | Optional names and terms the decoder should favour. |
| `no_speech_threshold` | 0.6 | Whisper default guard against silence. |
| `log_prob_threshold` | −1.0 | Whisper default guard against low-confidence output. |
| `compression_ratio_threshold` | 2.4 | Whisper default guard against repetitive output. |

**No sampling fallback.** Whisper's default behaviour retries a poor result
with random sampling at increasing temperatures. VoxNote decodes at
temperature 0 only, for two reasons. First, sampling produces
plausible-sounding text for unclear audio, which works against a faithful
transcript. Second, with CTranslate2 4.7.1 on CUDA, a model that has run a
sampling decode aborts the whole process when it is destroyed (observed on
the development computer: exit code `0xC0000409` when the model was unloaded
or the program ended). Since unloading happens whenever the user switches the
model, this would have crashed the application. Without sampling the abort
does not occur.

**Vocabulary.** The names entered in Settings are passed as `hotwords`. They
are formatted as a normally punctuated list (`Gesi, Erhan.`) because the
decoder imitates the style of its prompt: a hint without punctuation made it
drop the punctuation of the transcript in tests. The transcript is never
edited after recognition.

**Completeness over tidiness.** By default (`keep_uncertain`) every piece of
text the recogniser returns for a detected utterance is kept, including text
it is unsure about. Earlier versions dropped pieces with a high no-speech
probability or a high compression ratio; in practice that removed parts of
real sentences, which is worse for a transcript than an occasional wrong
word. The option can be switched off in Settings. If a result looks like a
repetition loop while context was supplied, the utterance is decoded once
more without context instead of being dropped. Nothing corrects or rewrites
the text.

**GPU failure during a session.** A `RuntimeError` from the GPU (typically
out of memory because another program took the VRAM) makes `Transcriber`
reload the model on the CPU, retry the same utterance and notify the GUI.
Any other failure skips that one utterance, shows a notice and continues.

## Language detection

Detecting the language once per recording would lock the whole session to the
first language. VoxNote detects it **once per utterance**, on exactly the
audio of that utterance.

`LanguageTracker.decide(probabilities, duration)`:

0. If the user ticked spoken languages (`LanguageTracker.allowed`), all other
   languages are removed and the remaining probabilities are rescaled to sum
   to one. Choosing between two or three languages is far more reliable than
   choosing between a hundred. With one allowed language the decision is
   fixed.
1. If the top language is **confident** — probability at least 0.70, or at
   least 0.90 for utterances shorter than 1.5 seconds — use it.
2. Otherwise, if the top language was not used in this session yet but an
   already used language is still **plausible** (its probability is at least
   half of the top one), stay with that language. This suppresses spurious
   switches to unrelated languages on short or unclear audio.
3. Otherwise use the top language, marked as not confident.

Rule 2 deliberately requires plausibility. Forcing Whisper to decode speech
in a language it considers unlikely makes it *translate* instead of
transcribe (observed during development: Turkish "Tamam, anladım." decoded
as English produced "Okay, I got it."). That would violate the faithfulness
goal, so an implausible language is never forced.

`LanguageTracker.record(decision)` is called only for utterances that
produced text. The session list is: languages in order of their first
confident occurrence, followed by languages that were only ever detected
without confidence, so every language label used in the transcript appears
in the metadata.

Limits that no configuration removes: detection is per utterance, not per
word, and a single short word carries too little information.

## Export pipeline

```
Session ──▶ export_manager.export_session(session, directory, template, format)
              1. check_directory            exists? is a directory? writable?
              2. render_filename            template -> safe file name stem
              3. _reserve                   atomically create the first free name
              4. exporter.write(temp file)  format-specific
              5. os.replace(temp, target)   publish the finished file
```

- `build_document` (`app/exporters/base.py`) converts a `Session` and the
  user's `ExportOptions` into a format-independent `ExportDocument` (title,
  the selected metadata rows, language blocks, and the transcript as one
  paragraph). Every exporter renders this object, which is what keeps the
  formats equivalent.
- **Collisions.** `_reserve` opens candidate names with mode `x` (create,
  fail if it exists). The first success is ours even if another program
  creates files at the same time.
- **Atomic writes.** The exporter writes into a hidden temporary file in the
  same folder. Only a complete, non-empty file is moved over the reserved
  name. On any error the temporary file and the placeholder are removed and
  an `ExportError` with a machine-readable code is raised.
- **File names.** `filename_template.py` substitutes placeholders with a
  regular expression (not `str.format`, which could reach object attributes),
  replaces characters that are invalid on Windows, strips leading dots and
  trailing dots or spaces, avoids reserved device names such as `CON`, and
  limits the length. Because separators are replaced, a template cannot
  escape the target directory.
- **Save As** uses `export_to_path` with the path from the system file
  dialog, which has already asked about overwriting.

## Crash recovery

`SessionJournal` appends one JSON line per recognised segment to
`%LOCALAPPDATA%\VoxNote\sessions\<session id>.jsonl` and calls `fsync` after
each line. The cost is negligible at the rate of a few utterances per minute.

- Deleted when the session is saved, contained no speech, or is discarded.
- Kept when saving fails or the process dies.
- On start-up, `MainWindow.check_recovery` offers to recover, discard or
  postpone. Recovery loads the journal into a `Session` and runs the normal
  export.
- A line cut off by a crash is skipped when reading.

## Settings persistence

`Settings` is a data class; `SettingsManager` reads and writes it as JSON in
`%APPDATA%\VoxNote\settings.json`.

- Writing is atomic (temporary file, then `os.replace`).
- Reading is tolerant: unknown keys are ignored (forward compatibility),
  missing keys get defaults, wrong types and out-of-range numbers are
  normalised, and a corrupt file is renamed to `settings.json.corrupt`
  instead of being overwritten.
- `save_directory` is stored as an empty string while the default is in use,
  so the default keeps following the Documents folder if Windows moves it.
  The Documents folder is obtained from the shell (`SHGetKnownFolderPath`),
  not assumed.
- A `schema_version` field is stored for future migrations.

## Interface and localisation

- `theme.py` defines one set of colour tokens for light and one for dark and
  generates the style sheet from them; the variant follows the system colour
  scheme.
- **Icons** (`icons.py`) are small SVG drawings stored as strings and rendered
  with `QSvgRenderer` in the colour of the current theme, with a dimmed
  variant for disabled controls. No image files or icon fonts are shipped.
- The settings dialog sizes itself to the visible tab (`_fit_to_tab`), because
  a `QTabWidget` is otherwise as tall as its tallest page.
- Informational and error messages are shown inline (`Banner`), not in modal
  dialogs. A banner can carry actions, for example *Open File* after saving.
- Document content (`content_panel.py`) is a pop-up that writes straight into
  the settings and is therefore usable during a recording; the settings
  dialog, which is locked while recording, does not repeat these options. Modal dialogs are reserved for decisions that must not be skipped:
  discarding an unsaved transcript, closing during a recording, and recovery.
- **Strings.** `app/i18n/locales/<code>.py` each contain a dictionary.
  `tr(key, **values)` looks up the current language and falls back to
  English. Windows keep message *keys* rather than rendered text, so changing
  the language updates everything immediately (`MainWindow.retranslate`).
  `tests/test_i18n.py` checks that all languages define the same keys and
  placeholders.
- Errors travel through the application as codes (`AudioError.code`,
  `TranscriberError.code`, `ExportError.code`) and are turned into text only
  in the window (`error_text`), which keeps engine modules free of
  user-facing language.

## Desktop integration

Three small pieces let the application be used without its main window in
the foreground. They are created by `MainWindow.enable_desktop_integration`,
which only `main.py` calls, so tests and tools are unaffected.

**Edge bar (`dock.py`).** A separate top-level `QWidget` with the flags
`Tool | FramelessWindowHint | WindowStaysOnTopHint`: no border, no taskbar
entry, above other windows. `WA_TranslucentBackground` allows the rounded
shape, `WA_ShowWithoutActivating` keeps it from stealing the keyboard focus.
Hidden, the window is positioned so that all but an 8-pixel strip lies
outside the screen. `enterEvent` starts a `QPropertyAnimation` on the window
position (160 ms, ease-out) that slides it in; `leaveEvent` starts a 450 ms
timer, after which the bar slides back if the pointer is really gone. The
delay prevents flicker when the pointer crosses the border. The bar does not
talk to the engine itself: it emits `start_requested`, `stop_requested` and
`show_window_requested`, which the main window connects to the same methods
its own buttons use, so all checks (folder, unsaved transcript) apply.

**Global hotkey (`global_hotkeys.py`).** `RegisterHotKey` from the Windows
API registers exactly one combination, `Ctrl+Alt+R`, for the GUI thread.
Windows then posts a `WM_HOTKEY` message when it is pressed, whatever
application has the focus. A `QAbstractNativeEventFilter` installed on the
application sees every native message and turns that one into a Qt signal.
No keyboard hook is installed and no other keystrokes are observed. If the
combination is taken, registration fails and a notice is shown.

**Single instance (`single_instance.py`).** At start, `main.py` tries to
connect to a `QLocalServer` named after the user. If that succeeds, another
VoxNote is running: the new process sends a short message and exits, and the
running one brings its window to the front. Otherwise it creates the server.
This is what makes the `Ctrl+Alt+V` shortcut key of the desktop icon usable
as "show VoxNote": Windows starts the shortcut, and the second start only
activates the first.

## Error handling and logging

- Each engine module defines one exception type with a `code` and a technical
  `detail`. The GUI shows the localised message for the code; the detail goes
  to the log.
- Workers catch exceptions at their top level (`Worker._guarded`), log the
  traceback and emit their failure signal, so a crashed worker cannot leave
  the application stuck in a busy state.
- Uncaught exceptions on the GUI thread are logged by `sys.excepthook`.
- Logs are written to a rotating file (1 MB, three backups). Modules log
  durations, counts, states and error text, never transcript text or audio.

## Resource management

- The microphone stream is created on Start and closed on Stop, on error and
  on exit. `AudioRecorder.stop` is safe to call more than once.
- Every session creates new queues, workers and a new `VadProcessor`, so no
  state leaks between sessions. The Whisper model and the Silero detector are
  reused (the detector's recurrent state is reset per session).
- Worker references are dropped when the session finishes.
- The debug WAV writer, when enabled, is closed in a `finally` block.

## Extending the application

| Task | Where |
| --- | --- |
| Add an export format | See [EXPORT_FORMATS.md](EXPORT_FORMATS.md#adding-a-format) |
| Add an interface language | Copy `app/i18n/locales/en.py`, translate, register in `app/i18n/__init__.py` and in `UI_LANGUAGES` (`settings_manager.py`) |
| Add a setting | Field in `Settings`, range in `LIMITS` if numeric, control in `settings_dialog.py`, strings in every locale |
| Offer another Whisper model | Add it to `MODELS` in `app/__init__.py` with its download size, and add a `settings.model.option.<name>` string to every locale |
| Change segmentation | `VadProcessor` and its tests |

## Decisions and trade-offs

| Decision | Alternative | Why |
| --- | --- | --- |
| Streaming Silero VAD driven by the application | Energy threshold; `vad_filter=True` | Robust against noise and works live; reuses the model file that faster-whisper already ships. |
| Separate language detection call per utterance | Let `transcribe` auto-detect | Exposes all probabilities so the tracker can avoid spurious switches. Costs one extra encoder pass per utterance. |
| In-memory audio buffers with explicit bounds | Temporary files, database | Small, fast, private; see [Buffering](#buffering). |
| Transcript journal on disk | Keep transcript in memory only | A crash must not destroy a long session. Text is small and the journal is deleted after saving. |
| Python daemon threads with Qt signals | `QThread`, `QThreadPool` | Cannot block process exit; signals still arrive on the GUI thread. |
| System fonts for PDF | Bundling a font | No font licence to ship, and CJK coverage comes from fonts Windows already has. Costs: depends on installed fonts. |
| JSON settings file | Registry, `QSettings` | Readable, portable, testable without Qt. |
| Dictionary-based translations | Qt Linguist (`.ts`/`.qm`) | No build step; adding a language is copying one file. |
| English labels in exported files | Localised exports | Files stay consistent whatever the interface language. |
