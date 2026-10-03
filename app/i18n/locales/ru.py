"""Russian interface strings."""

STRINGS = {
    "app.version": "Версия {version}",
    "unit.ms": "мс",
    "unit.s": "с",
    # Main window
    "main.settings": "Настройки",
    "main.settings.tip": "Открыть настройки ({shortcut})",
    "main.start": "\u25cf  Начать запись",
    "main.start.tip": "Начать новую запись ({shortcut})",
    "main.start.tip.model": "Будет доступно, как только загрузится речевая модель",
    "main.start.tip.busy": "Будет доступно после завершения текущего сеанса",
    "main.stop": "\u25a0  Остановить запись",
    "main.stop.tip": "Остановить, завершить расшифровку и сохранить её ({shortcut})",
    "main.microphone": "Микрофон:",
    "main.microphone.default": "Системный микрофон по умолчанию",
    "main.refresh": "Обновить",
    "main.refresh.tip": "Найти недавно подключённые микрофоны",
    "main.refresh.done": "Найдено микрофонов: {count}",
    "main.level": "Уровень входа:",
    "main.elapsed": "Прошедшее время записи",
    "main.status": "Состояние: {status}",
    "main.transcript": "Расшифровка",
    "main.transcript.placeholder": (
        "Ваши слова появляются здесь, пока вы говорите. "
        "Нажмите \u00abНачать запись\u00bb, чтобы начать."
    ),
    "main.languages": "Языки: {languages}",
    "main.languages.none": "пока не определены",
    "main.copy": "Копировать текст",
    "main.copy.tip": "Скопировать текст расшифровки в буфер обмена ({shortcut})",
    "main.copy.done": "Расшифровка скопирована в буфер обмена.",
    "main.output": "Результат",
    "main.folder": "Папка сохранения:",
    "main.folder.change": "Изменить\u2026",
    "main.folder.change.tip": "Выбрать, куда сохраняются расшифровки",
    "main.folder.dialog": "Выберите папку для сохранения расшифровок",
    "main.folder.changed": "Папка сохранения изменена.",
    "main.format": "Формат:",
    "main.filename_hint": "Имя файла для этого сеанса: {name}",
    "main.open_file": "Открыть файл",
    "main.open_folder": "Открыть папку",
    "main.open_folder.tip": "Показать сохранённый файл в его папке ({shortcut})",
    "main.save": "Сохранить",
    "main.save.tip": "Сохранить расшифровку в папку сохранения",
    "main.save_as": "Сохранить как\u2026",
    "main.save_as.tip": "Сохранить расшифровку в другое место или в другом формате ({shortcut})",
    "main.save_as.dialog": "Сохранить расшифровку как",
    "main.dismiss": "Закрыть это сообщение",
    # States
    "state.ready": "Готово к записи",
    "state.recording": "Идёт запись",
    "state.recording.speech": "Идёт запись \u00b7 обнаружена речь",
    "state.processing": "Обработка речи",
    "state.processing.pending": "Обработка речи \u00b7 осталось {seconds} с",
    "state.saving": "Сохранение файла",
    "state.completed": "Завершено",
    "state.error": "Ошибка",
    # Results and notices
    "result.saved": "Сохранено: {path}",
    "result.file_missing": (
        "Сохранённого файла больше нет на месте. "
        "Используйте \u00abСохранить как\u2026\u00bb, чтобы сохранить его снова."
    ),
    "result.open_failed": "Нет приложения, которое может открыть {path}.",
    "notice.no_speech": "Речь не обнаружена, поэтому файл не был создан.",
    "notice.microphone_disconnected": (
        "Микрофон перестал передавать звук, поэтому запись остановлена. "
        "Всё сказанное до этого сохранено."
    ),
    "notice.backlog_limit": (
        "Распознавание речи не успевало, поэтому запись остановлена. "
        "Всё записанное расшифровывается."
    ),
    "notice.silent_input": (
        "С микрофона поступает только тишина. Проверьте, что он не отключён и что "
        "Windows разрешает классическим приложениям доступ к микрофону "
        "(Параметры \u203a Конфиденциальность и защита \u203a Микрофон)."
    ),
    "notice.audio_dropped": (
        "Компьютер был слишком загружен, и короткий фрагмент звука был потерян."
    ),
    "notice.transcription_failed": (
        "Часть записи не удалось расшифровать, она пропущена. "
        "Подробности записаны в файл журнала."
    ),
    "notice.gpu_fallback": (
        "Видеокарту больше не удаётся использовать. Распознавание продолжается на "
        "процессоре и будет медленнее."
    ),
    "notice.session_recovered": "Несохранённый сеанс восстановлен.",
    # Errors
    "error.unknown": "Что-то пошло не так. Подробности записаны в файл журнала:\n{log}",
    "error.settings_save_failed": "Не удалось сохранить настройки: {detail}",
    "error.no_microphone": (
        "Микрофон не найден. Подключите микрофон и нажмите \u00abОбновить\u00bb."
    ),
    "error.microphone_open_failed": (
        "Не удалось открыть микрофон. Убедитесь, что другая программа не использует "
        "его в монопольном режиме и что Windows разрешает классическим приложениям "
        "доступ к микрофону (Параметры \u203a Конфиденциальность и защита \u203a Микрофон)."
    ),
    "error.audio_backend_unavailable": (
        "Запись звука недоступна на этом компьютере. Подробности записаны в файл журнала:\n{log}"
    ),
    "error.engine_blocked_by_policy": (
        "Windows заблокировала модуль распознавания речи (Smart App Control или другая "
        "политика управления приложениями). См. раздел \u00abTroubleshooting\u00bb в документации."
    ),
    "error.engine_import_failed": (
        "Не удалось запустить модуль распознавания речи. Возможно, установка неполная. "
        "Подробности записаны в файл журнала:\n{log}"
    ),
    "error.model_cache_unwritable": (
        "Нет доступа на запись в папку речевой модели: {detail}"
    ),
    "error.no_disk_space": (
        "Недостаточно свободного места на диске для загрузки речевой модели "
        "(нужно около 1 ГБ)."
    ),
    "error.model_download_failed": (
        "Не удалось загрузить речевую модель. Подключение к интернету нужно только в "
        "первый раз. Проверьте подключение и повторите попытку."
    ),
    "error.model_load_failed": (
        "Не удалось загрузить речевую модель. Подробности записаны в файл журнала:\n{log}"
    ),
    "error.model_not_loaded": "Речевая модель ещё не загружена.",
    "error.directory_missing": "Папка сохранения не существует: {detail}",
    "error.directory_invalid": "Место сохранения не является папкой: {detail}",
    "error.directory_not_writable": (
        "Нет доступа на запись в папку сохранения. Выберите другую папку. "
        "Расшифровка по-прежнему здесь и не потеряна."
    ),
    "error.export_failed": (
        "Не удалось сохранить файл. Расшифровка по-прежнему здесь: нажмите "
        "\u00abСохранить\u00bb, чтобы повторить, или \u00abСохранить как\u2026\u00bb, "
        "чтобы выбрать другое место."
    ),
    "error.unknown_format": "Выбранный формат файла не поддерживается.",
    "error.pdf_font_missing": (
        "Не найден шрифт, поддерживающий все символы, поэтому PDF не создан. "
        "Выберите другой формат или см. раздел \u00abTroubleshooting\u00bb в документации."
    ),
    # Model and device
    "model.idle": "Речевая модель: не загружена",
    "model.checking": "Проверка речевой модели\u2026",
    "model.downloading": "Загрузка речевой модели (только при первом запуске)\u2026",
    "model.downloading.progress": "Загрузка речевой модели\u2026 {megabytes} МБ",
    "model.initializing": "Инициализация речевой модели\u2026",
    "model.ready": "Модель: {model} \u00b7 {device}",
    "model.failed": "Речевая модель недоступна",
    "model.retry": "Повторить",
    "model.tip": "Речь распознаётся на этом компьютере. Звук никуда не отправляется.",
    "device.gpu": "GPU (NVIDIA CUDA, {compute_type})",
    "device.cpu": "Процессор ({compute_type})",
    "device.reason.cpu_selected": (
        "Используется процессор, потому что он выбран в настройках."
    ),
    "device.reason.cuda_unavailable": (
        "Используется процессор, потому что совместимая видеокарта NVIDIA не найдена."
    ),
    "device.reason.cuda_unsupported_compute_type": (
        "Используется процессор, потому что видеокарта не поддерживает подходящий "
        "числовой формат."
    ),
    "device.reason.cuda_init_failed": (
        "Используется процессор, потому что не удалось инициализировать видеокарту. "
        "Возможно, отсутствуют библиотеки NVIDIA (cuBLAS, cuDNN)."
    ),
    "device.reason.cuda_out_of_memory": (
        "Используется процессор, потому что видеокарте не хватило памяти."
    ),
    "device.reason.cuda_runtime_error": (
        "Используется процессор, потому что видеокарта сообщила об ошибке."
    ),
    # Dialogs
    "dialog.unsaved.title": "Несохранённая расшифровка",
    "dialog.unsaved.text": (
        "Текущая расшифровка не сохранена. При начале новой записи она будет удалена."
    ),
    "dialog.recover.title": "Восстановление несохранённых сеансов",
    "dialog.recover.text": (
        "При прошлом запуске приложения не были сохранены сеансы: {count}. "
        "Восстановить и сохранить их сейчас?"
    ),
    "dialog.recover.recover": "Восстановить и сохранить",
    "dialog.recover.discard": "Удалить",
    "dialog.recover.later": "Решить позже",
    "dialog.close.title": "Идёт запись",
    "dialog.close.recording": (
        "Идёт запись. Остановить её и сохранить расшифровку перед закрытием?"
    ),
    "dialog.close.stop_save": "Остановить, сохранить и закрыть",
    "dialog.close.keep": "Продолжить запись",
    "dialog.close.wait": (
        "Расшифровка завершается. Окно закроется после сохранения\u2026"
    ),
    "dialog.close.unsaved": (
        "Расшифровка не сохранена. Если закрыть сейчас, при следующем запуске будет "
        "предложено её восстановить."
    ),
    # Settings
    "settings.title": "Настройки",
    "settings.tab.general": "Общие",
    "settings.tab.recording": "Запись",
    "settings.tab.system": "Система",
    "settings.save": "Сохранить",
    "settings.cancel": "Отмена",
    "settings.defaults": "По умолчанию",
    "settings.defaults.tip": (
        "Заполняет форму значениями по умолчанию. Ничего не изменится, пока вы не сохраните."
    ),
    "settings.saved": "Настройки сохранены.",
    "settings.ui_language": "Язык интерфейса:",
    "settings.ui_language.hint": (
        "Меняет только язык этого приложения. Речь распознаётся на том языке, "
        "на котором говорят."
    ),
    "settings.folder": "Папка сохранения:",
    "settings.folder.hint": (
        "Расшифровки автоматически сохраняются сюда, когда запись останавливается."
    ),
    "settings.folder.error.relative": (
        "Введите полный путь, например C:\\Users\\Name\\Documents\\Transcripts."
    ),
    "settings.folder.create.title": "Создать папку",
    "settings.folder.create.text": "Такой папки нет:\n{path}\n\nСоздать её?",
    "settings.browse": "Обзор\u2026",
    "settings.format": "Формат файла:",
    "settings.template": "Имя файла:",
    "settings.template.hint": "Доступные подстановки: {placeholders}",
    "settings.template.preview": "Пример: {name}",
    "settings.template.error.empty": "Имя файла не может быть пустым.",
    "settings.template.error.unbalanced": "Фигурная скобка не закрыта.",
    "settings.template.error.unknown": "Неизвестная подстановка: {name}",
    "settings.documents": "Документы:",
    "settings.timestamps": "Показывать время в начале каждой строки расшифровки",
    "settings.open_after_save": "Открывать документ после сохранения",
    "settings.microphone": "Микрофон:",
    "settings.silence": "Пауза, завершающая фрагмент:",
    "settings.silence.hint": (
        "Тишина такой длительности завершает текущий фрагмент. Более короткие паузы "
        "остаются внутри него. Увеличьте значение, если фразы делятся слишком часто."
    ),
    "settings.threshold": "Чувствительность к речи:",
    "settings.threshold.hint": (
        "Низкие значения улавливают тихую речь, но и больше фонового шума. "
        "Высокие значения отсекают больше шума."
    ),
    "settings.min_speech": "Самая короткая речь:",
    "settings.min_speech.hint": "Более короткие звуки, например щелчки, игнорируются.",
    "settings.max_segment": "Самый длинный фрагмент:",
    "settings.max_segment.hint": (
        "Непрерывная речь делится на ближайшей короткой паузе, когда приближается к "
        "этой длительности."
    ),
    "settings.pre_roll": "Запас в начале:",
    "settings.pre_roll.hint": (
        "Звук, сохраняемый до обнаружения речи, чтобы не обрезать первый слог."
    ),
    "settings.post_roll": "Запас в конце:",
    "settings.post_roll.hint": (
        "Звук, сохраняемый после окончания речи, чтобы не обрезать последний слог."
    ),
    "settings.debugging": "Диагностика:",
    "settings.retain_audio": "Сохранять исходный звук каждого сеанса",
    "settings.retain_audio.hint": (
        "По умолчанию выключено. Если включено, звук с микрофона каждого сеанса "
        "хранится на этом компьютере в виде WAV-файла, пока вы его не удалите."
    ),
    "settings.open_audio_folder": "Открыть папку со звуком",
    "settings.device": "Устройство обработки:",
    "settings.device.hint": (
        "\u00abАвтоматически\u00bb использует видеокарту NVIDIA, если она работает, иначе процессор."
    ),
    "settings.device.auto": "Автоматически (рекомендуется)",
    "settings.device.cuda": "Видеокарта (NVIDIA CUDA)",
    "settings.device.cpu": "Процессор (CPU)",
    "settings.device.in_use": "Сейчас используется:",
    "settings.model": "Речевая модель:",
    "settings.model.cached": "Whisper {model} \u00b7 хранится на этом компьютере ({megabytes} МБ)",
    "settings.model.missing": "Whisper {model} \u00b7 ещё не загружена",
    "settings.model.location": "Расположение модели:",
    "settings.model.open": "Открыть папку модели",
    "settings.logs": "Файлы журнала:",
    "settings.logs.open": "Открыть папку журналов",
    "settings.logs.hint": (
        "Журналы содержат только технические сведения и никогда не содержат звук или "
        "текст расшифровки."
    ),
    "settings.privacy": "Конфиденциальность:",
    "settings.privacy.text": (
        "Звук и расшифровки остаются на этом компьютере. Интернет используется только "
        "один раз, чтобы загрузить речевую модель."
    ),
}
