"""German interface strings."""

STRINGS = {
    "app.version": "Version {version}",
    "unit.ms": "ms",
    "unit.s": "s",
    # Main window
    "main.settings": "Einstellungen",
    "main.settings.tip": "Einstellungen öffnen ({shortcut})",
    "main.start": "\u25cf  Aufnahme starten",
    "main.start.tip": "Neue Aufnahme starten ({shortcut})",
    "main.start.tip.model": "Verfügbar, sobald das Sprachmodell geladen ist",
    "main.start.tip.busy": "Verfügbar, sobald die aktuelle Sitzung abgeschlossen ist",
    "main.stop": "\u25a0  Aufnahme stoppen",
    "main.stop.tip": "Stoppen, Transkript fertigstellen und speichern ({shortcut})",
    "main.microphone": "Mikrofon:",
    "main.microphone.default": "Standardmikrofon des Systems",
    "main.refresh": "Aktualisieren",
    "main.refresh.tip": "Nach neu angeschlossenen Mikrofonen suchen",
    "main.refresh.done": "Gefundene Mikrofone: {count}",
    "main.level": "Eingangspegel:",
    "main.elapsed": "Bisherige Aufnahmedauer",
    "main.status": "Status: {status}",
    "main.transcript": "Transkript",
    "main.transcript.placeholder": (
        "Ihre Worte erscheinen hier, während Sie sprechen. "
        "Klicken Sie zum Beginnen auf \u201eAufnahme starten\u201c."
    ),
    "main.languages": "Sprachen: {languages}",
    "main.languages.none": "noch keine erkannt",
    "main.copy": "Text kopieren",
    "main.copy.tip": "Transkripttext in die Zwischenablage kopieren ({shortcut})",
    "main.copy.done": "Transkript in die Zwischenablage kopiert.",
    "main.output": "Ausgabe",
    "main.folder": "Speicherordner:",
    "main.folder.change": "Ändern\u2026",
    "main.folder.change.tip": "Festlegen, wo Transkripte gespeichert werden",
    "main.folder.dialog": "Ordner für gespeicherte Transkripte auswählen",
    "main.folder.changed": "Speicherordner geändert.",
    "main.format": "Format:",
    "main.filename_hint": "Dateiname für diese Sitzung: {name}",
    "main.open_file": "Datei öffnen",
    "main.open_folder": "Ordner öffnen",
    "main.open_folder.tip": "Gespeicherte Datei im Ordner anzeigen ({shortcut})",
    "main.save": "Speichern",
    "main.save.tip": "Transkript im Speicherordner speichern",
    "main.save_as": "Speichern unter\u2026",
    "main.save_as.tip": "Transkript an einem anderen Ort oder in einem anderen Format speichern ({shortcut})",
    "main.save_as.dialog": "Transkript speichern unter",
    "main.dismiss": "Diese Meldung schließen",
    # States
    "state.ready": "Bereit",
    "state.recording": "Aufnahme läuft",
    "state.recording.speech": "Aufnahme läuft \u00b7 Sprache erkannt",
    "state.processing": "Sprache wird verarbeitet",
    "state.processing.pending": "Sprache wird verarbeitet \u00b7 noch {seconds} s",
    "state.saving": "Datei wird gespeichert",
    "state.completed": "Abgeschlossen",
    "state.error": "Fehler",
    # Results and notices
    "result.saved": "Gespeichert: {path}",
    "result.file_missing": (
        "Die gespeicherte Datei befindet sich nicht mehr an ihrem Ort. "
        "Mit \u201eSpeichern unter\u2026\u201c können Sie sie erneut speichern."
    ),
    "result.open_failed": "Es ist keine Anwendung zum Öffnen von {path} vorhanden.",
    "notice.no_speech": "Es wurde keine Sprache erkannt, daher wurde keine Datei erstellt.",
    "notice.microphone_disconnected": (
        "Das Mikrofon liefert kein Audio mehr, daher wurde die Aufnahme gestoppt. "
        "Alles bis dahin Gesprochene bleibt erhalten."
    ),
    "notice.backlog_limit": (
        "Die Spracherkennung kam nicht mehr hinterher, daher wurde die Aufnahme gestoppt. "
        "Alles bisher Aufgenommene wird transkribiert."
    ),
    "notice.silent_input": (
        "Das Mikrofon liefert nur Stille. Prüfen Sie, ob es stummgeschaltet ist und ob "
        "Windows Desktop-Apps den Zugriff auf das Mikrofon erlaubt "
        "(Einstellungen \u203a Datenschutz und Sicherheit \u203a Mikrofon)."
    ),
    "notice.audio_dropped": (
        "Der Computer war zu stark ausgelastet, ein kurzes Stück Audio ging verloren."
    ),
    "notice.transcription_failed": (
        "Ein Teil der Aufnahme konnte nicht transkribiert werden und wurde übersprungen. "
        "Details stehen in der Protokolldatei."
    ),
    "notice.gpu_fallback": (
        "Die Grafikkarte kann nicht mehr verwendet werden. Die Erkennung läuft auf dem "
        "Prozessor weiter und wird langsamer."
    ),
    "notice.session_recovered": "Eine nicht gespeicherte Sitzung wurde wiederhergestellt.",
    # Errors
    "error.unknown": "Etwas ist schiefgelaufen. Details wurden in die Protokolldatei geschrieben:\n{log}",
    "error.settings_save_failed": "Die Einstellungen konnten nicht gespeichert werden: {detail}",
    "error.no_microphone": (
        "Es wurde kein Mikrofon gefunden. Schließen Sie ein Mikrofon an und klicken Sie "
        "auf \u201eAktualisieren\u201c."
    ),
    "error.microphone_open_failed": (
        "Das Mikrofon konnte nicht geöffnet werden. Stellen Sie sicher, dass kein anderes "
        "Programm es exklusiv verwendet und dass Windows Desktop-Apps den Zugriff auf das "
        "Mikrofon erlaubt (Einstellungen \u203a Datenschutz und Sicherheit \u203a Mikrofon)."
    ),
    "error.audio_backend_unavailable": (
        "Audioaufnahme ist auf diesem Computer nicht verfügbar. Details wurden in die "
        "Protokolldatei geschrieben:\n{log}"
    ),
    "error.engine_blocked_by_policy": (
        "Windows hat die Spracherkennung blockiert (Smart App Control oder eine andere "
        "Richtlinie zur Anwendungssteuerung). Siehe \u201eTroubleshooting\u201c in der Dokumentation."
    ),
    "error.engine_import_failed": (
        "Die Spracherkennung konnte nicht gestartet werden. Die Installation ist "
        "möglicherweise unvollständig. Details wurden in die Protokolldatei geschrieben:\n{log}"
    ),
    "error.model_cache_unwritable": (
        "In den Ordner für das Sprachmodell kann nicht geschrieben werden: {detail}"
    ),
    "error.no_disk_space": (
        "Es ist nicht genügend freier Speicherplatz vorhanden, um das Sprachmodell "
        "herunterzuladen (etwa 1 GB wird benötigt)."
    ),
    "error.model_download_failed": (
        "Das Sprachmodell konnte nicht heruntergeladen werden. Eine Internetverbindung "
        "wird nur beim ersten Mal benötigt. Prüfen Sie die Verbindung und versuchen Sie es erneut."
    ),
    "error.model_load_failed": (
        "Das Sprachmodell konnte nicht geladen werden. Details wurden in die "
        "Protokolldatei geschrieben:\n{log}"
    ),
    "error.model_not_loaded": "Das Sprachmodell ist noch nicht geladen.",
    "error.directory_missing": "Der Speicherordner ist nicht vorhanden: {detail}",
    "error.directory_invalid": "Der Speicherort ist kein Ordner: {detail}",
    "error.directory_not_writable": (
        "In den Speicherordner kann nicht geschrieben werden. Wählen Sie einen anderen "
        "Ordner. Ihr Transkript ist noch vorhanden und nicht verloren."
    ),
    "error.export_failed": (
        "Die Datei konnte nicht gespeichert werden. Ihr Transkript ist noch vorhanden: "
        "Mit \u201eSpeichern\u201c versuchen Sie es erneut, mit \u201eSpeichern unter\u2026\u201c "
        "wählen Sie einen anderen Ort."
    ),
    "error.unknown_format": "Das ausgewählte Dateiformat wird nicht unterstützt.",
    "error.pdf_font_missing": (
        "Es wurde keine Schriftart gefunden, die alle Zeichen unterstützt, daher wurde "
        "kein PDF erstellt. Wählen Sie ein anderes Format oder lesen Sie "
        "\u201eTroubleshooting\u201c in der Dokumentation."
    ),
    # Model and device
    "model.idle": "Sprachmodell: nicht geladen",
    "model.checking": "Sprachmodell wird geprüft\u2026",
    "model.downloading": "Sprachmodell wird heruntergeladen (nur beim ersten Start)\u2026",
    "model.downloading.progress": "Sprachmodell wird heruntergeladen\u2026 {megabytes} MB",
    "model.initializing": "Sprachmodell wird geladen\u2026",
    "model.ready": "Modell: {model} \u00b7 {device}",
    "model.failed": "Sprachmodell nicht verfügbar",
    "model.retry": "Erneut versuchen",
    "model.tip": "Sprache wird auf diesem Computer erkannt. Es wird kein Audio versendet.",
    "device.gpu": "GPU (NVIDIA CUDA, {compute_type})",
    "device.cpu": "CPU ({compute_type})",
    "device.reason.cpu_selected": (
        "Der Prozessor wird verwendet, weil er in den Einstellungen ausgewählt ist."
    ),
    "device.reason.cuda_unavailable": (
        "Der Prozessor wird verwendet, weil keine kompatible NVIDIA-Grafikkarte gefunden wurde."
    ),
    "device.reason.cuda_unsupported_compute_type": (
        "Der Prozessor wird verwendet, weil die Grafikkarte kein geeignetes Zahlenformat unterstützt."
    ),
    "device.reason.cuda_init_failed": (
        "Der Prozessor wird verwendet, weil die Grafikkarte nicht initialisiert werden "
        "konnte. Möglicherweise fehlen die NVIDIA-Bibliotheken (cuBLAS, cuDNN)."
    ),
    "device.reason.cuda_out_of_memory": (
        "Der Prozessor wird verwendet, weil der Speicher der Grafikkarte nicht ausreichte."
    ),
    "device.reason.cuda_runtime_error": (
        "Der Prozessor wird verwendet, weil die Grafikkarte einen Fehler gemeldet hat."
    ),
    # Dialogs
    "dialog.unsaved.title": "Nicht gespeichertes Transkript",
    "dialog.unsaved.text": (
        "Das aktuelle Transkript wurde nicht gespeichert. Beim Start einer neuen Aufnahme "
        "wird es verworfen."
    ),
    "dialog.recover.title": "Nicht gespeicherte Sitzungen wiederherstellen",
    "dialog.recover.text": (
        "Beim letzten Programmlauf wurden {count} Sitzung(en) nicht gespeichert. "
        "Möchten Sie sie jetzt wiederherstellen und speichern?"
    ),
    "dialog.recover.recover": "Wiederherstellen und speichern",
    "dialog.recover.discard": "Verwerfen",
    "dialog.recover.later": "Später entscheiden",
    "dialog.close.title": "Aufnahme läuft",
    "dialog.close.recording": (
        "Eine Aufnahme läuft. Soll sie vor dem Schließen gestoppt und das Transkript "
        "gespeichert werden?"
    ),
    "dialog.close.stop_save": "Stoppen, speichern und schließen",
    "dialog.close.keep": "Weiter aufnehmen",
    "dialog.close.wait": (
        "Das Transkript wird fertiggestellt. Das Fenster schließt sich nach dem Speichern\u2026"
    ),
    "dialog.close.unsaved": (
        "Das Transkript wurde nicht gespeichert. Wenn Sie jetzt schließen, wird es beim "
        "nächsten Start zur Wiederherstellung angeboten."
    ),
    # Settings
    "settings.title": "Einstellungen",
    "settings.tab.general": "Allgemein",
    "settings.tab.recording": "Aufnahme",
    "settings.tab.system": "System",
    "settings.save": "Speichern",
    "settings.cancel": "Abbrechen",
    "settings.defaults": "Standardwerte",
    "settings.defaults.tip": (
        "Füllt das Formular mit den Standardwerten. Es ändert sich nichts, bevor Sie speichern."
    ),
    "settings.saved": "Einstellungen gespeichert.",
    "settings.ui_language": "Sprache der Oberfläche:",
    "settings.ui_language.hint": (
        "Ändert nur die Sprache dieser Anwendung. Erkannt wird die Sprache, "
        "die tatsächlich gesprochen wird."
    ),
    "settings.folder": "Speicherordner:",
    "settings.folder.hint": (
        "Transkripte werden hier automatisch gespeichert, wenn eine Aufnahme endet."
    ),
    "settings.folder.error.relative": (
        "Geben Sie einen vollständigen Pfad ein, zum Beispiel C:\\Users\\Name\\Documents\\Transkripte."
    ),
    "settings.folder.create.title": "Ordner erstellen",
    "settings.folder.create.text": "Dieser Ordner ist nicht vorhanden:\n{path}\n\nSoll er erstellt werden?",
    "settings.browse": "Durchsuchen\u2026",
    "settings.format": "Dateiformat:",
    "settings.template": "Dateiname:",
    "settings.template.hint": "Verfügbare Platzhalter: {placeholders}",
    "settings.template.preview": "Vorschau: {name}",
    "settings.template.error.empty": "Der Dateiname darf nicht leer sein.",
    "settings.template.error.unbalanced": "Eine geschweifte Klammer ist nicht geschlossen.",
    "settings.template.error.unknown": "Unbekannter Platzhalter: {name}",
    "settings.documents": "Dokumente:",
    "settings.timestamps": "Zeit am Anfang jeder Transkriptzeile anzeigen",
    "settings.open_after_save": "Dokument nach dem Speichern öffnen",
    "settings.microphone": "Mikrofon:",
    "settings.silence": "Pause, die ein Segment beendet:",
    "settings.silence.hint": (
        "Stille dieser Länge beendet das aktuelle Segment. Kürzere Pausen bleiben darin "
        "enthalten. Erhöhen Sie den Wert, wenn Sätze zu oft geteilt werden."
    ),
    "settings.threshold": "Sprachempfindlichkeit:",
    "settings.threshold.hint": (
        "Niedrigere Werte erfassen leise Sprache, aber auch mehr Hintergrundgeräusche. "
        "Höhere Werte ignorieren mehr Geräusche."
    ),
    "settings.min_speech": "Kürzeste Sprache:",
    "settings.min_speech.hint": "Kürzere Geräusche, etwa ein Klicken, werden ignoriert.",
    "settings.max_segment": "Längstes Segment:",
    "settings.max_segment.hint": (
        "Durchgehende Sprache wird bei der nächsten kurzen Pause geteilt, wenn sie sich "
        "dieser Länge nähert."
    ),
    "settings.pre_roll": "Vorlauf:",
    "settings.pre_roll.hint": (
        "Audio, das vor erkannter Sprache behalten wird, damit die erste Silbe nicht fehlt."
    ),
    "settings.post_roll": "Nachlauf:",
    "settings.post_roll.hint": (
        "Audio, das nach dem Ende der Sprache behalten wird, damit die letzte Silbe nicht fehlt."
    ),
    "settings.debugging": "Fehlersuche:",
    "settings.retain_audio": "Rohaudio jeder Sitzung behalten",
    "settings.retain_audio.hint": (
        "Standardmäßig aus. Wenn aktiviert, wird das Mikrofonaudio jeder Sitzung als "
        "WAV-Datei auf diesem Computer gespeichert, bis Sie es löschen."
    ),
    "settings.open_audio_folder": "Audioordner öffnen",
    "settings.device": "Rechengerät:",
    "settings.device.hint": (
        "\u201eAutomatisch\u201c verwendet eine funktionierende NVIDIA-Grafikkarte und sonst den Prozessor."
    ),
    "settings.device.auto": "Automatisch (empfohlen)",
    "settings.device.cuda": "Grafikkarte (NVIDIA CUDA)",
    "settings.device.cpu": "Prozessor (CPU)",
    "settings.device.in_use": "Derzeit verwendet:",
    "settings.model": "Sprachmodell:",
    "settings.model.cached": "Whisper {model} \u00b7 auf diesem Computer gespeichert ({megabytes} MB)",
    "settings.model.missing": "Whisper {model} \u00b7 noch nicht heruntergeladen",
    "settings.model.location": "Speicherort des Modells:",
    "settings.model.open": "Modellordner öffnen",
    "settings.logs": "Protokolldateien:",
    "settings.logs.open": "Protokollordner öffnen",
    "settings.logs.hint": (
        "Protokolle enthalten nur technische Details, niemals Audio oder Transkripttext."
    ),
    "settings.privacy": "Datenschutz:",
    "settings.privacy.text": (
        "Audio und Transkripte bleiben auf diesem Computer. Das Internet wird nur einmal "
        "genutzt, um das Sprachmodell herunterzuladen."
    ),
}
