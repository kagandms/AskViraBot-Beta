from .common import (
    SOCIAL_MEDIA_LINKS, 
    CITY_NAMES_TRANSLATED, 
    turkish_lower, 
    generate_mappings_from_buttons
)
TEXTS = {
    # --- YENİ EKLENENLER: DÜZENLEME & OYUN & MENÜ ---
    "edit_notes_menu_prompt": {
        "tr": "✏️ Düzenlemek istediğiniz notu seçin:",
        "en": "✏️ Select the note you want to edit:",
        "ru": "✏️ Выберите заметку для редактирования:"
    },
    "prompt_select_note_to_edit": {
        "tr": "✏️ Lütfen içeriğini değiştirmek istediğiniz notu seçin:",
        "en": "✏️ Please select the note you want to edit:",
        "ru": "✏️ Пожалуйста, выберите заметку для изменения:"
    },
    "prompt_new_content_for_note": {
        "tr": "📝 Seçilen not için YENİ içeriği yazın:",
        "en": "📝 Type the NEW content for the selected note:",
        "ru": "📝 Введите НОВОЕ содержимое для выбранной заметки:"
    },
    "note_updated": {
        "tr": "✅ Not başarıyla güncellendi.",
        "en": "✅ Note successfully updated.",
        "ru": "✅ Заметка успешно обновлена."
    },
    "games_menu_prompt": {
        "tr": "🎮 Oyun Odasına Hoş Geldiniz! Bir oyun seçin:",
        "en": "🎮 Welcome to Game Room! Choose a game:",
        "ru": "🎮 Добро пожаловать в игровую комнату! Выберите игру:"
    },
    "tools_menu_prompt": {
        "tr": "🛠 Araçlar Menüsüne Hoş Geldiniz! Bir araç seçin:",
        "en": "🛠 Welcome to Tools Menu! Choose a tool:",
        "ru": "🛠 Добро пожаловать в меню инструментов! Выберите инструмент:"
    },
    
    # ... (Eski metinler korunuyor) ...
    "start": {
        "tr": "👋 Merhaba! Ben DruzhikBot. Seni tekrar görmek güzel.\n/menu yazarak komutlara ulaşabilirsin.",
        "en": "👋 Hello! I am DruzhikBot. Good to see you again.\nYou can access commands by typing /menu.",
        "ru": "👋 Привет! Я DruzhikBot. Рад снова видеть тебя.\nВы можете получить доступ к командам, набрав /menu."
    },
    "menu_prompt": {
        "tr": "🏠 Ana Menüdesiniz. Ne yapmak istersiniz? 👇",
        "en": "🏠 You are in the Main Menu. What would you like to do? 👇",
        "ru": "🏠 Вы в Главном меню. Что бы вы хотели сделать? 👇"
    },
    "language_set": {
        "tr": "Dil Türkçe olarak ayarlandı.",
        "en": "Language set to English.",
        "ru": "Язык установлен на русский."
    },
    "no_notes": {
        "tr": "📂 Henüz kayıtlı notunuz yok.",
        "en": "📂 You have no saved notes yet.",
        "ru": "📂 У вас еще нет сохраненных заметок."
    },
    "notes_header": {
        "tr": "📝 Kayıtlı Notlarınız:\n",
        "en": "📝 Your saved notes:\n",
        "ru": "📝 Ваши сохраненные заметки:\n"
    },
    "notes_menu_prompt": {
        "tr": "Notlar menüsünden bir işlem seçin:",
        "en": "Choose an action from the notes menu:",
        "ru": "Выберите действие из меню заметок:"
    },
    "delete_notes_menu_prompt": {
        "tr": "Silmek için bir seçenek belirleyin:",
        "en": "Choose a delete option:",
        "ru": "Выберите вариант удаления:"
    },
    "prompt_select_note_to_delete": {
        "tr": "Lütfen silmek istediğiniz notu seçin:",
        "en": "Please select the note you want to delete:",
        "ru": "Пожалуйста, выберите заметку, которую хотите удалить:"
    },
    "invalid_note_number": {
        "tr": "Geçersiz not numarası.",
        "en": "Invalid note number.",
        "ru": "Неверный номер заметки."
    },
    "unknown_command": {
        "tr": "❓ Üzgünüm, bu komutu anlayamadım. Lütfen /menu yazarak komutları görüntüleyin.",
        "en": "❓ Sorry, I didn't understand that command. Please type /menu to see available commands.",
        "ru": "❓ Извините, я не понял эту команду. Пожалуйста, введите /menu для списка команд."
    },
    "prompt_new_note": {
        "tr": "✏️ Lütfen notunuzu yazın:",
        "en": "✏️ Please write your note:",
        "ru": "✏️ Пожалуйста, напишите заметку:"
    },
    "addnote_no_content": {
        "tr": "Lütfen not almak için /addnote komutundan sonra notunu yaz.",
        "en": "Please write your note after /addnote command.",
        "ru": "Пожалуйста, напишите заметку после команды /addnote."
    },
    "note_saved": {
        "tr": "✅ Notunuz kaydedildi: ",
        "en": "✅ Your note has been saved: ",
        "ru": "✅ Ваша заметка сохранена: "
    },
    "note_deleted": {
        "tr": "🗑️ not silindi",
        "en": "🗑️ note deleted",
        "ru": "🗑️ заметка удалена"
    },
    "dice_rolled": {
        "tr": "🎲 Zar attın: {number}",
        "en": "🎲 You rolled: {number}",
        "ru": "🎲 Вы бросили: {number}"
    },
    "coinflip_result": {
        "tr": "🪙 {result} geldi!",
        "en": "🪙 It's {result}!",
        "ru": "🪙 Выпало: {result}!"
    },
    "remind_usage": {
        "tr": "ℹ️ Lütfen bir saat ve mesaj girin. Örn: `/remind 14:30 toplantı` veya `10:00 2025-12-31 yeni yıl`",
        "en": "ℹ️ Please enter a time and message. Ex: `/remind 14:30 meeting` or `10:00 2025-12-31 new year`",
        "ru": "ℹ️ Пожалуйста, введите время и сообщение. Пример: `/remind 14:30 встреча` или `10:00 2025-12-31 новый год`"
    },
    "remind_prompt_input": {
        "tr": "✏️ Lütfen hatırlatıcı için saati ve mesajı girin. Örn: `14:30 toplantı` veya `10:00 2025-12-31 yeni yıl`",
        "en": "✏️ Please enter the time and message for the reminder. Ex: `14:30 meeting` or `10:00 2025-12-31 new year`",
        "ru": "✏️ Пожалуйста, введите время и сообщение для напоминания. Пример: `14:30 встреча` или `10:00 2025-12-31 новый год`"
    },
    "reminder_set": {
        "tr": "⏰ Hatırlatıcı ayarlandı: {time_str} - {message}\nKalan süre: {remaining_time}",
        "en": "⏰ Reminder set for {time_str} - {message}\nRemaining time: {remaining_time}",
        "ru": "⏰ Напоминание установлено: {time_str} - {message}\nОставшееся время: {remaining_time}"
    },
    "error_occurred": {
        "tr": "❌ Hata oluştu: ",
        "en": "❌ An error occurred: ",
        "ru": "❌ Произошла ошибка: "
    },
    "qrcode_generated": {
        "tr": "✅ QR kod oluşturuldu.\n{data}",
        "en": "✅ QR code generated.\n{data}",
        "ru": "✅ QR-код создан.\n{data}"
    },
    "qrcode_prompt_input": {
        "tr": "Lütfen QR koda dönüştürmek istediğiniz metni, bağlantıyı veya veriyi yazın:",
        "en": "Please type the text, link, or data you want to convert to QR code:",
        "ru": "Пожалуйста, введите текст, ссылку или данные, которые вы хотите преобразовать в QR-код:"
    },
    "tkm_welcome": {
        "tr": "Taş-Kağıt-Makas oyununa hoşgeldin! Aşağıdaki butonlardan birini seç:",
        "en": "Welcome to Rock-Paper-Scissors! Choose one of the buttons below:",
        "ru": "Добро пожаловать в игру Камень-Ножницы-Бумага! Выберите одну из кнопок ниже:"
    },
    "tkm_tie": {
        "tr": "Berabere kaldık!",
        "en": "It's a tie!",
        "ru": "Ничья!"
    },
    "tkm_win": {
        "tr": "Tebrikler, kazandın! 🎉",
        "en": "Congratulations, you won! 🎉",
        "ru": "Поздравляю, ты выиграл(а)! 🎉"
    },
    "tkm_lose": {
        "tr": "Üzgünüm, kaybettin! 😞",
        "en": "Sorry, you lost! 😞",
        "ru": "К сожалению, ты проиграл(а)! 😞"
    },
    "tkm_labels_you": {
        "tr": "Sen",
        "en": "You",
        "ru": "Ты"
    },
    "tkm_labels_bot": {
        "tr": "Ben",
        "en": "Bot",
        "ru": "Я"
    },
    "tkm_invalid_input": {
        "tr": "Lütfen sadece butonları kullan: Taş, Kağıt veya Makas.",
        "en": "Please only use buttons: Rock, Paper, or Scissors.",
        "ru": "Пожалуйста, используйте только кнопки: Камень, Ножницы или Бумага."
    },
    "next_page": {
        "tr": "Sonraki Sayfa",
        "en": "Next Page",
        "ru": "Следующая Страница"
    },
    "previous_page": {
        "tr": "Önceki Sayfa",
        "en": "Previous Page",
        "ru": "Предыдущая Страница"
    },
    "note_button_prefix": {
        "tr": "Not ",
        "en": "Note ",
        "ru": "Заметка "
    },
    "back_button_inline": {
        "tr": "🔙 Geri",
        "en": "🔙 Back",
        "ru": "🔙 Назад"
    },
    "pdf_converter_menu_prompt": {
        "tr": "📄 PDF dönüştürme seçenekleri:",
        "en": "📄 PDF conversion options:",
        "ru": "📄 Параметры конвертации PDF:"
    },
    "prompt_text_for_pdf": {
        "tr": "✏️ Lütfen PDF'e dönüştürmek istediğiniz metni yazın:",
        "en": "✏️ Please type the text you want to convert to PDF:",
        "ru": "✏️ Пожалуйста, введите текст для конвертации в PDF:"
    },
    "prompt_file_for_pdf": {
        "tr": "📂 Lütfen PDF'e dönüştürmek istediğiniz dosyayı (resim, DOCX, TXT) gönderin:",
        "en": "📂 Please send the file (image, DOCX, TXT) you want to convert to PDF:",
        "ru": "📂 Пожалуйста, отправьте файл (изображение, DOCX, TXT) для конвертации в PDF:"
    },
    "pdf_conversion_success": {
        "tr": "✅ Dosya başarıyla PDF'e dönüştürüldü.",
        "en": "✅ File successfully converted to PDF.",
        "ru": "✅ Файл успешно сконвертирован в PDF."
    },
    "pdf_conversion_error": {
        "tr": "PDF dönüştürülürken bir hata oluştu: {error}",
        "en": "An error occurred while converting to PDF: {error}",
        "ru": "Произошла ошибка при конвертации в PDF: {error}"
    },
    "unsupported_file_type": {
        "tr": "Üzgünüm, bu dosya türünü PDF'e dönüştüremem. Lütfen bir resim (JPG, PNG), DOCX veya TXT dosyası gönderin.",
        "en": "Sorry, I cannot convert this file type to PDF. Please send an image (JPG, PNG), DOCX, or TXT file.",
        "ru": "Извините, я не могу конвертировать этот тип файла в PDF. Пожалуйста, отправьте изображение (JPG, PNG), DOCX или TXT файл."
    },
    "waiting_for_input": {
        "tr": "⏳ Lütfen girişinizi bekliyorum...",
        "en": "⏳ Waiting for your input...",
        "ru": "⏳ Ожидаю ваш ввод..."
    },
    "docx_conversion_warning": {
        "tr": "⚠️ DOCX'ten PDF'e dönüştürme için sunucuda Microsoft Word veya LibreOffice kurulu olması gerekebilir. Kurulum yoksa bu işlem başarısız olabilir.",
        "en": "⚠️ DOCX to PDF conversion might require Microsoft Word or LibreOffice installed on the server. The operation may fail if not present.",
        "ru": "⚠️ Для конвертации DOCX в PDF может потребоваться установка Microsoft Word или LibreOffice на сервере. Операция может завершиться неудачей, если они отсутствуют."
    },
    "weather_prompt_city": {
        "tr": "🏙️ Hava durumunu öğrenmek istediğiniz şehrin adını girin:",
        "en": "🏙️ Please enter the name of the city for which you want to get the weather:",
        "ru": "🏙️ Пожалуйста, введите название города, для которого вы хотите узнать погоду:"
    },
    "weather_current": {
        "tr": "📍 {city}\n🌡️ Sıcaklık: {temp}°C\n❔ Hissedilen: {feels_like}°C\n✨ Durum: {description}\n💧 Nem: %{humidity}\n💨 Rüzgar: {wind_speed} m/s",
        "en": "📍 {city}\n🌡️ Temperature: {temp}°C\n❔ Feels like: {feels_like}°C\n✨ Condition: {description}\n💧 Humidity: %{humidity}\n💨 Wind: {wind_speed} m/s",
        "ru": "📍 {city}\n🌡️ Температура: {temp}°C\n❔ Ощущается как: {feels_like}°C\n✨ Условия: {description}\n💧 Влажность: %{humidity}\n💨 Ветер: {wind_speed} м/с"
    },
    "weather_city_not_found": {
        "tr": "❌ Üzgünüm, '{city}' şehri için hava durumu bilgisi bulunamadı. Lütfen şehir adını doğru yazdığınızdan emin olun.",
        "en": "❌ Sorry, weather information for '{city}' not found. Please make sure you spelled the city name correctly.",
        "ru": "❌ Извините, информация о погоде для города '{city}' не найдена. Пожалуйста, убедитесь, что вы правильно ввели название города."
    },
    "weather_api_error": {
        "tr": "❌ Hava durumu bilgisi alınırken bir hata oluştu. Lütfen daha sonra tekrar deneyin.",
        "en": "❌ An error occurred while fetching weather information. Please try again later.",
        "ru": "❌ Произошла ошибка при получении информации о погоде. Пожалуйста, попробуйте позже."
    },
    "weather_select_city": { 
        "tr": "🏙️ Hava durumunu öğrenmek istediğiniz şehri seçin:",
        "en": "🏙️ Select the city for which you want to get the weather:",
        "ru": "🏙️ Выберите город, для которого вы хотите узнать погоду:"
    },
    "weather_forecast_button": {
        "tr": "📅 5 Günlük Tahmin",
        "en": "📅 5-Day Forecast",
        "ru": "📅 Прогноз на 5 дней"
    },
    "weather_forecast_title": {
        "tr": "📅 *{city} - 5 Günlük Tahmin*",
        "en": "📅 *{city} - 5-Day Forecast*",
        "ru": "📅 *{city} - Прогноз на 5 дней*"
    },
    "weather_day_format": {
        "tr": "*{day}:* {icon} {max_temp}°C / {min_temp}°C ({desc})",
        "en": "*{day}:* {icon} {max_temp}°C / {min_temp}°C ({desc})",
        "ru": "*{day}:* {icon} {max_temp}°C / {min_temp}°C ({desc})"
    },
    "weather_back_to_current": {
        "tr": "🔄 Şu Anki Durum",
        "en": "🔄 Current Weather",
        "ru": "🔄 Текущая Погода"
    },
    "developer_info_prompt": { 
        "tr": "👨‍💻 Sosyal medya hesaplarıma aşağıdaki bağlantılardan ulaşabilirsiniz:",
        "en": "👨‍💻 You can reach my social media accounts via the links below:",
        "ru": "👨‍💻 Вы можете связаться со мной через социальные сети по ссылкам ниже:"
    },
    "reminder_menu_prompt": {
        "tr": "Hatırlatıcılar menüsünden bir işlem seçin:",
        "en": "Choose an action from the reminders menu:",
        "ru": "Выберите действие из меню напоминаний:"
    },
    "no_reminders": {
        "tr": "📂 Henüz kayıtlı hatırlatıcınız yok.",
        "en": "📂 You have no saved reminders yet.",
        "ru": "📂 У вас еще нет сохраненных напоминаний."
    },
    "reminders_header": {
        "tr": "⏰ Kayıtlı Hatırlatıcılarınız:\n",
        "en": "⏰ Your saved reminders:\n",
        "ru": "⏰ Ваши сохранённые напоминания:\n"
    },
    "prompt_select_reminder_to_delete": {
        "tr": "🗑️ Lütfen silmek istediğiniz hatırlatıcıyı seçin:",
        "en": "🗑️ Please select the reminder you want to delete:",
        "ru": "🗑️ Пожалуйста, выберите напоминание, которое хотите удалить:"
    },
    "reminder_deleted": {
        "tr": "🗑️ hatırlatıcı silindi.",
        "en": "🗑️ reminder deleted.",
        "ru": "🗑️ напоминание удалено."
    },
    "invalid_reminder_number": {
        "tr": "❌ Geçersiz hatırlatıcı numarası.",
        "en": "❌ Invalid reminder number.",
        "ru": "❌ Неверный номер напоминания."
    },
    "remaining_time_format": {
        "tr": "{days} gün, {hours} saat, {minutes} dakika, {seconds} saniye",
        "en": "{days} days, {hours} hours, {minutes} minutes, {seconds} seconds",
        "ru": "{days} дней, {hours} часов, {minutes} часов, {seconds} секунд"
    },
    "remaining_time_format_short": {
        "tr": "{hours}s {minutes}dk {seconds}sn",
        "en": "{hours}h {minutes}m {seconds}s",
        "ru": "{hours}ч {minutes}м {seconds}с"
    },
    "my_website": {
        "tr": "🌐 Web Sitem",
        "en": "🌐 My Website",
        "ru": "🌐 Мой Веб-сайт"
    },

    # --- XOX (TIC TAC TOE) ---
    "xox_welcome": {
        "tr": "XOX (Tic-Tac-Toe) oyununa hoş geldin! Hamle yapmak için bir kutuya tıkla.",
        "en": "Welcome to Tic-Tac-Toe! Click a box to make a move.",
        "ru": "Добро пожаловать в Крестики-нолики! Нажмите на клетку, чтобы сделать ход."
    },
    "xox_turn_user": {
        "tr": "Sıra sende (X) 👇",
        "en": "Your turn (X) 👇",
        "ru": "Твой ход (X) 👇"
    },
    "xox_turn_bot": {
        "tr": "Sıra bende (O)...",
        "en": "My turn (O)...",
        "ru": "Мой ход (O)..."
    },
    "xox_win": {
        "tr": "🎉 Tebrikler! Sen kazandın!",
        "en": "🎉 Congratulations! You won!",
        "ru": "🎉 Поздравляю! Ты выиграл(а)!"
    },
    "xox_lose": {
        "tr": "🤖 Ben kazandım! Bir dahaki sefere...",
        "en": "🤖 I won! Maybe next time...",
        "ru": "🤖 Я выиграл(а)! В следующий раз..."
    },
    "xox_draw": {
        "tr": "🤝 Berabere!",
        "en": "🤝 It's a draw!",
        "ru": "🤝 Ничья!"
    },
    "xox_invalid_move": {
        "tr": "Bu kutu dolu veya oyun bitti.",
        "en": "This box is taken or game is over.",
        "ru": "Эта клетка занята или игра окончена."
    },
    "xox_bot_moved": {
        "tr": "🤖 Bot hamle yaptı! Sıra sende.",
        "en": "🤖 Bot played! Your turn.",
        "ru": "🤖 Бот сделал ход! Ваша очередь."
    },
    
    # --- VIDEO DOWNLOADER ---
    "video_downloader_menu_prompt": {
        "tr": "📥 Video İndirici\n\nHangi platformdan indirmek istiyorsunuz?",
        "en": "📥 Video Downloader\n\nWhich platform do you want to download from?",
        "ru": "📥 Загрузчик Видео\n\nС какой платформы вы хотите скачать?"
    },
    "video_downloader_prompt_link": {
        "tr": "🔗 Lütfen {platform} video linkini gönderin:",
        "en": "🔗 Please send the {platform} video link:",
        "ru": "🔗 Пожалуйста, отправьте ссылку на видео {platform}:"
    },
    "video_downloading": {
        "tr": "⏳ Video indiriliyor, lütfen bekleyin...",
        "en": "⏳ Downloading video, please wait...",
        "ru": "⏳ Загрузка видео, пожалуйста подождите..."
    },
    "video_download_success": {
        "tr": "✅ Video başarıyla indirildi!",
        "en": "✅ Video downloaded successfully!",
        "ru": "✅ Видео успешно загружено!"
    },
    "video_download_error": {
        "tr": "❌ Video indirilemedi. Link geçersiz olabilir veya içerik private olabilir.\nHata: {error}",
        "en": "❌ Could not download video. The link may be invalid or the content may be private.\nError: {error}",
        "ru": "❌ Не удалось загрузить видео. Ссылка может быть недействительной или контент приватный.\nОшибка: {error}"
    },
    "video_file_too_large": {
        "tr": "⚠️ Video dosyası çok büyük (50MB üzeri). Telegram limiti aşıyor.",
        "en": "⚠️ Video file is too large (over 50MB). Exceeds Telegram limit.",
        "ru": "⚠️ Видеофайл слишком большой (более 50МБ). Превышен лимит Telegram."
    },
    "video_invalid_link": {
        "tr": "⚠️ Geçersiz link. Lütfen geçerli bir {platform} linki gönderin.",
        "en": "⚠️ Invalid link. Please send a valid {platform} link.",
        "ru": "⚠️ Недействительная ссылка. Отправьте действительную ссылку {platform}."
    },
    "format_selection_prompt": {
        "tr": "🎥 Hangi formatı indirmek istiyorsunuz?",
        "en": "🎥 Which format do you want to download?",
        "ru": "🎥 В каком формате вы хотите скачать?"
    },
    "audio_downloading": {
        "tr": "⏳ Ses dosyası indiriliyor, lütfen bekleyin...",
        "en": "⏳ Downloading audio, please wait...",
        "ru": "⏳ Загрузка аудио, пожалуйста подождите..."
    },
    "audio_download_success": {
        "tr": "✅ Ses dosyası başarıyla indirildi!",
        "en": "✅ Audio downloaded successfully!",
        "ru": "✅ Аудио успешно загружено!"
    },
    
    # --- AI ASISTAN ---
    "ai_menu_prompt": {
        "tr": "🤖 *AI Asistan*\n\nYapay zeka destekli sohbet asistanınız.\nSorularınızı sorun, yardım isteyin!\n\n📊 Günlük hakkınız: {remaining}/{limit}",
        "en": "🤖 *AI Assistant*\n\nYour AI-powered chat assistant.\nAsk questions, get help!\n\n📊 Daily quota: {remaining}/{limit}",
        "ru": "🤖 *AI Ассистент*\n\nВаш чат-ассистент на базе ИИ.\nЗадавайте вопросы, получайте помощь!\n\n📊 Дневной лимит: {remaining}/{limit}"
    },
    "ai_menu_prompt_admin": {
        "tr": "🤖 *AI Asistan (Admin)*\n\nYapay zeka destekli sohbet asistanınız.\n\n⚡️ *Durum: ♾️ Sınırsız Mod*",
        "en": "🤖 *AI Assistant (Admin)*\n\nYour AI-powered chat assistant.\n\n⚡️ *Status: ♾️ Unlimited Mode*",
        "ru": "🤖 *AI Ассистент (Admin)*\n\nВаш чат-ассистент на базе ИИ.\n\n⚡️ *Статус: ♾️ Безлимит*"
    },
    "ai_chat_started": {
        "tr": "🧠 AI sohbet modu başladı!\n\nBana her şeyi sorabilirsin. Bitirmek için aşağıdaki butonu kullan.",
        "en": "🧠 AI chat mode started!\n\nYou can ask me anything. Use the button below to end.",
        "ru": "🧠 Режим AI чата начат!\n\nВы можете спросить меня о чём угодно. Используйте кнопку ниже, чтобы завершить."
    },
    "ai_chat_ended": {
        "tr": "👋 AI sohbeti sonlandırıldı. Ana menüye döndünüz.",
        "en": "👋 AI chat ended. You're back to main menu.",
        "ru": "👋 AI чат завершён. Вы вернулись в главное меню."
    },
    "ai_thinking": {
        "tr": "🤔 Düşünüyorum...",
        "en": "🤔 Thinking...",
        "ru": "🤔 Думаю..."
    },
    "ai_limit_reached": {
        "tr": "⚠️ Günlük AI mesaj limitinize ulaştınız (30/30).\nYarın tekrar deneyebilirsiniz!",
        "en": "⚠️ You've reached your daily AI message limit (30/30).\nTry again tomorrow!",
        "ru": "⚠️ Вы достигли дневного лимита AI сообщений (30/30).\nПопробуйте завтра!"
    },
    "ai_remaining_footer": {
        "tr": "💬 Hak: {status}",
        "en": "💬 Quota: {status}",
        "ru": "💬 Лимит: {status}"
    },
    "ai_unlimited_text": {
        "tr": "♾️ Sınırsız",
        "en": "♾️ Unlimited",
        "ru": "♾️ Безлимит"
    },
    "ai_error": {
        "tr": "❌ AI yanıt verirken bir hata oluştu. Lütfen tekrar deneyin.",
        "en": "❌ An error occurred while AI was responding. Please try again.",
        "ru": "❌ Произошла ошибка при ответе AI. Пожалуйста, попробуйте снова."
    },
    "ai_api_error": {
        "tr": "❌ AI servisi şu an kullanılamıyor. Lütfen daha sonra tekrar deneyin.",
        "en": "❌ AI service is currently unavailable. Please try again later.",
        "ru": "❌ Сервис AI временно недоступен. Попробуйте позже."
    },
    
    # --- METRO İSTANBUL ---
    "metro_menu_prompt": {
        "tr": "🚇 *Metro İstanbul*\n\n🚆 Hangi hatta seyahat edeceksiniz?\n\n_ℹ️ Veriler İBB'den alınmaktadır._",
        "en": "🚇 *Metro Istanbul*\n\nWhich line will you travel on?\n\n_ℹ️ Data sourced from IBB._",
        "ru": "🚇 *Метро Стамбул*\n\nНа какой линии вы будете ехать?\n\n_ℹ️ Данные из IBB._"
    },
    "metro_select_station": {
        "tr": "🚇 *{line}*\n\n📍 Hangi istasyonu kullanacaksınız?",
        "en": "🚇 *{line}*\n\n📍 Which station will you use?",
        "ru": "🚇 *{line}*\n\n📍 Какую станцию вы будете использовать?"
    },
    "metro_select_direction": {
        "tr": "➡️ Gideceğiniz yönü seçin:",
        "en": "➡️ Select your destination direction:",
        "ru": "➡️ Выберите направление:"
    },
    "metro_departures_header": {
        "tr": "🚇 *{line} - {station}*\n📍 {direction} Yönü\n\n_Yaklaşan seferler:_",
        "en": "🚇 *{line} - {station}*\n📍 Direction: {direction}\n\n_Upcoming departures:_",
        "ru": "🚇 *{line} - {station}*\n📍 Направление: {direction}\n\n_Ближайшие отправления:_"
    },
    "metro_no_departures": {
        "tr": "⚠️ Bu yön için yaklaşan sefer bulunamadı.",
        "en": "⚠️ No upcoming departures found for this direction.",
        "ru": "⚠️ Ближайших отправлений в этом направлении не найдено."
    },
    "metro_api_error": {
        "tr": "❌ Metro verisi alınamadı. Lütfen tekrar deneyin.",
        "en": "❌ Could not fetch metro data. Please try again.",
        "ru": "❌ Не удалось получить данные метро. Попробуйте снова."
    }
}

