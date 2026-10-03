"""English interface strings (reference language)."""

STRINGS = {
    "app.version": "Version {version}",
    "unit.ms": "ms",
    "unit.s": "s",
    # Main window
    "main.settings": "Settings",
    "main.settings.tip": "Open settings ({shortcut})",
    "main.start": "\u25cf  Start Recording",
    "main.start.tip": "Start a new recording ({shortcut})",
    "main.start.tip.model": "Available as soon as the speech model has loaded",
    "main.start.tip.busy": "Available when the current session has finished",
    "main.stop": "\u25a0  Stop Recording",
    "main.stop.tip": "Stop, finish the transcript and save it ({shortcut})",
    "main.microphone": "Microphone:",
    "main.microphone.default": "System default microphone",
    "main.refresh": "Refresh",
    "main.refresh.tip": "Look for newly connected microphones",
    "main.refresh.done": "Microphones found: {count}",
    "main.level": "Input level:",
    "main.elapsed": "Elapsed recording time",
    "main.status": "Status: {status}",
    "main.transcript": "Transcript",
    "main.transcript.placeholder": (
        "Your words appear here while you speak. Press \u201cStart Recording\u201d to begin."
    ),
    "main.languages": "Languages: {languages}",
    "main.languages.none": "none detected yet",
    "main.copy": "Copy Text",
    "main.copy.tip": "Copy the transcript text to the clipboard ({shortcut})",
    "main.copy.done": "Transcript copied to the clipboard.",
    "main.output": "Output",
    "main.folder": "Save folder:",
    "main.folder.change": "Change\u2026",
    "main.folder.change.tip": "Choose where transcripts are saved",
    "main.folder.dialog": "Choose the folder for saved transcripts",
    "main.folder.changed": "Save folder changed.",
    "main.format": "Format:",
    "main.filename_hint": "File name for this session: {name}",
    "main.filename_example": "Example file name: {name}",
    "main.open_file": "Open File",
    "main.open_folder": "Open Folder",
    "main.open_folder.tip": "Show the saved file in its folder ({shortcut})",
    "main.save": "Save",
    "main.save.tip": "Save the transcript to the save folder",
    "main.save_as": "Save As\u2026",
    "main.save_as.tip": "Save the transcript to another place or format ({shortcut})",
    "main.save_as.dialog": "Save transcript as",
    "main.dismiss": "Dismiss this message",
    # States
    "state.ready": "Ready",
    "state.recording": "Recording",
    "state.recording.speech": "Recording \u00b7 speech detected",
    "state.processing": "Processing speech",
    "state.processing.pending": "Processing speech \u00b7 {seconds} s left",
    "state.saving": "Saving file",
    "state.completed": "Completed",
    "state.error": "Error",
    # Results and notices
    "result.saved": "Saved: {path}",
    "result.file_missing": "The saved file is no longer at its location. Use \u201cSave As\u2026\u201d to save it again.",
    "result.open_failed": "No application is available to open {path}.",
    "notice.no_speech": "No speech was detected, so no file was created.",
    "notice.microphone_disconnected": (
        "The microphone stopped delivering audio, so recording was stopped. "
        "Everything spoken before that is kept."
    ),
    "notice.backlog_limit": (
        "Speech recognition could not keep up, so recording was stopped. "
        "Everything recorded so far is being transcribed."
    ),
    "notice.silent_input": (
        "The microphone delivers only silence. Check that it is not muted and that "
        "Windows allows desktop apps to use the microphone "
        "(Settings \u203a Privacy & security \u203a Microphone)."
    ),
    "notice.audio_dropped": (
        "The computer was too busy and a short piece of audio was lost."
    ),
    "notice.transcription_failed": (
        "A part of the recording could not be transcribed and was skipped. "
        "Details are in the log file."
    ),
    "notice.gpu_fallback": (
        "The graphics card could not be used any more. Recognition continues on the "
        "processor and will be slower."
    ),
    "notice.session_recovered": "An unsaved session was recovered.",
    # Errors
    "error.unknown": "Something went wrong. Details were written to the log file:\n{log}",
    "error.settings_save_failed": "The settings could not be saved: {detail}",
    "error.no_microphone": (
        "No microphone was found. Connect a microphone and press \u201cRefresh\u201d."
    ),
    "error.microphone_open_failed": (
        "The microphone could not be opened. Make sure no other program uses it "
        "exclusively and that Windows allows desktop apps to use the microphone "
        "(Settings \u203a Privacy & security \u203a Microphone)."
    ),
    "error.audio_backend_unavailable": (
        "Audio recording is not available on this computer. Details were written to "
        "the log file:\n{log}"
    ),
    "error.engine_blocked_by_policy": (
        "Windows blocked the speech recognition engine (Smart App Control or another "
        "application control policy). See \u201cTroubleshooting\u201d in the documentation."
    ),
    "error.engine_import_failed": (
        "The speech recognition engine could not be started. The installation may be "
        "incomplete. Details were written to the log file:\n{log}"
    ),
    "error.model_cache_unwritable": (
        "The folder for the speech model cannot be written to: {detail}"
    ),
    "error.no_disk_space": (
        "There is not enough free disk space to download the speech model "
        "(about 1 GB is needed)."
    ),
    "error.model_download_failed": (
        "The speech model could not be downloaded. An internet connection is needed "
        "the first time only. Check the connection and try again."
    ),
    "error.model_load_failed": (
        "The speech model could not be loaded. Details were written to the log file:\n{log}"
    ),
    "error.model_not_loaded": "The speech model is not loaded yet.",
    "error.directory_missing": "The save folder does not exist: {detail}",
    "error.directory_invalid": "The save location is not a folder: {detail}",
    "error.directory_not_writable": (
        "The save folder cannot be written to. Choose another folder. "
        "Your transcript is still here and has not been lost."
    ),
    "error.export_failed": (
        "The file could not be saved. Your transcript is still here: use "
        "\u201cSave\u201d to try again or \u201cSave As\u2026\u201d to choose another place."
    ),
    "error.unknown_format": "The selected file format is not supported.",
    "error.pdf_font_missing": (
        "No font that supports all characters was found, so the PDF was not created. "
        "Choose another format or see \u201cTroubleshooting\u201d in the documentation."
    ),
    # Model and device
    "model.idle": "Speech model: not loaded",
    "model.checking": "Checking speech model\u2026",
    "model.downloading": "Downloading speech model (first run only)\u2026",
    "model.downloading.progress": "Downloading speech model\u2026 {megabytes} MB",
    "model.initializing": "Loading speech model\u2026",
    "model.ready": "Model: {model} \u00b7 {device}",
    "model.failed": "Speech model unavailable",
    "model.retry": "Try Again",
    "model.tip": "Speech is recognised on this computer. No audio is sent anywhere.",
    "device.gpu": "GPU (NVIDIA CUDA, {compute_type})",
    "device.cpu": "CPU ({compute_type})",
    "device.reason.cpu_selected": "The processor is used because it is selected in Settings.",
    "device.reason.cuda_unavailable": (
        "The processor is used because no compatible NVIDIA graphics card was found."
    ),
    "device.reason.cuda_unsupported_compute_type": (
        "The processor is used because the graphics card does not support a suitable "
        "number format."
    ),
    "device.reason.cuda_init_failed": (
        "The processor is used because the graphics card could not be initialised. "
        "The NVIDIA libraries (cuBLAS, cuDNN) may be missing."
    ),
    "device.reason.cuda_out_of_memory": (
        "The processor is used because the graphics card ran out of memory."
    ),
    "device.reason.cuda_runtime_error": (
        "The processor is used because the graphics card reported an error."
    ),
    # Dialogs
    "dialog.unsaved.title": "Unsaved transcript",
    "dialog.unsaved.text": (
        "The current transcript has not been saved. Starting a new recording discards it."
    ),
    "dialog.recover.title": "Recover unsaved sessions",
    "dialog.recover.text": (
        "{count} session(s) were not saved the last time the application ran. "
        "Do you want to recover and save them now?"
    ),
    "dialog.recover.recover": "Recover and Save",
    "dialog.recover.discard": "Discard",
    "dialog.recover.later": "Decide Later",
    "dialog.close.title": "Recording in progress",
    "dialog.close.recording": (
        "A recording is in progress. Stop it and save the transcript before closing?"
    ),
    "dialog.close.stop_save": "Stop, Save and Close",
    "dialog.close.keep": "Keep Recording",
    "dialog.close.wait": "Finishing the transcript. The window closes when it has been saved\u2026",
    "dialog.close.unsaved": (
        "The transcript has not been saved. If you close now, it will be offered for "
        "recovery the next time the application starts."
    ),
    # Settings
    "settings.title": "Settings",
    "settings.tab.general": "General",
    "settings.tab.recording": "Recording",
    "settings.tab.system": "System",
    "settings.save": "Save",
    "settings.cancel": "Cancel",
    "settings.defaults": "Restore Defaults",
    "settings.defaults.tip": "Fill the form with the default values. Nothing changes until you save.",
    "settings.saved": "Settings saved.",
    "settings.ui_language": "Interface language:",
    "settings.ui_language.hint": (
        "Changes the language of this application only. Speech is recognised in "
        "whatever language is spoken."
    ),
    "settings.folder": "Save folder:",
    "settings.folder.hint": "Transcripts are saved here automatically when a recording stops.",
    "settings.folder.error.relative": "Enter a full path, for example C:\\Users\\Name\\Documents\\Transcripts.",
    "settings.folder.create.title": "Create folder",
    "settings.folder.create.text": "This folder does not exist:\n{path}\n\nCreate it?",
    "settings.browse": "Browse\u2026",
    "settings.format": "File format:",
    "settings.template": "File name:",
    "settings.template.hint": "Available placeholders: {placeholders}",
    "settings.template.preview": "Preview: {name}",
    "settings.template.error.empty": "The file name must not be empty.",
    "settings.template.error.unbalanced": "A curly bracket is not closed.",
    "settings.template.error.unknown": "Unknown placeholder: {name}",
    "settings.documents": "Documents:",
    "settings.timestamps": "Show the time at the start of each transcript line",
    "settings.open_after_save": "Open the document after it has been saved",
    "settings.microphone": "Microphone:",
    "settings.silence": "Pause that ends a segment:",
    "settings.silence.hint": (
        "Silence of this length ends the current segment. Shorter pauses stay inside it. "
        "Increase it if sentences are split too often."
    ),
    "settings.threshold": "Speech sensitivity:",
    "settings.threshold.hint": (
        "Lower values pick up quiet speech but also more background noise. "
        "Higher values ignore more noise."
    ),
    "settings.min_speech": "Shortest speech:",
    "settings.min_speech.hint": "Sounds shorter than this, such as clicks, are ignored.",
    "settings.max_segment": "Longest segment:",
    "settings.max_segment.hint": (
        "Continuous speech is split at the next short pause when it approaches this length."
    ),
    "settings.pre_roll": "Lead-in:",
    "settings.pre_roll.hint": "Audio kept before speech is detected, so the first syllable is not cut off.",
    "settings.post_roll": "Lead-out:",
    "settings.post_roll.hint": "Audio kept after speech ends, so the last syllable is not cut off.",
    "settings.debugging": "Troubleshooting:",
    "settings.retain_audio": "Keep the raw audio of each session",
    "settings.retain_audio.hint": (
        "Off by default. When on, the microphone audio of every session is stored as a "
        "WAV file on this computer until you delete it."
    ),
    "settings.open_audio_folder": "Open Audio Folder",
    "settings.device": "Processing device:",
    "settings.device.hint": (
        "\u201cAutomatic\u201d uses an NVIDIA graphics card when one works and the processor otherwise."
    ),
    "settings.device.auto": "Automatic (recommended)",
    "settings.device.cuda": "Graphics card (NVIDIA CUDA)",
    "settings.device.cpu": "Processor (CPU)",
    "settings.device.in_use": "Currently used:",
    "settings.model": "Speech model:",
    "settings.model.cached": "Whisper {model} \u00b7 stored on this computer ({megabytes} MB)",
    "settings.model.missing": "Whisper {model} \u00b7 not downloaded yet",
    "settings.model.location": "Model location:",
    "settings.model.open": "Open Model Folder",
    "settings.logs": "Log files:",
    "settings.logs.open": "Open Log Folder",
    "settings.logs.hint": "Logs contain technical details only, never audio or transcript text.",
    "settings.privacy": "Privacy:",
    "settings.privacy.text": (
        "Audio and transcripts stay on this computer. The internet is used only once, "
        "to download the speech model."
    ),
}
