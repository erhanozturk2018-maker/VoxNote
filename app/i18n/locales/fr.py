"""French interface strings."""

STRINGS = {
    "app.version": "Version {version}",
    "unit.ms": "ms",
    "unit.s": "s",
    # Main window
    "main.settings": "Paramètres",
    "main.settings.tip": "Ouvrir les paramètres ({shortcut})",
    "main.start": "\u25cf  Démarrer l'enregistrement",
    "main.start.tip": "Démarrer un nouvel enregistrement ({shortcut})",
    "main.start.tip.model": "Disponible dès que le modèle vocal est chargé",
    "main.start.tip.busy": "Disponible lorsque la session en cours est terminée",
    "main.stop": "\u25a0  Arrêter l'enregistrement",
    "main.stop.tip": "Arrêter, terminer la transcription et l'enregistrer ({shortcut})",
    "main.microphone": "Microphone :",
    "main.microphone.default": "Microphone par défaut du système",
    "main.refresh": "Actualiser",
    "main.refresh.tip": "Rechercher les microphones récemment connectés",
    "main.refresh.done": "Microphones trouvés : {count}",
    "main.level": "Niveau d'entrée :",
    "main.elapsed": "Durée d'enregistrement écoulée",
    "main.status": "État : {status}",
    "main.transcript": "Transcription",
    "main.transcript.placeholder": (
        "Vos paroles apparaissent ici pendant que vous parlez. "
        "Cliquez sur \u00ab Démarrer l'enregistrement \u00bb pour commencer."
    ),
    "main.languages": "Langues : {languages}",
    "main.languages.none": "aucune détectée pour l'instant",
    "main.copy": "Copier le texte",
    "main.copy.tip": "Copier le texte de la transcription dans le presse-papiers ({shortcut})",
    "main.copy.done": "Transcription copiée dans le presse-papiers.",
    "main.output": "Sortie",
    "main.folder": "Dossier d'enregistrement :",
    "main.folder.change": "Modifier\u2026",
    "main.folder.change.tip": "Choisir où les transcriptions sont enregistrées",
    "main.folder.dialog": "Choisir le dossier des transcriptions enregistrées",
    "main.folder.changed": "Dossier d'enregistrement modifié.",
    "main.format": "Format :",
    "main.filename_hint": "Nom du fichier pour cette session : {name}",
    "main.open_file": "Ouvrir le fichier",
    "main.open_folder": "Ouvrir le dossier",
    "main.open_folder.tip": "Afficher le fichier enregistré dans son dossier ({shortcut})",
    "main.save": "Enregistrer",
    "main.save.tip": "Enregistrer la transcription dans le dossier d'enregistrement",
    "main.save_as": "Enregistrer sous\u2026",
    "main.save_as.tip": "Enregistrer la transcription ailleurs ou dans un autre format ({shortcut})",
    "main.save_as.dialog": "Enregistrer la transcription sous",
    "main.dismiss": "Fermer ce message",
    # States
    "state.ready": "Prêt",
    "state.recording": "Enregistrement",
    "state.recording.speech": "Enregistrement \u00b7 parole détectée",
    "state.processing": "Traitement de la parole",
    "state.processing.pending": "Traitement de la parole \u00b7 {seconds} s restantes",
    "state.saving": "Enregistrement du fichier",
    "state.completed": "Terminé",
    "state.error": "Erreur",
    # Results and notices
    "result.saved": "Enregistré : {path}",
    "result.file_missing": (
        "Le fichier enregistré ne se trouve plus à son emplacement. "
        "Utilisez \u00ab Enregistrer sous\u2026 \u00bb pour l'enregistrer à nouveau."
    ),
    "result.open_failed": "Aucune application n'est disponible pour ouvrir {path}.",
    "notice.no_speech": "Aucune parole n'a été détectée ; aucun fichier n'a donc été créé.",
    "notice.microphone_disconnected": (
        "Le microphone a cessé de fournir du son ; l'enregistrement a donc été arrêté. "
        "Tout ce qui a été dit auparavant est conservé."
    ),
    "notice.backlog_limit": (
        "La reconnaissance vocale n'arrivait plus à suivre ; l'enregistrement a donc été "
        "arrêté. Tout ce qui a été enregistré est en cours de transcription."
    ),
    "notice.silent_input": (
        "Le microphone ne fournit que du silence. Vérifiez qu'il n'est pas coupé et que "
        "Windows autorise les applications de bureau à utiliser le microphone "
        "(Paramètres \u203a Confidentialité et sécurité \u203a Microphone)."
    ),
    "notice.audio_dropped": (
        "L'ordinateur était trop sollicité et un court passage audio a été perdu."
    ),
    "notice.transcription_failed": (
        "Une partie de l'enregistrement n'a pas pu être transcrite et a été ignorée. "
        "Les détails se trouvent dans le fichier journal."
    ),
    "notice.gpu_fallback": (
        "La carte graphique ne peut plus être utilisée. La reconnaissance se poursuit "
        "sur le processeur et sera plus lente."
    ),
    "notice.session_recovered": "Une session non enregistrée a été récupérée.",
    # Errors
    "error.unknown": (
        "Un problème est survenu. Les détails ont été écrits dans le fichier journal :\n{log}"
    ),
    "error.settings_save_failed": "Les paramètres n'ont pas pu être enregistrés : {detail}",
    "error.no_microphone": (
        "Aucun microphone n'a été trouvé. Connectez un microphone et cliquez sur "
        "\u00ab Actualiser \u00bb."
    ),
    "error.microphone_open_failed": (
        "Le microphone n'a pas pu être ouvert. Vérifiez qu'aucun autre programme ne "
        "l'utilise en mode exclusif et que Windows autorise les applications de bureau à "
        "utiliser le microphone (Paramètres \u203a Confidentialité et sécurité \u203a Microphone)."
    ),
    "error.audio_backend_unavailable": (
        "L'enregistrement audio n'est pas disponible sur cet ordinateur. Les détails ont "
        "été écrits dans le fichier journal :\n{log}"
    ),
    "error.engine_blocked_by_policy": (
        "Windows a bloqué le moteur de reconnaissance vocale (Smart App Control ou une "
        "autre stratégie de contrôle des applications). Consultez \u00ab Troubleshooting \u00bb "
        "dans la documentation."
    ),
    "error.engine_import_failed": (
        "Le moteur de reconnaissance vocale n'a pas pu démarrer. L'installation est "
        "peut-être incomplète. Les détails ont été écrits dans le fichier journal :\n{log}"
    ),
    "error.model_cache_unwritable": (
        "Impossible d'écrire dans le dossier du modèle vocal : {detail}"
    ),
    "error.no_disk_space": (
        "L'espace disque libre est insuffisant pour télécharger le modèle vocal "
        "(environ 1 Go est nécessaire)."
    ),
    "error.model_download_failed": (
        "Le modèle vocal n'a pas pu être téléchargé. Une connexion Internet n'est "
        "nécessaire que la première fois. Vérifiez la connexion et réessayez."
    ),
    "error.model_load_failed": (
        "Le modèle vocal n'a pas pu être chargé. Les détails ont été écrits dans le "
        "fichier journal :\n{log}"
    ),
    "error.model_not_loaded": "Le modèle vocal n'est pas encore chargé.",
    "error.directory_missing": "Le dossier d'enregistrement n'existe pas : {detail}",
    "error.directory_invalid": "L'emplacement d'enregistrement n'est pas un dossier : {detail}",
    "error.directory_not_writable": (
        "Impossible d'écrire dans le dossier d'enregistrement. Choisissez un autre "
        "dossier. Votre transcription est toujours là et n'a pas été perdue."
    ),
    "error.export_failed": (
        "Le fichier n'a pas pu être enregistré. Votre transcription est toujours là : "
        "utilisez \u00ab Enregistrer \u00bb pour réessayer ou \u00ab Enregistrer sous\u2026 \u00bb "
        "pour choisir un autre emplacement."
    ),
    "error.unknown_format": "Le format de fichier sélectionné n'est pas pris en charge.",
    "error.pdf_font_missing": (
        "Aucune police prenant en charge tous les caractères n'a été trouvée ; le PDF "
        "n'a donc pas été créé. Choisissez un autre format ou consultez "
        "\u00ab Troubleshooting \u00bb dans la documentation."
    ),
    # Model and device
    "model.idle": "Modèle vocal : non chargé",
    "model.checking": "Vérification du modèle vocal\u2026",
    "model.downloading": "Téléchargement du modèle vocal (premier lancement uniquement)\u2026",
    "model.downloading.progress": "Téléchargement du modèle vocal\u2026 {megabytes} Mo",
    "model.initializing": "Chargement du modèle vocal\u2026",
    "model.ready": "Modèle : {model} \u00b7 {device}",
    "model.failed": "Modèle vocal indisponible",
    "model.retry": "Réessayer",
    "model.tip": "La parole est reconnue sur cet ordinateur. Aucun son n'est envoyé ailleurs.",
    "device.gpu": "GPU (NVIDIA CUDA, {compute_type})",
    "device.cpu": "Processeur ({compute_type})",
    "device.reason.cpu_selected": (
        "Le processeur est utilisé parce qu'il est sélectionné dans les paramètres."
    ),
    "device.reason.cuda_unavailable": (
        "Le processeur est utilisé parce qu'aucune carte graphique NVIDIA compatible n'a été trouvée."
    ),
    "device.reason.cuda_unsupported_compute_type": (
        "Le processeur est utilisé parce que la carte graphique ne prend pas en charge "
        "un format numérique adapté."
    ),
    "device.reason.cuda_init_failed": (
        "Le processeur est utilisé parce que la carte graphique n'a pas pu être "
        "initialisée. Les bibliothèques NVIDIA (cuBLAS, cuDNN) sont peut-être absentes."
    ),
    "device.reason.cuda_out_of_memory": (
        "Le processeur est utilisé parce que la mémoire de la carte graphique était insuffisante."
    ),
    "device.reason.cuda_runtime_error": (
        "Le processeur est utilisé parce que la carte graphique a signalé une erreur."
    ),
    # Dialogs
    "dialog.unsaved.title": "Transcription non enregistrée",
    "dialog.unsaved.text": (
        "La transcription actuelle n'a pas été enregistrée. Démarrer un nouvel "
        "enregistrement la supprimera."
    ),
    "dialog.recover.title": "Récupérer les sessions non enregistrées",
    "dialog.recover.text": (
        "{count} session(s) n'ont pas été enregistrées lors de la dernière utilisation. "
        "Voulez-vous les récupérer et les enregistrer maintenant ?"
    ),
    "dialog.recover.recover": "Récupérer et enregistrer",
    "dialog.recover.discard": "Supprimer",
    "dialog.recover.later": "Décider plus tard",
    "dialog.close.title": "Enregistrement en cours",
    "dialog.close.recording": (
        "Un enregistrement est en cours. L'arrêter et enregistrer la transcription "
        "avant de fermer ?"
    ),
    "dialog.close.stop_save": "Arrêter, enregistrer et fermer",
    "dialog.close.keep": "Continuer l'enregistrement",
    "dialog.close.wait": (
        "Finalisation de la transcription. La fenêtre se fermera une fois le fichier enregistré\u2026"
    ),
    "dialog.close.unsaved": (
        "La transcription n'a pas été enregistrée. Si vous fermez maintenant, sa "
        "récupération sera proposée au prochain démarrage."
    ),
    # Settings
    "settings.title": "Paramètres",
    "settings.tab.general": "Général",
    "settings.tab.recording": "Enregistrement",
    "settings.tab.system": "Système",
    "settings.save": "Enregistrer",
    "settings.cancel": "Annuler",
    "settings.defaults": "Valeurs par défaut",
    "settings.defaults.tip": (
        "Remplit le formulaire avec les valeurs par défaut. Rien ne change tant que "
        "vous n'enregistrez pas."
    ),
    "settings.saved": "Paramètres enregistrés.",
    "settings.ui_language": "Langue de l'interface :",
    "settings.ui_language.hint": (
        "Modifie uniquement la langue de cette application. La parole est reconnue "
        "dans la langue réellement parlée."
    ),
    "settings.folder": "Dossier d'enregistrement :",
    "settings.folder.hint": (
        "Les transcriptions y sont enregistrées automatiquement à la fin d'un enregistrement."
    ),
    "settings.folder.error.relative": (
        "Saisissez un chemin complet, par exemple C:\\Users\\Nom\\Documents\\Transcriptions."
    ),
    "settings.folder.create.title": "Créer le dossier",
    "settings.folder.create.text": "Ce dossier n'existe pas :\n{path}\n\nLe créer ?",
    "settings.browse": "Parcourir\u2026",
    "settings.format": "Format de fichier :",
    "settings.template": "Nom du fichier :",
    "settings.template.hint": "Variables disponibles : {placeholders}",
    "settings.template.preview": "Aperçu : {name}",
    "settings.template.error.empty": "Le nom du fichier ne doit pas être vide.",
    "settings.template.error.unbalanced": "Une accolade n'est pas fermée.",
    "settings.template.error.unknown": "Variable inconnue : {name}",
    "settings.documents": "Documents :",
    "settings.timestamps": "Afficher l'heure au début de chaque ligne de transcription",
    "settings.open_after_save": "Ouvrir le document après son enregistrement",
    "settings.microphone": "Microphone :",
    "settings.silence": "Pause qui termine un segment :",
    "settings.silence.hint": (
        "Un silence de cette durée termine le segment en cours. Les pauses plus courtes "
        "y restent incluses. Augmentez la valeur si les phrases sont trop souvent coupées."
    ),
    "settings.threshold": "Sensibilité à la parole :",
    "settings.threshold.hint": (
        "Les valeurs basses captent la parole faible, mais aussi davantage de bruit de "
        "fond. Les valeurs élevées ignorent davantage de bruit."
    ),
    "settings.min_speech": "Parole la plus courte :",
    "settings.min_speech.hint": "Les sons plus courts, comme les clics, sont ignorés.",
    "settings.max_segment": "Segment le plus long :",
    "settings.max_segment.hint": (
        "La parole continue est coupée à la prochaine courte pause lorsqu'elle approche "
        "de cette durée."
    ),
    "settings.pre_roll": "Marge avant :",
    "settings.pre_roll.hint": (
        "Audio conservé avant la détection de la parole, pour ne pas couper la première syllabe."
    ),
    "settings.post_roll": "Marge après :",
    "settings.post_roll.hint": (
        "Audio conservé après la fin de la parole, pour ne pas couper la dernière syllabe."
    ),
    "settings.debugging": "Dépannage :",
    "settings.retain_audio": "Conserver l'audio brut de chaque session",
    "settings.retain_audio.hint": (
        "Désactivé par défaut. Lorsqu'il est activé, l'audio du microphone de chaque "
        "session est stocké sur cet ordinateur au format WAV jusqu'à ce que vous le supprimiez."
    ),
    "settings.open_audio_folder": "Ouvrir le dossier audio",
    "settings.device": "Périphérique de calcul :",
    "settings.device.hint": (
        "\u00ab Automatique \u00bb utilise une carte graphique NVIDIA si elle fonctionne, "
        "sinon le processeur."
    ),
    "settings.device.auto": "Automatique (recommandé)",
    "settings.device.cuda": "Carte graphique (NVIDIA CUDA)",
    "settings.device.cpu": "Processeur (CPU)",
    "settings.device.in_use": "Actuellement utilisé :",
    "settings.model": "Modèle vocal :",
    "settings.model.cached": "Whisper {model} \u00b7 stocké sur cet ordinateur ({megabytes} Mo)",
    "settings.model.missing": "Whisper {model} \u00b7 pas encore téléchargé",
    "settings.model.location": "Emplacement du modèle :",
    "settings.model.open": "Ouvrir le dossier du modèle",
    "settings.logs": "Fichiers journaux :",
    "settings.logs.open": "Ouvrir le dossier des journaux",
    "settings.logs.hint": (
        "Les journaux ne contiennent que des détails techniques, jamais d'audio ni de "
        "texte transcrit."
    ),
    "settings.privacy": "Confidentialité :",
    "settings.privacy.text": (
        "L'audio et les transcriptions restent sur cet ordinateur. Internet n'est "
        "utilisé qu'une seule fois, pour télécharger le modèle vocal."
    ),
}