# --- YENİLENMİŞ ANA MENÜ (AI Asistan eklendi) ---
MAIN_BUTTONS = {
    "tr": [["🛠 Araçlar", "🎮 Oyun Odası"], ["🌐 Dil Değiştir", "👨‍💻 Geliştirici"], ["🤖 AI Asistan (Beta)", "❓ Nasıl Kullanılır?"]],
    "en": [["🛠 Tools", "🎮 Game Room"], ["🌐 Change Language", "👨‍💻 Developer"], ["🤖 AI Assistant (Beta)", "❓ How to Use?"]],
    "ru": [["🛠 Инструменты", "🎮 Игровая Комната"], ["🌐 Сменить Язык", "👨‍💻 Разработчик"], ["🤖 AI Ассистент (Бета)", "❓ Как использовать?"]]
}

TOOLS_BUTTONS = {
    "tr": [["📝 Notlar", "⏰ Hatırlatıcı"], ["📷 QR Kod", "📄 PDF Dönüştürücü"], ["☀️ Hava Durumu", "📥 Video İndir"], ["🚇 Canlı Metro İstanbul", "🔙 Ana Menü"]],
    "en": [["📝 Notes", "⏰ Reminder"], ["📷 QR Code", "📄 PDF Converter"], ["☀️ Weather", "📥 Video Download"], ["🚇 Live Metro Istanbul", "🔙 Main Menu"]],
    "ru": [["📝 Заметки", "⏰ Напоминание"], ["📷 QR-код", "📄 Конвертер PDF"], ["☀️ Погода", "📥 Скачать Видео"], ["🚇 Метро Стамбул", "🔙 Главное Меню"]]
}

