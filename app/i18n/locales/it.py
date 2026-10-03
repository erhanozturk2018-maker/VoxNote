"""Italian interface strings."""

STRINGS = {
    "app.version": "Versione {version}",
    "unit.ms": "ms",
    "unit.s": "s",
    # Main window
    "main.settings": "Impostazioni",
    "main.settings.tip": "Apri le impostazioni ({shortcut})",
    "main.start": "\u25cf  Avvia registrazione",
    "main.start.tip": "Avvia una nuova registrazione ({shortcut})",
    "main.start.tip.model": "Disponibile non appena il modello vocale è stato caricato",
    "main.start.tip.busy": "Disponibile al termine della sessione in corso",
    "main.stop": "\u25a0  Ferma registrazione",
    "main.stop.tip": "Ferma, completa la trascrizione e salvala ({shortcut})",
    "main.microphone": "Microfono:",
    "main.microphone.default": "Microfono predefinito del sistema",
    "main.refresh": "Aggiorna",
    "main.refresh.tip": "Cerca i microfoni collegati di recente",
    "main.refresh.done": "Microfoni trovati: {count}",
    "main.level": "Livello di ingresso:",
    "main.elapsed": "Tempo di registrazione trascorso",
    "main.status": "Stato: {status}",
    "main.transcript": "Trascrizione",
    "main.transcript.placeholder": (
        "Le tue parole compaiono qui mentre parli. "
        "Premi \u00abAvvia registrazione\u00bb per iniziare."
    ),
    "main.languages": "Lingue: {languages}",
    "main.languages.none": "nessuna rilevata finora",
    "main.copy": "Copia testo",
    "main.copy.tip": "Copia il testo della trascrizione negli appunti ({shortcut})",
    "main.copy.done": "Trascrizione copiata negli appunti.",
    "main.output": "Output",
    "main.folder": "Cartella di salvataggio:",
    "main.folder.change": "Cambia\u2026",
    "main.folder.change.tip": "Scegli dove salvare le trascrizioni",
    "main.folder.dialog": "Scegli la cartella per le trascrizioni salvate",
    "main.folder.changed": "Cartella di salvataggio modificata.",
    "main.format": "Formato:",
    "main.filename_hint": "Nome del file per questa sessione: {name}",
    "main.filename_example": "Esempio di nome del file: {name}",
    "main.open_file": "Apri file",
    "main.open_folder": "Apri cartella",
    "main.open_folder.tip": "Mostra il file salvato nella sua cartella ({shortcut})",
    "main.save": "Salva",
    "main.save.tip": "Salva la trascrizione nella cartella di salvataggio",
    "main.save_as": "Salva con nome\u2026",
    "main.save_as.tip": "Salva la trascrizione in un'altra posizione o in un altro formato ({shortcut})",
    "main.save_as.dialog": "Salva la trascrizione con nome",
    "main.dismiss": "Chiudi questo messaggio",
    # States
    "state.ready": "Pronto",
    "state.recording": "Registrazione",
    "state.recording.speech": "Registrazione \u00b7 voce rilevata",
    "state.processing": "Elaborazione del parlato",
    "state.processing.pending": "Elaborazione del parlato \u00b7 {seconds} s rimanenti",
    "state.saving": "Salvataggio del file",
    "state.completed": "Completato",
    "state.error": "Errore",
    # Results and notices
    "result.saved": "Salvato: {path}",
    "result.file_missing": (
        "Il file salvato non si trova più nella sua posizione. "
        "Usa \u00abSalva con nome\u2026\u00bb per salvarlo di nuovo."
    ),
    "result.open_failed": "Nessuna applicazione disponibile per aprire {path}.",
    "notice.no_speech": "Non è stato rilevato alcun parlato, quindi non è stato creato alcun file.",
    "notice.microphone_disconnected": (
        "Il microfono ha smesso di fornire audio, quindi la registrazione è stata "
        "fermata. Tutto ciò che è stato detto prima viene conservato."
    ),
    "notice.backlog_limit": (
        "Il riconoscimento vocale non riusciva a tenere il passo, quindi la "
        "registrazione è stata fermata. Tutto ciò che è stato registrato viene trascritto."
    ),
    "notice.silent_input": (
        "Il microfono fornisce solo silenzio. Controlla che non sia disattivato e che "
        "Windows consenta alle app desktop di usare il microfono "
        "(Impostazioni \u203a Privacy e sicurezza \u203a Microfono)."
    ),
    "notice.audio_dropped": (
        "Il computer era troppo occupato e un breve tratto di audio è andato perso."
    ),
    "notice.transcription_failed": (
        "Una parte della registrazione non è stata trascritta ed è stata saltata. "
        "I dettagli sono nel file di log."
    ),
    "notice.gpu_fallback": (
        "La scheda grafica non può più essere usata. Il riconoscimento continua sul "
        "processore e sarà più lento."
    ),
    "notice.session_recovered": "È stata recuperata una sessione non salvata.",
    # Errors
    "error.unknown": "Si è verificato un problema. I dettagli sono stati scritti nel file di log:\n{log}",
    "error.settings_save_failed": "Impossibile salvare le impostazioni: {detail}",
    "error.no_microphone": (
        "Nessun microfono trovato. Collega un microfono e premi \u00abAggiorna\u00bb."
    ),
    "error.microphone_open_failed": (
        "Impossibile aprire il microfono. Assicurati che nessun altro programma lo usi "
        "in modo esclusivo e che Windows consenta alle app desktop di usare il microfono "
        "(Impostazioni \u203a Privacy e sicurezza \u203a Microfono)."
    ),
    "error.audio_backend_unavailable": (
        "La registrazione audio non è disponibile su questo computer. I dettagli sono "
        "stati scritti nel file di log:\n{log}"
    ),
    "error.engine_blocked_by_policy": (
        "Windows ha bloccato il motore di riconoscimento vocale (Smart App Control o "
        "un altro criterio di controllo delle applicazioni). Vedi \u00abTroubleshooting\u00bb "
        "nella documentazione."
    ),
    "error.engine_import_failed": (
        "Impossibile avviare il motore di riconoscimento vocale. L'installazione "
        "potrebbe essere incompleta. I dettagli sono stati scritti nel file di log:\n{log}"
    ),
    "error.model_cache_unwritable": (
        "Impossibile scrivere nella cartella del modello vocale: {detail}"
    ),
    "error.no_disk_space": (
        "Spazio libero su disco insufficiente per scaricare il modello vocale "
        "(serve circa 1 GB)."
    ),
    "error.model_download_failed": (
        "Impossibile scaricare il modello vocale. La connessione a Internet serve solo "
        "la prima volta. Controlla la connessione e riprova."
    ),
    "error.model_load_failed": (
        "Impossibile caricare il modello vocale. I dettagli sono stati scritti nel file di log:\n{log}"
    ),
    "error.model_not_loaded": "Il modello vocale non è ancora stato caricato.",
    "error.directory_missing": "La cartella di salvataggio non esiste: {detail}",
    "error.directory_invalid": "La posizione di salvataggio non è una cartella: {detail}",
    "error.directory_not_writable": (
        "Impossibile scrivere nella cartella di salvataggio. Scegli un'altra cartella. "
        "La trascrizione è ancora qui e non è andata persa."
    ),
    "error.export_failed": (
        "Impossibile salvare il file. La trascrizione è ancora qui: usa \u00abSalva\u00bb "
        "per riprovare o \u00abSalva con nome\u2026\u00bb per scegliere un'altra posizione."
    ),
    "error.unknown_format": "Il formato di file selezionato non è supportato.",
    "error.pdf_font_missing": (
        "Non è stato trovato alcun carattere che supporti tutti i simboli, quindi il "
        "PDF non è stato creato. Scegli un altro formato o vedi \u00abTroubleshooting\u00bb "
        "nella documentazione."
    ),
    # Model and device
    "model.idle": "Modello vocale: non caricato",
    "model.checking": "Verifica del modello vocale\u2026",
    "model.downloading": "Download del modello vocale (solo al primo avvio)\u2026",
    "model.downloading.progress": "Download del modello vocale\u2026 {megabytes} MB",
    "model.initializing": "Caricamento del modello vocale\u2026",
    "model.ready": "Modello: {model} \u00b7 {device}",
    "model.failed": "Modello vocale non disponibile",
    "model.retry": "Riprova",
    "model.tip": "Il parlato viene riconosciuto su questo computer. Nessun audio viene inviato altrove.",
    "device.gpu": "GPU (NVIDIA CUDA, {compute_type})",
    "device.cpu": "CPU ({compute_type})",
    "device.reason.cpu_selected": (
        "Viene usato il processore perché è selezionato nelle impostazioni."
    ),
    "device.reason.cuda_unavailable": (
        "Viene usato il processore perché non è stata trovata una scheda grafica NVIDIA compatibile."
    ),
    "device.reason.cuda_unsupported_compute_type": (
        "Viene usato il processore perché la scheda grafica non supporta un formato "
        "numerico adatto."
    ),
    "device.reason.cuda_init_failed": (
        "Viene usato il processore perché non è stato possibile inizializzare la scheda "
        "grafica. Le librerie NVIDIA (cuBLAS, cuDNN) potrebbero mancare."
    ),
    "device.reason.cuda_out_of_memory": (
        "Viene usato il processore perché la memoria della scheda grafica non era sufficiente."
    ),
    "device.reason.cuda_runtime_error": (
        "Viene usato il processore perché la scheda grafica ha segnalato un errore."
    ),
    # Dialogs
    "dialog.unsaved.title": "Trascrizione non salvata",
    "dialog.unsaved.text": (
        "La trascrizione attuale non è stata salvata. Avviando una nuova registrazione "
        "verrà eliminata."
    ),
    "dialog.recover.title": "Recupera le sessioni non salvate",
    "dialog.recover.text": (
        "{count} sessione/i non sono state salvate all'ultimo utilizzo dell'applicazione. "
        "Vuoi recuperarle e salvarle ora?"
    ),
    "dialog.recover.recover": "Recupera e salva",
    "dialog.recover.discard": "Elimina",
    "dialog.recover.later": "Decidi più tardi",
    "dialog.close.title": "Registrazione in corso",
    "dialog.close.recording": (
        "È in corso una registrazione. Fermarla e salvare la trascrizione prima di chiudere?"
    ),
    "dialog.close.stop_save": "Ferma, salva e chiudi",
    "dialog.close.keep": "Continua a registrare",
    "dialog.close.wait": (
        "Completamento della trascrizione. La finestra si chiuderà dopo il salvataggio\u2026"
    ),
    "dialog.close.unsaved": (
        "La trascrizione non è stata salvata. Se chiudi ora, al prossimo avvio verrà "
        "proposto di recuperarla."
    ),
    # Settings
    "settings.title": "Impostazioni",
    "settings.tab.general": "Generale",
    "settings.tab.recording": "Registrazione",
    "settings.tab.system": "Sistema",
    "settings.save": "Salva",
    "settings.cancel": "Annulla",
    "settings.defaults": "Ripristina predefiniti",
    "settings.defaults.tip": (
        "Compila il modulo con i valori predefiniti. Non cambia nulla finché non salvi."
    ),
    "settings.saved": "Impostazioni salvate.",
    "settings.ui_language": "Lingua dell'interfaccia:",
    "settings.ui_language.hint": (
        "Cambia solo la lingua di questa applicazione. Il parlato viene riconosciuto "
        "nella lingua effettivamente parlata."
    ),
    "settings.folder": "Cartella di salvataggio:",
    "settings.folder.hint": (
        "Le trascrizioni vengono salvate qui automaticamente al termine di una registrazione."
    ),
    "settings.folder.error.relative": (
        "Inserisci un percorso completo, ad esempio C:\\Users\\Nome\\Documents\\Trascrizioni."
    ),
    "settings.folder.create.title": "Crea cartella",
    "settings.folder.create.text": "Questa cartella non esiste:\n{path}\n\nCrearla?",
    "settings.browse": "Sfoglia\u2026",
    "settings.format": "Formato del file:",
    "settings.template": "Nome del file:",
    "settings.template.hint": "Segnaposto disponibili: {placeholders}",
    "settings.template.preview": "Anteprima: {name}",
    "settings.template.error.empty": "Il nome del file non può essere vuoto.",
    "settings.template.error.unbalanced": "Una parentesi graffa non è chiusa.",
    "settings.template.error.unknown": "Segnaposto sconosciuto: {name}",
    "settings.documents": "Documenti:",
    "settings.timestamps": "Mostra l'ora all'inizio di ogni riga della trascrizione",
    "settings.open_after_save": "Apri il documento dopo il salvataggio",
    "settings.microphone": "Microfono:",
    "settings.silence": "Pausa che chiude un segmento:",
    "settings.silence.hint": (
        "Un silenzio di questa durata chiude il segmento corrente. Le pause più brevi "
        "restano al suo interno. Aumenta il valore se le frasi vengono divise troppo spesso."
    ),
    "settings.threshold": "Sensibilità al parlato:",
    "settings.threshold.hint": (
        "Valori bassi colgono il parlato a basso volume ma anche più rumore di fondo. "
        "Valori alti ignorano più rumore."
    ),
    "settings.min_speech": "Parlato più breve:",
    "settings.min_speech.hint": "I suoni più brevi, come i clic, vengono ignorati.",
    "settings.max_segment": "Segmento più lungo:",
    "settings.max_segment.hint": (
        "Il parlato continuo viene diviso alla prossima breve pausa quando si avvicina "
        "a questa durata."
    ),
    "settings.pre_roll": "Margine iniziale:",
    "settings.pre_roll.hint": (
        "Audio conservato prima del rilevamento del parlato, per non tagliare la prima sillaba."
    ),
    "settings.post_roll": "Margine finale:",
    "settings.post_roll.hint": (
        "Audio conservato dopo la fine del parlato, per non tagliare l'ultima sillaba."
    ),
    "settings.debugging": "Risoluzione dei problemi:",
    "settings.retain_audio": "Conserva l'audio originale di ogni sessione",
    "settings.retain_audio.hint": (
        "Disattivato per impostazione predefinita. Se attivato, l'audio del microfono "
        "di ogni sessione viene salvato su questo computer come file WAV finché non lo elimini."
    ),
    "settings.open_audio_folder": "Apri cartella audio",
    "settings.device": "Dispositivo di elaborazione:",
    "settings.device.hint": (
        "\u00abAutomatico\u00bb usa una scheda grafica NVIDIA se funziona, altrimenti il processore."
    ),
    "settings.device.auto": "Automatico (consigliato)",
    "settings.device.cuda": "Scheda grafica (NVIDIA CUDA)",
    "settings.device.cpu": "Processore (CPU)",
    "settings.device.in_use": "Attualmente in uso:",
    "settings.model": "Modello vocale:",
    "settings.model.cached": "Whisper {model} \u00b7 salvato su questo computer ({megabytes} MB)",
    "settings.model.missing": "Whisper {model} \u00b7 non ancora scaricato",
    "settings.model.location": "Posizione del modello:",
    "settings.model.open": "Apri cartella del modello",
    "settings.logs": "File di log:",
    "settings.logs.open": "Apri cartella dei log",
    "settings.logs.hint": (
        "I log contengono solo dettagli tecnici, mai audio o testo trascritto."
    ),
    "settings.privacy": "Privacy:",
    "settings.privacy.text": (
        "Audio e trascrizioni restano su questo computer. Internet viene usato una "
        "sola volta, per scaricare il modello vocale."
    ),
}
