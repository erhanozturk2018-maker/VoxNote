"""Turkish interface strings."""

STRINGS = {
    "app.version": "Sürüm {version}",
    "unit.ms": "ms",
    "unit.s": "sn",
    # Main window
    "main.settings": "Ayarlar",
    "main.settings.tip": "Ayarları aç ({shortcut})",
    "main.start": "\u25cf  Kaydı Başlat",
    "main.start.tip": "Yeni bir kayıt başlat ({shortcut})",
    "main.start.tip.model": "Konuşma modeli yüklenir yüklenmez kullanılabilir",
    "main.start.tip.busy": "Geçerli oturum bittiğinde kullanılabilir",
    "main.stop": "\u25a0  Kaydı Durdur",
    "main.stop.tip": "Durdur, dökümü tamamla ve kaydet ({shortcut})",
    "main.microphone": "Mikrofon:",
    "main.microphone.default": "Sistem varsayılan mikrofonu",
    "main.refresh": "Yenile",
    "main.refresh.tip": "Yeni bağlanan mikrofonları ara",
    "main.refresh.done": "Bulunan mikrofon sayısı: {count}",
    "main.level": "Giriş seviyesi:",
    "main.elapsed": "Geçen kayıt süresi",
    "main.status": "Durum: {status}",
    "main.transcript": "Döküm",
    "main.transcript.placeholder": (
        "Konuştukça sözleriniz burada görünür. Başlamak için \u201cKaydı Başlat\u201d düğmesine basın."
    ),
    "main.languages": "Diller: {languages}",
    "main.languages.none": "henüz algılanmadı",
    "main.copy": "Metni Kopyala",
    "main.copy.tip": "Döküm metnini panoya kopyala ({shortcut})",
    "main.copy.done": "Döküm panoya kopyalandı.",
    "main.output": "Çıktı",
    "main.folder": "Kayıt klasörü:",
    "main.folder.change": "Değiştir\u2026",
    "main.folder.change.tip": "Dökümlerin kaydedileceği yeri seç",
    "main.folder.dialog": "Dökümlerin kaydedileceği klasörü seçin",
    "main.folder.changed": "Kayıt klasörü değiştirildi.",
    "main.format": "Biçim:",
    "main.filename_hint": "Bu oturumun dosya adı: {name}",
    "main.filename_example": "Örnek dosya adı: {name}",
    "main.open_file": "Dosyayı Aç",
    "main.open_folder": "Klasörü Aç",
    "main.open_folder.tip": "Kaydedilen dosyayı klasöründe göster ({shortcut})",
    "main.save": "Kaydet",
    "main.save.tip": "Dökümü kayıt klasörüne kaydet",
    "main.save_as": "Farklı Kaydet\u2026",
    "main.save_as.tip": "Dökümü başka bir yere veya biçimde kaydet ({shortcut})",
    "main.save_as.dialog": "Dökümü farklı kaydet",
    "main.dismiss": "Bu iletiyi kapat",
    # States
    "state.ready": "Hazır",
    "state.recording": "Kaydediliyor",
    "state.recording.speech": "Kaydediliyor \u00b7 konuşma algılandı",
    "state.processing": "Konuşma işleniyor",
    "state.processing.pending": "Konuşma işleniyor \u00b7 {seconds} sn kaldı",
    "state.saving": "Dosya kaydediliyor",
    "state.completed": "Tamamlandı",
    "state.error": "Hata",
    # Results and notices
    "result.saved": "Kaydedildi: {path}",
    "result.file_missing": (
        "Kaydedilen dosya artık yerinde değil. Yeniden kaydetmek için "
        "\u201cFarklı Kaydet\u2026\u201d seçeneğini kullanın."
    ),
    "result.open_failed": "{path} dosyasını açabilecek bir uygulama yok.",
    "notice.no_speech": "Konuşma algılanmadı, bu yüzden dosya oluşturulmadı.",
    "notice.microphone_disconnected": (
        "Mikrofon ses göndermeyi bıraktığı için kayıt durduruldu. "
        "O ana kadar söylenen her şey korunuyor."
    ),
    "notice.backlog_limit": (
        "Konuşma tanıma yetişemediği için kayıt durduruldu. "
        "O ana kadar kaydedilen her şey yazıya dökülüyor."
    ),
    "notice.silent_input": (
        "Mikrofondan yalnızca sessizlik geliyor. Mikrofonun kapalı olmadığını ve Windows'un "
        "masaüstü uygulamalarına mikrofon izni verdiğini kontrol edin "
        "(Ayarlar \u203a Gizlilik ve güvenlik \u203a Mikrofon)."
    ),
    "notice.audio_dropped": "Bilgisayar çok meşguldü ve sesin kısa bir bölümü kayboldu.",
    "notice.transcription_failed": (
        "Kaydın bir bölümü yazıya dökülemedi ve atlandı. Ayrıntılar günlük dosyasında."
    ),
    "notice.gpu_fallback": (
        "Ekran kartı artık kullanılamıyor. Tanıma işlemciyle devam ediyor ve daha yavaş olacak."
    ),
    "notice.session_recovered": "Kaydedilmemiş bir oturum kurtarıldı.",
    # Errors
    "error.unknown": "Bir sorun oluştu. Ayrıntılar günlük dosyasına yazıldı:\n{log}",
    "error.settings_save_failed": "Ayarlar kaydedilemedi: {detail}",
    "error.no_microphone": (
        "Mikrofon bulunamadı. Bir mikrofon bağlayın ve \u201cYenile\u201d düğmesine basın."
    ),
    "error.microphone_open_failed": (
        "Mikrofon açılamadı. Başka bir programın mikrofonu tek başına kullanmadığından ve "
        "Windows'un masaüstü uygulamalarına mikrofon izni verdiğinden emin olun "
        "(Ayarlar \u203a Gizlilik ve güvenlik \u203a Mikrofon)."
    ),
    "error.audio_backend_unavailable": (
        "Bu bilgisayarda ses kaydı kullanılamıyor. Ayrıntılar günlük dosyasına yazıldı:\n{log}"
    ),
    "error.engine_blocked_by_policy": (
        "Windows konuşma tanıma motorunu engelledi (Akıllı Uygulama Denetimi veya başka bir "
        "uygulama denetim ilkesi). Belgelerdeki \u201cTroubleshooting\u201d bölümüne bakın."
    ),
    "error.engine_import_failed": (
        "Konuşma tanıma motoru başlatılamadı. Kurulum eksik olabilir. "
        "Ayrıntılar günlük dosyasına yazıldı:\n{log}"
    ),
    "error.model_cache_unwritable": "Konuşma modelinin klasörüne yazılamıyor: {detail}",
    "error.no_disk_space": (
        "Konuşma modelini indirmek için yeterli boş disk alanı yok (yaklaşık 1 GB gerekir)."
    ),
    "error.model_download_failed": (
        "Konuşma modeli indirilemedi. İnternet bağlantısı yalnızca ilk seferde gerekir. "
        "Bağlantıyı kontrol edip yeniden deneyin."
    ),
    "error.model_load_failed": (
        "Konuşma modeli yüklenemedi. Ayrıntılar günlük dosyasına yazıldı:\n{log}"
    ),
    "error.model_not_loaded": "Konuşma modeli henüz yüklenmedi.",
    "error.directory_missing": "Kayıt klasörü yok: {detail}",
    "error.directory_invalid": "Kayıt konumu bir klasör değil: {detail}",
    "error.directory_not_writable": (
        "Kayıt klasörüne yazılamıyor. Başka bir klasör seçin. "
        "Dökümünüz hâlâ burada, kaybolmadı."
    ),
    "error.export_failed": (
        "Dosya kaydedilemedi. Dökümünüz hâlâ burada: yeniden denemek için "
        "\u201cKaydet\u201d, başka bir yer seçmek için \u201cFarklı Kaydet\u2026\u201d düğmesini kullanın."
    ),
    "error.unknown_format": "Seçilen dosya biçimi desteklenmiyor.",
    "error.pdf_font_missing": (
        "Tüm karakterleri destekleyen bir yazı tipi bulunamadığı için PDF oluşturulmadı. "
        "Başka bir biçim seçin veya belgelerdeki \u201cTroubleshooting\u201d bölümüne bakın."
    ),
    # Model and device
    "model.idle": "Konuşma modeli: yüklenmedi",
    "model.checking": "Konuşma modeli kontrol ediliyor\u2026",
    "model.downloading": "Konuşma modeli indiriliyor (yalnızca ilk çalıştırmada)\u2026",
    "model.downloading.progress": "Konuşma modeli indiriliyor\u2026 {megabytes} MB",
    "model.initializing": "Konuşma modeli yükleniyor\u2026",
    "model.ready": "Model: {model} \u00b7 {device}",
    "model.failed": "Konuşma modeli kullanılamıyor",
    "model.retry": "Yeniden Dene",
    "model.tip": "Konuşma bu bilgisayarda tanınır. Hiçbir ses dışarı gönderilmez.",
    "device.gpu": "GPU (NVIDIA CUDA, {compute_type})",
    "device.cpu": "İşlemci ({compute_type})",
    "device.reason.cpu_selected": "Ayarlar'da seçildiği için işlemci kullanılıyor.",
    "device.reason.cuda_unavailable": (
        "Uyumlu bir NVIDIA ekran kartı bulunamadığı için işlemci kullanılıyor."
    ),
    "device.reason.cuda_unsupported_compute_type": (
        "Ekran kartı uygun bir sayı biçimini desteklemediği için işlemci kullanılıyor."
    ),
    "device.reason.cuda_init_failed": (
        "Ekran kartı başlatılamadığı için işlemci kullanılıyor. "
        "NVIDIA kitaplıkları (cuBLAS, cuDNN) eksik olabilir."
    ),
    "device.reason.cuda_out_of_memory": (
        "Ekran kartının belleği yetmediği için işlemci kullanılıyor."
    ),
    "device.reason.cuda_runtime_error": (
        "Ekran kartı hata bildirdiği için işlemci kullanılıyor."
    ),
    # Dialogs
    "dialog.unsaved.title": "Kaydedilmemiş döküm",
    "dialog.unsaved.text": (
        "Geçerli döküm kaydedilmedi. Yeni bir kayıt başlatırsanız silinir."
    ),
    "dialog.recover.title": "Kaydedilmemiş oturumları kurtar",
    "dialog.recover.text": (
        "Uygulama son çalıştığında {count} oturum kaydedilmedi. "
        "Şimdi kurtarıp kaydetmek ister misiniz?"
    ),
    "dialog.recover.recover": "Kurtar ve Kaydet",
    "dialog.recover.discard": "Sil",
    "dialog.recover.later": "Sonra Karar Ver",
    "dialog.close.title": "Kayıt sürüyor",
    "dialog.close.recording": (
        "Bir kayıt sürüyor. Kapatmadan önce kayıt durdurulup döküm kaydedilsin mi?"
    ),
    "dialog.close.stop_save": "Durdur, Kaydet ve Kapat",
    "dialog.close.keep": "Kayda Devam Et",
    "dialog.close.wait": "Döküm tamamlanıyor. Kaydedildiğinde pencere kapanacak\u2026",
    "dialog.close.unsaved": (
        "Döküm kaydedilmedi. Şimdi kapatırsanız, uygulama bir sonraki açılışta "
        "onu kurtarmayı önerecek."
    ),
    # Settings
    "settings.title": "Ayarlar",
    "settings.tab.general": "Genel",
    "settings.tab.recording": "Kayıt",
    "settings.tab.system": "Sistem",
    "settings.save": "Kaydet",
    "settings.cancel": "İptal",
    "settings.defaults": "Varsayılanlara Dön",
    "settings.defaults.tip": "Formu varsayılan değerlerle doldurur. Kaydedene kadar hiçbir şey değişmez.",
    "settings.saved": "Ayarlar kaydedildi.",
    "settings.ui_language": "Arayüz dili:",
    "settings.ui_language.hint": (
        "Yalnızca bu uygulamanın dilini değiştirir. Konuşma, hangi dilde konuşulursa "
        "o dilde tanınır."
    ),
    "settings.folder": "Kayıt klasörü:",
    "settings.folder.hint": "Kayıt durduğunda dökümler otomatik olarak buraya kaydedilir.",
    "settings.folder.error.relative": "Tam yol girin, örneğin C:\\Users\\Ad\\Documents\\Dokumler.",
    "settings.folder.create.title": "Klasör oluştur",
    "settings.folder.create.text": "Bu klasör yok:\n{path}\n\nOluşturulsun mu?",
    "settings.browse": "Gözat\u2026",
    "settings.format": "Dosya biçimi:",
    "settings.template": "Dosya adı:",
    "settings.template.hint": "Kullanılabilir yer tutucular: {placeholders}",
    "settings.template.preview": "Önizleme: {name}",
    "settings.template.error.empty": "Dosya adı boş olamaz.",
    "settings.template.error.unbalanced": "Bir süslü parantez kapatılmamış.",
    "settings.template.error.unknown": "Bilinmeyen yer tutucu: {name}",
    "settings.documents": "Belgeler:",
    "settings.timestamps": "Her döküm satırının başında zamanı göster",
    "settings.open_after_save": "Belge kaydedildikten sonra aç",
    "settings.microphone": "Mikrofon:",
    "settings.silence": "Bölümü bitiren duraklama:",
    "settings.silence.hint": (
        "Bu uzunluktaki sessizlik geçerli bölümü bitirir. Daha kısa duraklamalar bölümün "
        "içinde kalır. Cümleler çok sık bölünüyorsa artırın."
    ),
    "settings.threshold": "Konuşma duyarlılığı:",
    "settings.threshold.hint": (
        "Düşük değerler kısık sesli konuşmayı yakalar ama daha fazla arka plan gürültüsü de alır. "
        "Yüksek değerler gürültüyü daha çok yok sayar."
    ),
    "settings.min_speech": "En kısa konuşma:",
    "settings.min_speech.hint": "Tıklama gibi bundan kısa sesler yok sayılır.",
    "settings.max_segment": "En uzun bölüm:",
    "settings.max_segment.hint": (
        "Kesintisiz konuşma bu uzunluğa yaklaştığında bir sonraki kısa duraklamada bölünür."
    ),
    "settings.pre_roll": "Ön pay:",
    "settings.pre_roll.hint": "İlk hecenin kesilmemesi için konuşma algılanmadan önce tutulan ses.",
    "settings.post_roll": "Son pay:",
    "settings.post_roll.hint": "Son hecenin kesilmemesi için konuşma bittikten sonra tutulan ses.",
    "settings.debugging": "Sorun giderme:",
    "settings.retain_audio": "Her oturumun ham sesini sakla",
    "settings.retain_audio.hint": (
        "Varsayılan olarak kapalıdır. Açıkken her oturumun mikrofon sesi, siz silene kadar "
        "bu bilgisayarda WAV dosyası olarak saklanır."
    ),
    "settings.open_audio_folder": "Ses Klasörünü Aç",
    "settings.device": "İşlem aygıtı:",
    "settings.device.hint": (
        "\u201cOtomatik\u201d, çalışan bir NVIDIA ekran kartı varsa onu, yoksa işlemciyi kullanır."
    ),
    "settings.device.auto": "Otomatik (önerilir)",
    "settings.device.cuda": "Ekran kartı (NVIDIA CUDA)",
    "settings.device.cpu": "İşlemci (CPU)",
    "settings.device.in_use": "Şu an kullanılan:",
    "settings.model": "Konuşma modeli:",
    "settings.model.cached": "Whisper {model} \u00b7 bu bilgisayarda kayıtlı ({megabytes} MB)",
    "settings.model.missing": "Whisper {model} \u00b7 henüz indirilmedi",
    "settings.model.location": "Model konumu:",
    "settings.model.open": "Model Klasörünü Aç",
    "settings.logs": "Günlük dosyaları:",
    "settings.logs.open": "Günlük Klasörünü Aç",
    "settings.logs.hint": "Günlükler yalnızca teknik ayrıntı içerir; ses veya döküm metni içermez.",
    "settings.privacy": "Gizlilik:",
    "settings.privacy.text": (
        "Ses ve dökümler bu bilgisayarda kalır. İnternet yalnızca bir kez, "
        "konuşma modelini indirmek için kullanılır."
    ),
}