# --- VIDEO DOWNLOADER MENÜSÜ ---
VIDEO_DOWNLOADER_BUTTONS = {
    "tr": [["📱 TikTok", "🐦 Twitter/X"], ["📸 Instagram"], ["🔙 Araçlar Menüsü"]],
    "en": [["📱 TikTok", "🐦 Twitter/X"], ["📸 Instagram"], ["🔙 Tools Menu"]],
    "ru": [["📱 TikTok", "🐦 Twitter/X"], ["📸 Instagram"], ["🔙 Меню Инструментов"]]
}

# --- FORMAT SEÇİM MENÜSÜ ---
FORMAT_SELECTION_BUTTONS = {
    "tr": [["🎥 Video (MP4)", "🎵 Ses (MP3)"], ["🔙 Platform Seçimi"]],
    "en": [["🎥 Video (MP4)", "🎵 Audio (MP3)"], ["🔙 Platform Selection"]],
    "ru": [["🎥 Видео (MP4)", "🎵 Аудио (MP3)"], ["🔙 Выбор Платформы"]]
}

# --- YENİ OYUN MENÜSÜ ---
# Karar çarkı kaldırıldı, düzen 2x2 yapıldı
GAMES_BUTTONS = {
    "tr": [["❌⭕ XOX", "🎲 Zar"], ["🪙 Yazı Tura", "🪨📄✂️ T-K-M"], ["🔙 Ana Menü"]],
    "en": [["❌⭕ XOX", "🎲 Dice"], ["🪙 Coinflip", "🪨📄✂️ R-P-S"], ["🔙 Main Menu"]],
    "ru": [["❌⭕ XOX", "🎲 Кубик"], ["🪙 Монета", "🪨📄✂️ К-Б-Н"], ["🔙 Главное Меню"]]
}

