# Testing

This document describes the automated tests, lists what has actually been
verified so far, and provides a manual checklist for everything that needs a
microphone, a human voice or specific hardware.

- [Automated tests](#automated-tests)
- [Verification status](#verification-status)
- [Pipeline test with an audio file](#pipeline-test-with-an-audio-file)
- [Manual test checklist](#manual-test-checklist)
- [Recording a test result](#recording-a-test-result)

## Automated tests

```powershell
pip install -r requirements-dev.txt
python -m pytest
```

The tests need neither a microphone nor the speech model nor a display (Qt
runs in "offscreen" mode). All application data is redirected to a temporary
folder, so your settings and transcripts are not touched.

| File | Covers |
| --- | --- |
| `tests/test_filename_template.py` | Template expansion, validation, sanitising of invalid characters, path traversal attempts, reserved Windows names, length limit, numeric suffixes for collisions |
| `tests/test_settings.py` | Defaults, save and load round trip with non-ASCII text, atomic writing, corrupt and partial files, clamping of invalid values, data locations |
| `tests/test_exporters.py` | Markdown, text, JSON (including schema validation and deliberately broken documents), DOCX and PDF read back from disk; Turkish characters in PDF; mixed scripts in one PDF; equivalent content across formats; empty transcripts; special characters; collisions; no overwriting; no leftover temporary files; failure handling |
| `tests/test_language_tracker.py` | De-duplication and ordering of languages, confidence thresholds, avoiding unnecessary switches, never forcing an implausible language, restriction to the user's spoken languages |
| `tests/test_vad_processor.py` | Segmentation with a scripted detector: silence, pre-roll and post-roll, short and long pauses, minimum speech, hysteresis, flush on stop, maximum length, no overlapping or duplicated audio, independence from block size; resampler length and continuity |
| `tests/test_session_journal.py` | Journal round trip, durability before close, truncated lines, deletion, unreadable files |
| `tests/test_i18n.py` | Every language has exactly the keys and placeholders of the English table |
| `tests/test_transcriber_options.py` | Uncertain text kept or dropped, context passing, retry without context, vocabulary hint, with a stand-in model |
| `tests/test_document_content.py` | Paragraph layout and content options in every document format; settings for them; the content panel; edge bar positions and requests; start/stop toggle; single-instance activation |
| `tests/test_controller_and_gui.py` | State machine guards; automatic save; empty session; failed save keeps the transcript and allows saving elsewhere; crash recovery; main window controls per state; language switching; settings dialog validation, cancel and defaults; dialog height per tab; language chooser; help window; every icon renders; introduction shown once; theme cycling and persistence |

**Result of the last run by the developer** (Windows 11, Python 3.11.9):
`202 passed`.

## Verification status

Honest status of each area at version 0.5.0. "Verified" means it was actually
exercised on the development computer (Windows 11, Intel laptop with NVIDIA
RTX 3060 Laptop GPU 6 GB, built-in microphone array, Python 3.11.9).

| Area | Status | How |
| --- | --- | --- |
| File name templates, settings, exporters, language tracker, VAD state machine, journal, translations | Verified | Automated tests |
| Turkish characters in all five formats | Verified | Automated tests read the files back |
| Model download on first run | Verified once | The `small` model was downloaded from the Hugging Face Hub through `Transcriber.load` (run from the pipeline tool, not from the window, so the progress display in the status bar was not observed); later starts reused the cache without network access |
| CPU inference (`int8`) | Verified | `tools/transcribe_file.py --device cpu` |
| GPU inference (`cuda`, `float16`) with the pip-installed cuBLAS/cuDNN | Verified | `tools/transcribe_file.py --device auto` and the application itself; no CUDA Toolkit installed |
| English, Turkish and switching between them | Verified with synthetic speech | A WAV file produced with the Windows text-to-speech voices (English, Turkish) was transcribed correctly, with the language detected per utterance |
| Silero VAD on real audio | Verified with the same file | Four utterances separated by pauses were found as four segments; silence produced none |
| Microphone capture → VAD → recognition → automatic save | Verified | The application recorded from the built-in microphone and saved a JSON file. Speech played through the laptop speakers was only partly picked up by the microphone, so this is a functional check, not an accuracy test |
| Start/stop guards (second start, second stop ignored) | Verified | Live run and automated tests |
| Session without speech creates no file | Verified | Live run and automated tests |
| Raw audio retention option | Verified | A 16 kHz mono WAV was written when enabled |
| Logs contain no transcript text | Verified | Checked after a live run |
| Windows application control blocking the engine | Observed | CTranslate2 4.8.2 was blocked by Smart App Control; 4.7.1 loads |
| Interface rendering in light and dark, English/Turkish/German | Verified visually | Screenshots in `docs/images` |
| **Real human speech**, different speakers, accents and rooms | **Not verified** | Needs the manual checklist below |
| **Languages other than English and Turkish** | **Not verified** | No test audio was available |
| **Microphone disconnection during recording** | **Not verified** | Logic is implemented; needs a USB or Bluetooth microphone |
| **Microphone permission denied by Windows** | **Not verified** | Logic is implemented (silent-input notice, open failure message) |
| **CUDA out-of-memory fallback** | **Not verified** | Logic is implemented; hard to provoke reliably |
| **Model download failure / no disk space** | **Not verified** | Logic is implemented |
| **Long sessions (30 minutes and more)** | **Not verified** | |
| **Windows 10, other GPUs, CPU-only computers** | **Not verified** | |
| **French, Italian and Russian interface texts** | **Not reviewed by native speakers** | Rendering was not checked on screen for these three |
| Packaged executable (`dist\VoxNote\VoxNote.exe`) | Verified on the development computer | Built with PyInstaller; started, loaded the model on the GPU and wrote its log |
| Installer | See [RELEASE.md](RELEASE.md#status) | |
| Large v3 Turbo model, language restriction, vocabulary | Verified with synthetic speech | See the comparison below |
| Switching the model in the running application | Verified | Recorded, switched from Large v3 Turbo to Small through the settings path, recorded again, closed with exit code 0 |
| Destroying a GPU model after decoding | Verified | With sampling fallback the process aborted (`0xC0000409`); with deterministic decoding it does not |
| Global hotkey | Partly verified | `RegisterHotKey` succeeded and a posted `WM_HOTKEY` message reached the application; the keys were not physically pressed in the test |
| Edge bar | Partly verified | Shown on the real desktop; sliding in and out was triggered from code and the positions checked; hovering with a real pointer was not tested |
| Start key of the shortcut (`Ctrl+Alt+V`) | **Not verified** | The property is written into the shortcut; pressing it was not tested |
| Longer pause, context and keeping uncertain text | Verified with synthetic speech | Two long sentences with one-second pauses were split into six segments before and two after; the words were identical in both runs, so this test shows the changed segmentation but not a gain in accuracy |
| **Medium model** | **Not verified** | Was not downloaded |
| **Screen readers, high contrast** | **Not verified** | |

Timing observed on the development computer with the synthetic test file
(one run, not a benchmark): utterances of 1.8 to 4.1 seconds were recognised
in about 0.2 seconds each on the GPU and about 3 seconds each on the CPU.
Your numbers will differ; use the log file to measure them.

### Model comparison

One synthetic file (Windows text-to-speech, English and Turkish voices) was
transcribed on the GPU with different settings. This is a single run on
artificial speech, not a benchmark.

| Spoken | Small | Large v3 Turbo | Turbo, languages `en,tr`, vocabulary `Gesi, Erhan` |
| --- | --- | --- | --- |
| I think I should speak more precisely, so you can understand me better. | correct | correct | correct |
| Precisely. (single word) | wrong ("Regissade", Portuguese) | wrong ("Rediçade", Portuguese) | wrong ("Predissade", English) |
| Accomplish. (single word) | wrong | wrong | wrong |
| Gesi bağlarında dolanıyorum. | "Gizli bağlarında …" | "Gezi bağlarında …" | correct |
| Evet. | wrong ("in it.", English) | correct | correct |
| Kendimi iyi hissediyorum. | correct | correct | correct |
| Okay, that's it. | correct | correct | correct |
| Hayır. | wrong ("Olhe isso.", Portuguese) | correct | correct |
| Languages reported | English, Turkish, Portuguese | English, Turkish, Portuguese | English, Turkish |
| Time per utterance | about 0.2 s | about 0.5 s | about 0.5 s |

What this shows: the larger model fixes short Turkish words, the language
restriction removes the stray third language, the vocabulary fixes the place
name, and isolated single English words from a synthetic voice stay wrong in
every configuration.

## Pipeline test with an audio file

`tools/transcribe_file.py` feeds a WAV file through the same resampler, VAD,
language tracker and recogniser that the application uses, in small blocks,
as if it came from a microphone. It is the quickest way to check recognition
without speaking.

```powershell
python tools/transcribe_file.py path\to\audio.wav
python tools/transcribe_file.py path\to\audio.wav --device cpu
python tools/transcribe_file.py path\to\audio.wav --model small --languages en,tr --vocabulary "Gesi, Erhan"
```

Only 16-bit PCM WAV files are supported. To create a test file with the
Windows text-to-speech voices that are installed on your system:

```powershell
Add-Type -AssemblyName System.Speech
$speech = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speech.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name }
$speech.SetOutputToWaveFile("$PWD\test.wav")
$speech.Speak("Yesterday I went to the gym, and I trained for about one hour.")
$speech.Dispose()
python tools/transcribe_file.py test.wav
```

Example of the tool's output format:

```
Input: 26.7 s at 22050 Hz
Model ready in 9.6 s on cuda (float16)
VAD found 4 speech segment(s)
[00:00:02] English p=1.00 confident audio=4.1s took=0.24s: Yesterday I went to the gym, and I trained for about one hour.
[00:00:08] Turkish p=0.99 confident audio=3.6s took=0.22s: Sonra arkadaşımı gördüm ve birlikte kahve içmeye gittik.
[00:00:14] English p=0.99 confident audio=1.8s took=0.18s: We talked for a while.
[00:00:22] English p=0.38 tentative audio=1.0s took=0.17s: Yeah, it's
Languages: English, Turkish
```

The last line of that run is instructive: the file ended with the single
Turkish word "Evet." spoken by a synthetic voice. One second of audio was not
enough for the model to identify the language, and the word was transcribed
wrongly. This is the short-utterance limitation described in the README.

## Manual test checklist

Run these with a real microphone. Unless stated otherwise, use the default
settings. For each test note **Pass**, **Fail** or **Not run**, and what you
observed.

### A. Start-up

| # | Step | Expected |
| --- | --- | --- |
| A1 | Start VoxNote on a computer that already has the model | Window appears at once; status bar shows "Loading speech model…", then "Model: small · …"; **Start Recording** becomes enabled |
| A2 | Hover over **Start Recording** while the model loads | Tooltip explains that the model is loading |
| A3 | Rename the model cache folder, disconnect the network, start VoxNote | A red message explains that the model could not be downloaded, with **Try Again**; the window stays usable |
| A4 | Reconnect and press **Try Again** | Download progress in megabytes, then Ready |
| A5 | Check **Settings › Recognition** | Model, device and compute type are correct; **Open Model Folder** opens the model |
| A6 | Press **Help** (`F1`) | Questions and About are shown in the interface language |

### B. Recording workflow

| # | Step | Expected |
| --- | --- | --- |
| B1 | **English only.** Speak three sentences with pauses of about two seconds | Three or more lines under "English"; Languages: English; file saved; path shown |
| B2 | **Turkish only.** Speak three sentences | Lines under "Turkish" with correct ğ, ü, ş, ı, ö, ç; Languages: Turkish |
| B3 | **English → Turkish.** Speak two English sentences, pause, then two Turkish sentences | An "English" block followed by a "Turkish" block; Languages: English, Turkish; nothing translated |
| B4 | **Turkish → English.** The reverse order | Languages: Turkish, English |
| B5 | **Another language** you speak (for example German or French) | Text in that language under the right heading |
| B6 | **Short pauses.** Speak one sentence with half-second pauses between phrases | One segment, not one per phrase |
| B7 | **Long silence.** Speak, stay silent for 30 seconds, speak again | Two segments; no text for the silence; timestamps about 30 seconds apart |
| B8 | **No speech.** Start, stay silent for 15 seconds, stop | "No speech was detected, so no file was created."; no file in the save folder |
| B9 | **Immediate stop.** Start and stop within one second | Same as B8, no error |
| B10 | **Background noise.** Record with a fan, keyboard typing or street noise, without speaking | No text, or far less than with speech; if text appears, raise Speech sensitivity and repeat |
| B11 | **Speech over noise.** Speak with the same noise present | Speech is transcribed |
| B12 | **Stop while speaking.** Press Stop in the middle of a sentence | The words spoken before Stop appear; nothing is lost |
| B13 | **Long utterance.** Speak for about a minute without pausing | Several segments, no missing or duplicated words at the joins |
| B14 | **Stop and restart.** Record, stop, record again, three times | Each session produces its own file; the transcript view is cleared for each new session; no slowdown |
| B15 | **Double start.** Press `Ctrl+R` repeatedly while recording | Nothing happens; still one session |
| B16 | **Faithfulness.** Say a sentence with a deliberate grammar mistake | The mistake is in the transcript; it has not been corrected |

### C. Output

| # | Step | Expected |
| --- | --- | --- |
| C1 | **Custom folder.** Choose a new folder with **Change…**, record | File appears in that folder |
| C2 | Restart VoxNote | The folder is still selected |
| C3 | In Settings, type a folder that does not exist | "Create it?" question; folder is created on Yes |
| C4 | **Every format.** Record once, then use **Save As…** for Markdown, text, JSON, Word and PDF | Five files that open in suitable programs with identical content and correct special characters |
| C5 | Set each format as default in turn and record | Automatic save uses that format |
| C6 | **File name.** Set the template to `test_{session_id}_{duration}` | Preview updates; saved file has that name |
| C7 | Type `{wrong}` into the template | Error under the field; **Save** disabled |
| C8 | **Collision.** Set the template to `fixed` and record twice | `fixed.md` and `fixed_2.md`; the first file is unchanged |
| C9 | **Open File**, **Open Folder**, **Copy Text** | Each does what it says |
| C10 | **Export failure.** Choose a folder on a USB drive, start recording, remove the drive, stop | Status "Error" with an explanation; transcript still visible; **Save As…** to another folder succeeds |
| C11 | Enable "Open the document after it has been saved" and record | The document opens automatically |
| C12 | Disable timestamps in **Document Content** and record | No `[00:00:00]` prefixes in preview and file |
| C13 | Choose *One continuous paragraph*, untick everything under *Include*, record three sentences | The file contains exactly the three sentences as one paragraph |
| C14 | Open **Document Content** during a recording and change options | The panel opens; the saved file follows the new options |
| C15 | Untick only *Session ID* | Every format except JSON lacks the session ID |

### D. Devices and failures

| # | Step | Expected |
| --- | --- | --- |
| D1 | Select a specific microphone, record | That microphone is used (level meter reacts to it only) |
| D2 | Plug in a USB microphone and press **Refresh** | It appears in the list |
| D3 | **Disconnection.** Record with a USB microphone and unplug it | Notice that the microphone stopped; speech so far is transcribed and saved |
| D4 | **Permission.** Switch off microphone access for desktop apps in Windows, record | A message about the microphone or about silent input, mentioning the Windows setting |
| D5 | No microphone connected at all | "No microphone was found" message; no crash |
| D6 | Force **Processor (CPU)** in Settings | Status bar shows CPU; recording still works |
| D8 | Switch the model in Settings after a recording, save | The model reloads (or downloads); no crash; the next recording works |
| D9 | Tick only English and Turkish under Spoken languages, say short words in both | No other language appears in the transcript |
| D10 | Add a name to "Names and special words" and say it in a sentence | The name is written as entered |
| D7 | Fill the video memory with another program, then record | Falls back to CPU with a notice, or works; no crash |

### E. Application lifecycle

| # | Step | Expected |
| --- | --- | --- |
| E1 | **Close during recording.** Click the window's close button while recording | Question with "Stop, Save and Close" and "Keep Recording" |
| E2 | Choose "Stop, Save and Close" | File is saved, then the window closes |
| E3 | **Crash recovery.** While recording, after some text appeared, end the process in Task Manager; start again | Offer to recover; the recovered file contains the text that had appeared |
| E4 | Choose **Discard** in the recovery question | No further question at the next start |
| E5 | **Settings persistence.** Change every setting, restart | All values are kept |
| E6 | **Cancel in Settings.** Change values, press Cancel | Nothing changed |
| E7 | **Interface language.** Switch to Turkish, then German | All texts change immediately; recognition is unaffected |
| E8 | **Offline.** Disconnect the network and record | Works as before |
| E9 | **Responsiveness.** Move and resize the window during recording and processing | Always responsive |
| E10 | **Appearance.** Press `Ctrl+T` three times, also during a recording | Light, dark, system in turn; transcript stays; choice is kept after restart |
| E11 | With "Same as system", switch Windows between light and dark while VoxNote runs | VoxNote follows |
| E12 | Delete `settings.json` and start VoxNote | The introduction opens once; not on the next start |
| E13 | **Edge bar.** Move the pointer to the strip at the screen edge | The bar slides out; it slides back when the pointer leaves |
| E14 | Start and stop a recording from the edge bar | Same result as with the window buttons; the strip is red while recording |
| E15 | **Global shortcut.** With another program in front, press `Ctrl+Alt+R` twice | Recording starts, then stops and saves |
| E16 | Press `Ctrl+Alt+V` with VoxNote closed, then again with it open but covered | VoxNote starts; the second press brings the window to the front, no second window |

### F. Privacy checks

| # | Step | Expected |
| --- | --- | --- |
| F1 | After several sessions, look into `%LOCALAPPDATA%\VoxNote\audio` | Empty or missing (retention is off) |
| F2 | Search `voxnote.log` for a word you spoke | Not found |
| F3 | After a normally saved session, look into `%LOCALAPPDATA%\VoxNote\sessions` | Empty |
| F4 | Watch network activity (for example with Resource Monitor) while recording | No connections by the VoxNote process |

## Recording a test result

When you run the checklist, keep a short record so that claims about
compatibility stay truthful:

```
Date:
VoxNote version:
Windows version:
Processor / GPU / driver:
Microphone:
Device shown in status bar:
Tests run:      (for example B1–B16, C1–C12)
Failures:       (number, what happened, relevant log lines)
```
