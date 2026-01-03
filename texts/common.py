# texts/common.py
# Dil bağımsız veriler ve yardımcı fonksiyonlar

# Sosyal Medya Linkleri
SOCIAL_MEDIA_LINKS = {
    "website": "https://kagansametdurmus.com.tr", 
    "instagram": "https://www.instagram.com/kagandms/",
    "telegram": "https://t.me/kagandms",
    "linkedin": "https://www.linkedin.com/in/kağan-samet-durmuş-37676332b/"
}

# Şehir adları çevirileri
CITY_NAMES_TRANSLATED = {
    "tr": {"Istanbul": "🇹🇷 İstanbul", "Moscow": "🇷🇺 Moskova", "London": "🇬🇧 Londra", "New York": "🇺🇸 New York", "Beijing": "🇨🇳 Pekin", "Ankara": "🇹🇷 Ankara", "Saint Petersburg": "🇷🇺 St. Petersburg", "Paris": "🇫🇷 Paris", "Berlin": "🇩🇪 Berlin"}, 
    "en": {"Istanbul": "🇹🇷 Istanbul", "Moscow": "🇷🇺 Moscow", "London": "🇬🇧 London", "New York": "🇺🇸 New York", "Beijing": "🇨🇳 Beijing", "Ankara": "🇹🇷 Ankara", "Saint Petersburg": "🇷🇺 St. Petersburg", "Paris": "🇫🇷 Paris", "Berlin": "🇩🇪 Berlin"}, 
    "ru": {"Istanbul": "🇹🇷 Стамбул", "Moscow": "🇷🇺 Москва", "London": "🇬🇧 Лондон", "New York": "🇺🇸 Нью-Йорк", "Beijing": "🇨🇳 Пекин", "Ankara": "🇹🇷 Анкара", "Saint Petersburg": "🇷🇺 Санкт-Петербург", "Paris": "🇫🇷 Париж", "Berlin": "🇩🇪 Берлин"} 
}


# --- TÜRKÇE LOWERCASE HELPER ---
def turkish_lower(text: str) -> str:
    """Türkçe karakterleri doğru şekilde lowercase yapar"""
    return text.replace("İ", "i").replace("I", "ı").lower()


# --- OTOMATİK BUTTON MAPPING ÜRETİCİ ---
def generate_mappings_from_buttons(*button_dicts):
    """
    Verilen buton sözlüklerinden otomatik lowercase mapping üretir.
    Tüm dillerdeki buton metinlerini toplar ve lowercase versiyonlarını döndürür.
    """
    all_buttons = set()
    for btn_dict in button_dicts:
        for lang, rows in btn_dict.items():
            for row in rows:
                for button_text in row:
                    all_buttons.add(turkish_lower(button_text))
    return all_buttons