# --- NOTLAR MENÜSÜ ---
# --- NOTLAR MENÜSÜ ---
NOTES_BUTTONS = {
    "tr": [["➕ Not Ekle", "✏️ Not Düzenle"], ["📋 Tüm Notları Göster", "🗑️ Not Sil"], ["🔙 Araçlar Menüsü"]],
    "en": [["➕ Add Note", "✏️ Edit Note"], ["📋 Show All Notes", "🗑️ Delete Note"], ["🔙 Tools Menu"]],
    "ru": [["➕ Добавить", "✏️ Изменить"], ["📋 Показать Все", "🗑️ Удалить"], ["🔙 Меню Инструментов"]]
}

DELETE_NOTES_BUTTONS = {
    "tr": [["✍️ Not Seçerek Sil"], ["🔙 Notlar Menüsü"]],
    "en": [["✍️ Select Note to Delete"], ["🔙 Notes Menu"]],
    "ru": [["✍️ Удалить По Номеру"], ["🔙 Меню Заметок"]]
}

TKM_BUTTONS = {
    "tr": [["🪨 Taş"], ["📄 Kağıt"], ["✂️ Makas"], ["🔙 Oyun Odası"]],
    "en": [["🪨 Rock"], ["📄 Paper",], ["✂️ Scissors"], ["🔙 Game Room"]],
    "ru": [["🪨 Камень"], ["📄 Бумага"], ["✂️ Ножницы"], ["🔙 Игровая Комната"]]
}

