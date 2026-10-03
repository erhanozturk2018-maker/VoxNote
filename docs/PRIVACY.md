# Privacy

VoxNote is designed so that your voice and your words stay on your computer.
This document states precisely what the application stores, where, and what
it uses the network for, so that the claim can be checked against the code.

## Summary

| Question | Answer |
| --- | --- |
| Is audio sent to a server? | No. |
| Are transcripts sent to a server? | No. |
| Is there telemetry, analytics or crash reporting? | No. |
| Is an account or licence check required? | No. |
| Does the application open a network port or run a server? | No. |
| Does it use an online AI or transcription service? | No. Recognition runs locally. |
| When is the network used? | To install the Python packages, and once to download the speech model. |
| Is microphone audio stored on disk? | No, unless you enable the debugging option. |

## What stays on your computer

### Microphone audio

- Audio is captured into memory, examined by the voice activity detector and,
  when speech is found, passed to the speech model. All of this happens in
  the VoxNote process on your computer.
- Silence is discarded as it arrives. Speech is discarded as soon as it has
  been recognised.
- **Audio is not written to disk by default.**
- If you switch on **Settings › Recording › Keep the raw audio of each
  session**, one WAV file per session is written to
  `%LOCALAPPDATA%\VoxNote\audio\`. This option exists for troubleshooting, is
  off by default, and the files stay there until you delete them. VoxNote
  never sends them anywhere.

### Transcripts

- The transcript of the current session is held in memory and shown in the
  window.
- When a recording stops, the transcript is written to the save folder you
  chose (default: `Documents\VoxNote`).
- **Recovery journal.** While recording, each recognised utterance is also
  appended to a file in `%LOCALAPPDATA%\VoxNote\sessions\`, so that a crash
  does not destroy your work. The journal contains transcript text and
  timestamps, never audio. It is deleted as soon as the session has been
  saved, when a session contained no speech, or when you choose **Discard**.
  It remains only while a transcript is unsaved: after a failed save, after
  the application stopped unexpectedly, or after you closed it with an
  unsaved transcript.

### Settings

`%APPDATA%\VoxNote\settings.json` contains your preferences: interface
language, save folder, file name template, export format, the name of the
selected microphone and the recording options. It contains no transcript
text and no audio.

### Log files

`%LOCALAPPDATA%\VoxNote\logs\voxnote.log` contains technical information:
start-up, state changes, durations, counts and error messages.

- **Transcript text is never logged.**
- **Audio is never logged.**
- Error messages can contain file and folder paths, which may include your
  Windows user name. Keep that in mind before sharing a log.

### Exported document metadata

Exported files contain the date, duration, detected languages, a random
session identifier and the name of the speech model. They do not contain
your user name or computer name: the author fields of DOCX and PDF files are
deliberately left empty.

## What the network is used for

### 1. Installing dependencies

`pip install` downloads Python packages from the Python Package Index
(pypi.org). This happens only when you run the command.

### 2. Downloading the speech model (first start only)

When the model is not yet on the computer, VoxNote downloads it from the
Hugging Face Hub (`huggingface.co`, repository
`Systran/faster-whisper-small`).

- As with any download, the server sees your IP address and standard request
  headers. No audio, transcript or personal data from VoxNote is part of the
  request.
- VoxNote sets `HF_HUB_DISABLE_TELEMETRY=1`, which switches off the usage
  statistics of the Hugging Face client library.
- On every later start, VoxNote first looks for the model on disk
  (`local_files_only`) and, when it is found, makes **no network request at
  all**.

### Nothing else

There is no update check, no error reporting, no advertising and no
third-party service. You can verify offline operation by disconnecting the
computer from the network after the first start: recording, recognition and
export keep working.

The Qt framework and the other libraries are used without any of their
networking features.

## What the application does not do

- It does not upload, share or synchronise recordings or transcripts.
- It does not record when you have not pressed **Start Recording**; the
  microphone is opened on Start and released on Stop.
- It does not keep audio after recognition (unless you enabled retention).
- It does not analyse, score, correct or translate what you say.
- It does not collect information about you or your computer.

## Things outside VoxNote's control

- **The save folder.** If you choose a folder that is synchronised by
  OneDrive, Dropbox or a similar service, that service uploads the exported
  transcripts. Choose a local folder if you do not want this. Note that
  Windows often places the Documents folder itself in OneDrive.
- **What you do with exports.** Uploading a transcript to another tool is
  your decision and subject to that tool's privacy terms.
- **Other people.** Recording other people may require their consent,
  depending on where you live. That responsibility lies with the user.
- **The operating system.** Windows and the audio driver handle the
  microphone signal before VoxNote receives it.

## Deleting your data

| Data | How to delete |
| --- | --- |
| Transcripts | Delete the files in your save folder |
| Recovery journals | Choose **Discard** when asked at start-up, or delete `%LOCALAPPDATA%\VoxNote\sessions` |
| Retained audio | **Settings › Recording › Open Audio Folder**, then delete the files |
| Logs | Delete `%LOCALAPPDATA%\VoxNote\logs` |
| Settings | Delete `%APPDATA%\VoxNote` |
| Speech model | Delete the folder shown in **Settings › System › Model location** |

## Verifying these statements

The relevant code is small:

| Topic | File |
| --- | --- |
| Audio capture and buffering | `app/audio_recorder.py`, `app/workers.py` |
| The only network call (model download) | `Transcriber._download` in `app/transcriber.py` |
| Offline model lookup | `Transcriber.cached_model_path` in `app/transcriber.py` |
| Optional audio retention | `CaptureWorker._open_writer` in `app/workers.py` |
| Recovery journal | `app/session_journal.py` |
| Logging | `app/logging_config.py` |
| Data locations | `app/paths.py` |
