# Sosyal Medya Linkleri
SOCIAL_MEDIA_LINKS = {
    "website": "https://kagansametdurmus.com.tr", 
    "instagram": "https://www.instagram.com/kagandms/",
    "telegram": "https://t.me/kagandms",
    "linkedin": "https://www.linkedin.com/in/kağan-samet-durmuş-37676332b/"
}

CITY_NAMES_TRANSLATED = {
    "tr": {"Istanbul": "Istanbul", "Moscow": "Moskova", "London": "Londra", "New York": "New York", "Beijing": "Pekin"}, 
    "en": {"Istanbul": "Istanbul", "Moscow": "Moscow", "London": "London", "New York": "New York", "Beijing": "Beijing"}, 
    "ru": {"Istanbul": "Стамбул", "Moscow": "Москва", "London": "Лондон", "New York": "Нью-Йорк", "Beijing": "Пекин"} 
}

TEXTS = {
    "start": {
        "tr": "Merhaba! Ben senin kişisel asistan botunum. Komutlar için /menu yazabilirsin.",
        "en": "Hello! I am your personal assistant bot. You can type /menu for commands.",
        "ru": "Привет, я твой личный помощник. Ты можешь ввести /menu для команд."
    },
    "menu_prompt": {
        "tr": "Menüden bir işlem seçin 👇",
        "en": "Please choose an action from the menu 👇",
        "ru": "Пожалуйста, выберите действие из меню 👇"
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
    "language_set": {
        "tr": "Dil Türkçe olarak ayarlandı.",
        "en": "Language set to English.",
        "ru": "Язык установлен на русский."
    },
    "no_notes": {
        "tr": "Henüz kayıtlı notunuz yok.",
        "en": "You have no saved notes yet.",
        "ru": "У вас еще нет сохраненных заметок."
    },
    "notes_header": {
        "tr": "Kayıtlı Notlarınız:\n",
        "en": "Your saved notes:\n",
        "ru": "Ваши сохраненные заметки:\n"
    },
    "invalid_note_number": {
        "tr": "Geçersiz not numarası.",
        "en": "Invalid note number.",
        "ru": "Неверный номер заметки."
    },
    "unknown_command": {
        "tr": "Üzgünüm, bu komutu anlayamadım. Lütfen /menu yazarak komutları görüntüleyin.",
        "en": "Sorry, I didn't understand that command. Please type /menu to see available commands.",
        "ru": "Извините, я не понял эту команду. Пожалуйста, введите /menu для списка команд."
    },
    "prompt_new_note": {
        "tr": "Lütfen notunuzu yazın:",
        "en": "Please write your note:",
        "ru": "Пожалуйста, напишите заметку:"
    },
    "addnote_no_content": {
        "tr": "Lütfen not almak için /addnote komutundan sonra notunu yaz.",
        "en": "Please write your note after /addnote command.",
        "ru": "Please write your note after /addnote command."
    },
    "note_saved": {
        "tr": "Notunuz kaydedildi: ",
        "en": "Your note has been saved: ",
        "ru": "Ваша заметка сохранена: "
    },
    "note_deleted": {
        "tr": "not silindi",
        "en": "note deleted",
        "ru": "заметка удалена"
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
        "tr": "Lütfen bir saat ve mesaj girin. Örn: `/remind 14:30 toplantı` veya `10:00 2025-12-31 yeni yıl`",
        "en": "Please enter a time and message. Ex: `/remind 14:30 meeting` or `10:00 2025-12-31 new year`",
        "ru": "Пожалуйста, введите время ve mesaj girin. Örn: `/remind 14:30 toplantı` veya `10:00 2025-12-31 yeni yıl`"
    },
    "remind_prompt_input": {
        "tr": "Lütfen hatırlatıcı için saati ve mesajı girin. Örn: `14:30 toplantı` veya `10:00 2025-12-31 yeni yıl`",
        "en": "Please enter the time and message for the reminder. Ex: `14:30 meeting` or `10:00 2025-12-31 new year`",
        "ru": "Пожалуйста, введите время и сообщение для напоминания. Пример: `14:30 встреча` или `10:00 2025-12-31 новый год`"
    },
    "reminder_set": {
        "tr": "⏰ Hatırlatıcı ayarlandı: {time_str} - {message}\nKalan süre: {remaining_time}",
        "en": "⏰ Reminder set for {time_str} - {message}\nRemaining time: {remaining_time}",
        "ru": "⏰ Напоминание установлено: {time_str} - {message}\nОставшееся время: {remaining_time}"
    },
    "error_occurred": {
        "tr": "Hata oluştu: ",
        "en": "An error occurred: ",
        "ru": "Произошла ошибка: "
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
    "decision_wheel_usage": {
        "tr": "Lütfen en az iki seçenek girin. Örn: `/decisionwheel kahve çay su`",
        "en": "Please enter at least two options. Example: `/decisionwheel coffee tea water`",
        "ru": "Пожалуйста, введите как минимум два варианта. Пример: `/decisionwheel кофе чай вода`"
    },
    "decision_wheel_chosen": {
        "tr": "Karar çarkı seçti: ",
        "en": "The wheel has chosen: ",
        "ru": "Колесо выбрало: "
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
        "tr": "PDF dönüştürme seçenekleri:",
        "en": "PDF conversion options:",
        "ru": "Параметры конвертации PDF:"
    },
    "prompt_text_for_pdf": {
        "tr": "Lütfen PDF'e dönüştürmek istediğiniz metni yazın:",
        "en": "Please type the text you want to convert to PDF:",
        "ru": "Пожалуйста, введите текст для конвертации в PDF:"
    },
    "prompt_file_for_pdf": {
        "tr": "Lütfen PDF'e dönüştürmek istediğiniz dosyayı (resim, DOCX, TXT) gönderin:",
        "en": "Please send the file (image, DOCX, TXT) you want to convert to PDF:",
        "ru": "Пожалуйста, отправьте файл (изображение, DOCX, TXT) для конвертации в PDF:"
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
        "tr": "Lütfen girişinizi bekliyorum...",
        "en": "Waiting for your input...",
        "ru": "Ожидаю ваш ввод..."
    },
    "docx_conversion_warning": {
        "tr": "DOCX'ten PDF'e dönüştürme için sunucuda Microsoft Word veya LibreOffice kurulu olması gerekebilir. Kurulum yoksa bu işlem başarısız olabilir.",
        "en": "DOCX to PDF conversion might require Microsoft Word or LibreOffice installed on the server. The operation may fail if not present.",
        "ru": "Для конвертации DOCX в PDF может потребоваться установка Microsoft Word или LibreOffice на сервере. Операция может завершиться неудачей, если они отсутствуют."
    },
    "weather_prompt_city": {
        "tr": "Hava durumunu öğrenmek istediğiniz şehrin adını girin:",
        "en": "Please enter the name of the city for which you want to get the weather:",
        "ru": "Пожалуйста, введите название города, для которого вы хотите узнать погоду:"
    },
    "weather_current": {
        "tr": "📍 {city}\n🌡️ Sıcaklık: {temp}°C\n❔ Hissedilen: {feels_like}°C\n✨ Durum: {description}\n💧 Nem: %{humidity}\n💨 Rüzgar: {wind_speed} m/s",
        "en": "📍 {city}\n🌡️ Temperature: {temp}°C\n❔ Feels like: {feels_like}°C\n✨ Condition: {description}\n💧 Humidity: %{humidity}\n💨 Wind: {wind_speed} m/s",
        "ru": "📍 {city}\n🌡️ Температура: {temp}°C\n❔ Ощущается как: {feels_like}°C\n✨ Условия: {description}\n💧 Влажность: %{humidity}\n💨 Ветер: {wind_speed} м/с"
    },
    "weather_city_not_found": {
        "tr": "Üzgünüm, '{city}' şehri için hava durumu bilgisi bulunamadı. Lütfen şehir adını doğru yazdığınızdan emin olun.",
        "en": "Sorry, weather information for '{city}' not found. Please make sure you spelled the city name correctly.",
        "ru": "Извините, информация о погоде для города '{city}' не найдена. Пожалуйста, убедитесь, что вы правильно ввели название города."
    },
    "weather_api_error": {
        "tr": "Hava durumu bilgisi alınırken bir hata oluştu. Lütfen daha sonra tekrar deneyin.",
        "en": "An error occurred while fetching weather information. Please try again later.",
        "ru": "Произошла ошибка при получении информации о погоде. Пожалуйста, попробуйте позже."
    },
    "weather_select_city": { 
        "tr": "Hava durumunu öğrenmek istediğiniz şehri seçin:",
        "en": "Select the city for which you want to get the weather:",
        "ru": "Выберите город, для которого вы хотите узнать погоду:"
    },
    "developer_info_prompt": { 
        "tr": "Sosyal medya hesaplarıma aşağıdaki bağlantılardan ulaşabilirsiniz:",
        "en": "You can reach my social media accounts via the links below:",
        "ru": "You can reach my social media accounts via the links below:"
    },
    "reminder_menu_prompt": {
        "tr": "Hatırlatıcılar menüsünden bir işlem seçin:",
        "en": "Choose an action from the reminders menu:",
        "ru": "Выберите действие из меню напоминаний:"
    },
    "no_reminders": {
        "tr": "Henüz kayıtlı hatırlatıcınız yok.",
        "en": "You have no saved reminders yet.",
        "ru": "У вас еще нет сохраненных напоминаний."
    },
    "reminders_header": {
        "tr": "Kayıtlı Hatırlatıcılarınız:\n",
        "en": "Your saved reminders:\n",
        "ru": "Ваши сохраненные reminders:\n"
    },
    "prompt_select_reminder_to_delete": {
        "tr": "Lütfen silmek istediğiniz hatırlatıcıyı seçin:",
        "en": "Please select the reminder you want to delete:",
        "ru": "Пожалуйста, выберите напоминание, которое хотите удалить:"
    },
    "reminder_deleted": {
        "tr": "hatırlatıcı silindi.",
        "en": "reminder deleted.",
        "ru": "напоминание удалено."
    },
    "invalid_reminder_number": {
        "tr": "Geçersiz hatırlatıcı numarası.",
        "en": "Invalid reminder number.",
        "ru": "Неверный номер напоминания."
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
    }
}

# --- BUTTONS ---
MAIN_BUTTONS = {
    "tr": [["📝 Notlar", "🎲 Zar", "🪙 Yazı Tura"], ["🕒 Saat", "⏰ Hatırlatıcı", "T-K-M 🪨📄✂️"], ["📷 QR Kod Oluştur", "📄 PDF Dönüştürücü", "☀️ Hava Durumu"], ["🌐 Dil Değiştir", "👨‍💻 Geliştirici"]],
    "en": [["📝 Notes", "🎲 Dice", "🪙 Coinflip"], ["🕒 Time", "⏰ Reminder", "R-P-S 🪨📄✂️"], ["📷 Create QR Code", "📄 PDF Converter", "☀️ Weather"], ["🌐 Change Language", "👨‍💻 Developer"]],
    "ru": [["📝 Заметки", "🎲 Кубик", "🪙 Монета"], ["🕒 Время", "⏰ Напоминание", "К-Б-Н 🪨📄✂️"], ["📷 Создать QR-код", "📄 Конвертер PDF", "☀️ Погода"], ["🌐 Сменить язык", "👨‍💻 Разработчик"]],
}

NOTES_BUTTONS = {
    "tr": [["➕ Not Ekle"], ["📋 Tüm Notları Göster"], ["🗑️ Not Sil"], ["🔙 Geri"]],
    "en": [["➕ Add Note"], ["📋 Show All Notes"], ["🗑️ Delete Note"], ["🔙 Back"]],
    "ru": [["➕ Добавить Заметку"], ["📋 Показать Все Заметки"], ["🗑️ Удалить Заметку"], ["🔙 Назад"]]
}

DELETE_NOTES_BUTTONS = {
    "tr": [["✍️ Not Seçerek Sil"], ["🔙 Geri"]],
    "en": [["✍️ Select Note to Delete"], ["🔙 Back"]],
    "ru": [["✍️ Удалить По Номеру"], ["🔙 Назад"]]
}

TKM_BUTTONS = {
    "tr": [["🪨 Taş"], ["📄 Kağıt"], ["✂️ Makas"], ["🔙 Geri"]],
    "en": [["🪨 Rock"], ["📄 Paper",], ["✂️ Scissors"], ["🔙 Back"]],
    "ru": [["🪨 Камень"], ["📄 Бумага"], ["✂️ Ножницы"], ["🔙 Назад"]]
}

PDF_CONVERTER_BUTTONS = {
    "tr": [["📝 Metinden PDF'e"], ["🖼️ Resimden PDF'e"], ["📄 Belgeden PDF'e"], ["🔙 Geri"]],
    "en": [["📝 Text to PDF"], ["🖼️ Image to PDF"], ["📄 Document to PDF"], ["🔙 Back"]],
    "ru": [["📝 Текст в PDF"], ["🖼️ Изображение в PDF"], ["📄 Документ в PDF"], ["🔙 Назад"]]
}

INPUT_BACK_BUTTONS = {
    "tr": [["🔙 Geri"]],
    "en": [["🔙 Back"]],
    "ru": [["🔙 Назад"]]
}

REMINDER_BUTTONS = {
    "tr": [["➕ Hatırlatıcı Ekle"], ["📋 Hatırlatıcıları Göster"], ["🗑️ Hatırlatıcı Sil"], ["🔙 Geri"]],
    "en": [["➕ Add Reminder"], ["📋 Show Reminders"], ["🗑️ Delete Reminder"], ["🔙 Back"]],
    "ru": [["➕ Добавить Напоминание"], ["📋 Показать Напоминания"], ["🗑️ Удалить Напоминание"], ["🔙 Назад"]]
}

BUTTON_MAPPINGS = {
    "notes_main_button": {"📝 notlar", "📝 notes", "📝 заметки"},
    "dice": {"🎲 zar", "🎲 dice", "🎲 кубик"},
    "coinflip": {"🪙 yazı tura", "🪙 coinflip", "🪙 монета"},
    "time": {"🕒 saat", "🕒 time", "🕒 время"},
    "reminder": {"⏰ hatırlatıcı", "⏰ reminder", "⏰ напоминание"},
    "tkm_main": {"t-k-m 🪨📄✂️", "r-p-s 🪨📄✂️", "к-б-н 🪨📄✂️"},
    "language": {"🌐 dil değiştir", "🌐 change language", "🌐 сменить язык"},
    "play_again": {"🔁 tekrar oyna", "🔁 play again", "🔁 сыграть снова"},
    "menu": {"🏠 menüye dön", "🏠 back to menu", "🏠 назад в меню", "🔙 geri", "🔙 back", "🔙 назад"},
    "add_note_button": {"➕ not ekle", "➕ add note", "➕ добавить заметку"},
    "show_all_notes_button": {"📋 tüm notları göster", "📋 show all notes", "📋 показать все заметки"},
    "delete_note_button": {"🗑️ not sil", "🗑️ delete note", "🗑️ удалить заметку"},
    "select_delete_note_button": {"✍️ not seçerek sil", "✍️ select note to delete", "✍️ удалить по номеру"},
    "tkm_rock": {"🪨 taş", "🪨 rock", "🪨 камень"},
    "tkm_paper": {"📄 kağıt", "📄 paper", "📄 бумага"},
    "tkm_scissors": {"✂️ makas", "✂️ scissors", "✂️ ножницы"},
    "qrcode_button": {"📷 qr kod oluştur", "📷 create qr code", "📷 создать qr-код"},
    "pdf_converter_main_button": {"📄 pdf dönüştürücü", "📄 pdf converter", "📄 конвертер pdf"},
    "text_to_pdf_button": {"📝 metinden pdf'e", "📝 text to pdf", "📝 текст в pdf"},
    "image_to_pdf_button": {"🖼️ resimden pdf'e", "🖼️ image to pdf", "🖼️ изображение в pdf"},
    "document_to_pdf_button": {"📄 belgeden pdf'e", "📄 document to pdf", "📄 документ в pdf"},
    "weather_main_button": {"☀️ hava durumu", "☀️ weather", "☀️ погода"}, 
    "developer_main_button": {"👨‍💻 geliştirici", "👨‍💻 developer", "👨‍💻 разработчик"}, 
    "add_reminder_button": {"➕ hatırlatıcı ekle", "➕ add reminder", "➕ добавить напоминание"},
    "show_reminders_button": {"📋 hatırlatıcıları göster", "📋 show reminders", "📋 показать напоминания"},
    "delete_reminder_button": {"🗑️ hatırlatıcı sil", "🗑️ delete reminder", "🗑️ удалить напоминание"},
}