PDF_CONVERTER_BUTTONS = {
    "tr": [["📝 Metinden PDF'e"], ["🖼️ Resimden PDF'e"], ["📄 Belgeden PDF'e"], ["🔙 Araçlar Menüsü"]],
    "en": [["📝 Text to PDF"], ["🖼️ Image to PDF"], ["📄 Document to PDF"], ["🔙 Tools Menu"]],
    "ru": [["📝 Текст в PDF"], ["🖼️ Изображение в PDF"], ["📄 Документ в PDF"], ["🔙 Меню Инструментов"]]
}

INPUT_BACK_BUTTONS = {
    "tr": [["🔙 Araçlar Menüsü"]],
    "en": [["🔙 Tools Menu"]],
    "ru": [["🔙 Меню Инструментов"]]
}

REMINDER_BUTTONS = {
    "tr": [["➕ Hatırlatıcı Ekle"], ["📋 Hatırlatıcıları Göster"], ["🗑️ Hatırlatıcı Sil"], ["🔙 Araçlar Menüsü"]],
    "en": [["➕ Add Reminder"], ["📋 Show Reminders"], ["🗑️ Delete Reminder"], ["🔙 Tools Menu"]],
    "ru": [["➕ Добавить Напоминание"], ["📋 Показать Напоминания"], ["🗑️ Удалить Напоминание"], ["🔙 Меню Инструментов"]]
}

