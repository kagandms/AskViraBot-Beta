# texts/__init__.py
# Bu dosya geriye dönük uyumluluk için texts modülünden tüm sembolleri export eder

from .common import (
    SOCIAL_MEDIA_LINKS,
    CITY_NAMES_TRANSLATED,
    turkish_lower,
    generate_mappings_from_buttons,
)

from .strings import (
    TEXTS,
    MAIN_BUTTONS,
    TOOLS_BUTTONS,
    VIDEO_DOWNLOADER_BUTTONS,
    FORMAT_SELECTION_BUTTONS,
    GAMES_BUTTONS,
    NOTES_BUTTONS,
    DELETE_NOTES_BUTTONS,
    TKM_BUTTONS,
    PDF_CONVERTER_BUTTONS,
    INPUT_BACK_BUTTONS,
    REMINDER_BUTTONS,
    AUTO_MAPPINGS,
    MANUAL_MAPPINGS,
    BUTTON_MAPPINGS,
)

# texts.py'deki tüm sembolleri buradan import edebilirsiniz
# Örnek: from texts import TEXTS, BUTTON_MAPPINGS

__all__ = [
    'TEXTS',
    'SOCIAL_MEDIA_LINKS', 
    'CITY_NAMES_TRANSLATED',
    'MAIN_BUTTONS',
    'TOOLS_BUTTONS',
    'VIDEO_DOWNLOADER_BUTTONS',
    'FORMAT_SELECTION_BUTTONS',
    'GAMES_BUTTONS',
    'NOTES_BUTTONS',
    'DELETE_NOTES_BUTTONS',
    'TKM_BUTTONS',
    'PDF_CONVERTER_BUTTONS',
    'INPUT_BACK_BUTTONS',
    'REMINDER_BUTTONS',
    'turkish_lower',
    'generate_mappings_from_buttons',
    'AUTO_MAPPINGS',
    'MANUAL_MAPPINGS',
    'BUTTON_MAPPINGS',
]