# --- TÜRKÇE LOWERCASE HELPER ---
# common.py'den import edildi (turkish_lower)

# --- OTOMATİK BUTTON MAPPING ÜRETİCİ ---
# common.py'den import edildi (generate_mappings_from_buttons)

# --- OTOMATİK ÜRETİLEN MAPPINGS ---
# Bu mappings, yukarıdaki BUTTONS sözlüklerinden otomatik üretilir
AUTO_MAPPINGS = {
    # Ana menü butonları
    "tools_main_button": generate_mappings_from_buttons({"tr": [["🛠 Araçlar"]], "en": [["🛠 Tools"]], "ru": [["🛠 Инструменты"]]}),
    "games_main_button": generate_mappings_from_buttons({"tr": [["🎮 Oyun Odası"]], "en": [["🎮 Game Room"]], "ru": [["🎮 Игровая Комната"]]}),
    "notes_main_button": generate_mappings_from_buttons({"tr": [["📝 Notlar"]], "en": [["📝 Notes"]], "ru": [["📝 Заметки"]]}),
    "language": generate_mappings_from_buttons({"tr": [["🌐 Dil Değiştir"]], "en": [["🌐 Change Language"]], "ru": [["🌐 Сменить Язык"]]}),
    "developer_main_button": generate_mappings_from_buttons({"tr": [["👨‍💻 Geliştirici"]], "en": [["👨‍💻 Developer"]], "ru": [["👨‍💻 Разработчик"]]}),
    "ai_main_button": generate_mappings_from_buttons({"tr": [["🤖 AI Asistan (Beta)"]], "en": [["🤖 AI Assistant (Beta)"]], "ru": [["🤖 AI Ассистент (Бета)"]]}),
    "help_button": generate_mappings_from_buttons({"tr": [["❓ Nasıl Kullanılır?"]], "en": [["❓ How to Use?"]], "ru": [["❓ Как использовать?"]]}),
    
    # Araçlar menüsü
    "reminder": generate_mappings_from_buttons({"tr": [["⏰ Hatırlatıcı"]], "en": [["⏰ Reminder"]], "ru": [["⏰ Напоминание"]]}),
    "qrcode_button": generate_mappings_from_buttons({"tr": [["📷 QR Kod"]], "en": [["📷 QR Code"]], "ru": [["📷 QR-код"]]}),
    "pdf_converter_main_button": generate_mappings_from_buttons({"tr": [["📄 PDF Dönüştürücü"]], "en": [["📄 PDF Converter"]], "ru": [["📄 Конвертер PDF"]]}),
    "weather_main_button": generate_mappings_from_buttons({"tr": [["☀️ Hava Durumu"]], "en": [["☀️ Weather"]], "ru": [["☀️ Погода"]]}),
    "video_downloader_main_button": generate_mappings_from_buttons({"tr": [["📥 Video İndir"]], "en": [["📥 Video Download"]], "ru": [["📥 Скачать Видео"]]}),
    "metro_main_button": generate_mappings_from_buttons({"tr": [["🚇 Canlı Metro İstanbul"]], "en": [["🚇 Live Metro Istanbul"]], "ru": [["🚇 Метро Стамбул"]]}),
    
    # Oyunlar menüsü
    "xox_game": generate_mappings_from_buttons({"tr": [["❌⭕ XOX"]], "en": [["❌⭕ XOX"]], "ru": [["❌⭕ XOX"]]}),
    "dice": generate_mappings_from_buttons({"tr": [["🎲 Zar"]], "en": [["🎲 Dice"]], "ru": [["🎲 Кубик"]]}),
    "coinflip": generate_mappings_from_buttons({"tr": [["🪙 Yazı Tura"]], "en": [["🪙 Coinflip"]], "ru": [["🪙 Монета"]]}),
    "tkm_main": generate_mappings_from_buttons({"tr": [["🪨📄✂️ T-K-M"]], "en": [["🪨📄✂️ R-P-S"]], "ru": [["🪨📄✂️ К-Б-Н"]]}),
    
    # Notlar menüsü
    "add_note_button": generate_mappings_from_buttons({"tr": [["➕ Not Ekle"]], "en": [["➕ Add Note"]], "ru": [["➕ Добавить"]]}),
    "edit_note_button": generate_mappings_from_buttons({"tr": [["✏️ Not Düzenle"]], "en": [["✏️ Edit Note"]], "ru": [["✏️ Изменить"]]}),
    "show_all_notes_button": generate_mappings_from_buttons({"tr": [["📋 Tüm Notları Göster"]], "en": [["📋 Show All Notes"]], "ru": [["📋 Показать Все"]]}),
    "delete_note_button": generate_mappings_from_buttons({"tr": [["🗑️ Not Sil"]], "en": [["🗑️ Delete Note"]], "ru": [["🗑️ Удалить"]]}),
    "select_delete_note_button": generate_mappings_from_buttons({"tr": [["✍️ Not Seçerek Sil"]], "en": [["✍️ Select Note to Delete"]], "ru": [["✍️ Удалить По Номеру"]]}),
    
    # TKM butonları
    "tkm_rock": generate_mappings_from_buttons({"tr": [["🪨 Taş"]], "en": [["🪨 Rock"]], "ru": [["🪨 Камень"]]}),
    "tkm_paper": generate_mappings_from_buttons({"tr": [["📄 Kağıt"]], "en": [["📄 Paper"]], "ru": [["📄 Бумага"]]}),
    "tkm_scissors": generate_mappings_from_buttons({"tr": [["✂️ Makas"]], "en": [["✂️ Scissors"]], "ru": [["✂️ Ножницы"]]}),
    
    # PDF menüsü
    "text_to_pdf_button": generate_mappings_from_buttons({"tr": [["📝 Metinden PDF'e"]], "en": [["📝 Text to PDF"]], "ru": [["📝 Текст в PDF"]]}),
    "image_to_pdf_button": generate_mappings_from_buttons({"tr": [["🖼️ Resimden PDF'e"]], "en": [["🖼️ Image to PDF"]], "ru": [["🖼️ Изображение в PDF"]]}),
    "document_to_pdf_button": generate_mappings_from_buttons({"tr": [["📄 Belgeden PDF'e"]], "en": [["📄 Document to PDF"]], "ru": [["📄 Документ в PDF"]]}),
    
    # Hatırlatıcı menüsü
    "add_reminder_button": generate_mappings_from_buttons({"tr": [["➕ Hatırlatıcı Ekle"]], "en": [["➕ Add Reminder"]], "ru": [["➕ Добавить Напоминание"]]}),
    "show_reminders_button": generate_mappings_from_buttons({"tr": [["📋 Hatırlatıcıları Göster"]], "en": [["📋 Show Reminders"]], "ru": [["📋 Показать Напоминания"]]}),
    "delete_reminder_button": generate_mappings_from_buttons({"tr": [["🗑️ Hatırlatıcı Sil"]], "en": [["🗑️ Delete Reminder"]], "ru": [["🗑️ Удалить Напоминание"]]}),
    
    # Video downloader
    "video_platform_tiktok": generate_mappings_from_buttons({"all": [["📱 TikTok"]]}),
    "video_platform_twitter": generate_mappings_from_buttons({"all": [["🐦 Twitter/X"]]}),
    "video_platform_instagram": generate_mappings_from_buttons({"all": [["📸 Instagram"]]}),
    "format_video": generate_mappings_from_buttons({"tr": [["🎥 Video (MP4)"]], "en": [["🎥 Video (MP4)"]], "ru": [["🎥 Видео (MP4)"]]}),
    "format_audio": generate_mappings_from_buttons({"tr": [["🎵 Ses (MP3)"]], "en": [["🎵 Audio (MP3)"]], "ru": [["🎵 Аудио (MP3)"]]}),
    "back_to_platform": generate_mappings_from_buttons({"tr": [["🔙 Platform Seçimi"]], "en": [["🔙 Platform Selection"]], "ru": [["🔙 Выбор Платформы"]]}),
    
    # AI Asistan
    "ai_start_chat": generate_mappings_from_buttons({"tr": [["🧠 Sohbete Başla"]], "en": [["🧠 Start Chat"]], "ru": [["🧠 Начать Чат"]]}),
    "ai_end_chat": generate_mappings_from_buttons({"tr": [["🔚 Sohbeti Bitir"]], "en": [["🔚 End Chat"]], "ru": [["🔚 Завершить Чат"]]}),
    "ai_back_to_menu": generate_mappings_from_buttons({"tr": [["🔙 Ana Menü"]], "en": [["🔙 Main Menu"]], "ru": [["🔙 Главное Меню"]]}),
}

# --- MANUEL MAPPINGS (Özel durumlar için) ---
# Bazı butonlar birden fazla varyant gerektirdiği için manuel tutulur
MANUAL_MAPPINGS = {
    "menu": {"🏠 menüye dön", "🏠 back to menu", "🏠 назад в меню", "🔙 geri", "🔙 back", "🔙 назад", "🔙 ana menü", "🔙 main menu", "🔙 главное меню"},
    "back_to_tools": {"🔙 araçlar menüsü", "🔙 tools menu", "🔙 меню инструментов"},
    "back_to_games": {"🔙 oyun odası", "🔙 game room", "🔙 игровая комната"},
    "back_to_notes": {"🔙 notlar menüsü", "🔙 notes menu", "🔙 меню заметок"},
    "admin_panel_button": {"🔒 yönetim", "🔒 admin", "🔒 управление"},
}

# --- BİRLEŞTİRİLMİŞ BUTTON_MAPPINGS ---
# Otomatik ve manuel mappings birleştirilir
BUTTON_MAPPINGS = {**AUTO_MAPPINGS, **MANUAL_MAPPINGS}