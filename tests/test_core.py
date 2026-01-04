"""
Comprehensive Unit Tests for ViraBot
Run with: python -m pytest tests/ -v
"""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock


# =============================================================================
# UTILITY TESTS
# =============================================================================

class TestTurkishLower:
    """Test Turkish lowercase conversion"""
    
    def test_turkish_i_conversion(self):
        from texts.common import turkish_lower
        assert turkish_lower("İSTANBUL") == "istanbul"
        assert turkish_lower("IŞIK") == "ışık"
    
    def test_normal_letters(self):
        from texts.common import turkish_lower
        assert turkish_lower("Test") == "test"
        assert turkish_lower("ABC") == "abc"
    
    def test_empty_string(self):
        from texts.common import turkish_lower
        assert turkish_lower("") == ""


class TestButtonMappings:
    """Test button mapping generator"""
    
    def test_generate_mappings(self):
        from texts.common import generate_mappings_from_buttons
        
        test_buttons = {
            "tr": [["Test Buton"]],
            "en": [["Test Button"]]
        }
        
        mappings = generate_mappings_from_buttons(test_buttons)
        assert "test buton" in mappings
        assert "test button" in mappings
    
    def test_empty_buttons(self):
        from texts.common import generate_mappings_from_buttons
        result = generate_mappings_from_buttons({})
        assert isinstance(result, set)


class TestIsBackButton:
    """Test back button detection"""
    
    def test_turkish_back(self):
        from utils import is_back_button
        assert is_back_button("geri") == True
        assert is_back_button("iptal") == True
    
    def test_english_back(self):
        from utils import is_back_button
        assert is_back_button("back") == True
        assert is_back_button("cancel") == True
    
    def test_russian_back(self):
        from utils import is_back_button
        assert is_back_button("назад") == True
        assert is_back_button("отмена") == True
    
    def test_emoji_back_buttons(self):
        from utils import is_back_button
        assert is_back_button("🔙 Ana Menü") == True
        assert is_back_button("🔙 Main Menu") == True
    
    def test_non_back_text(self):
        from utils import is_back_button
        assert is_back_button("hello") == False
        assert is_back_button("merhaba") == False
    
    def test_edge_cases(self):
        from utils import is_back_button
        assert is_back_button("") == False
        assert is_back_button(None) == False


# =============================================================================
# STATE TESTS
# =============================================================================

class TestStateConstants:
    """Test state module constants"""
    
    def test_all_states_defined(self):
        import state
        
        required_states = [
            'PLAYING_XOX', 'METRO_BROWSING', 'AI_CHAT_ACTIVE',
            'WAITING_FOR_QR_DATA', 'WAITING_FOR_NEW_NOTE_INPUT',
            'WAITING_FOR_WEATHER_CITY', 'WAITING_FOR_VIDEO_LINK',
            'WAITING_FOR_PDF_CONVERSION_INPUT', 'ADMIN_MENU_ACTIVE'
        ]
        
        for state_name in required_states:
            assert hasattr(state, state_name), f"Missing state: {state_name}"
    
    def test_states_are_strings(self):
        import state
        assert isinstance(state.PLAYING_XOX, str)
        assert isinstance(state.AI_CHAT_ACTIVE, str)


# =============================================================================
# CONFIG TESTS
# =============================================================================

class TestConfig:
    """Test configuration values"""
    
    def test_font_path_format(self):
        from config import FONT_PATH, BASE_DIR
        assert FONT_PATH.endswith(".ttf")
        assert BASE_DIR in FONT_PATH
    
    def test_notes_per_page(self):
        from config import NOTES_PER_PAGE
        assert isinstance(NOTES_PER_PAGE, int)
        assert 1 <= NOTES_PER_PAGE <= 20
    
    def test_bot_name_defined(self):
        from config import BOT_NAME
        assert isinstance(BOT_NAME, str)
        assert len(BOT_NAME) > 0
    
    def test_timezone_defined(self):
        from config import TIMEZONE
        assert isinstance(TIMEZONE, str)


# =============================================================================
# RATE LIMITER TESTS
# =============================================================================

class TestRateLimiter:
    """Test rate limiter functions"""
    
    def test_rate_limits_categories(self):
        from rate_limiter import RATE_LIMITS
        assert "general" in RATE_LIMITS
        assert "games" in RATE_LIMITS
        assert "heavy" in RATE_LIMITS
    
    def test_rate_limit_values(self):
        from rate_limiter import RATE_LIMITS
        for category, limit in RATE_LIMITS.items():
            assert isinstance(limit, int)
            assert limit > 0
    
    def test_window_seconds(self):
        from rate_limiter import WINDOW_SECONDS
        assert WINDOW_SECONDS == 60


# =============================================================================
# TEXTS TESTS
# =============================================================================

class TestTexts:
    """Test text definitions"""
    
    def test_all_languages_present(self):
        from texts import TEXTS
        
        sample_keys = ["start", "menu_prompt", "unknown_command"]
        for key in sample_keys:
            if key in TEXTS:
                assert "tr" in TEXTS[key], f"Missing TR for {key}"
                assert "en" in TEXTS[key], f"Missing EN for {key}"
                assert "ru" in TEXTS[key], f"Missing RU for {key}"
    
    def test_button_mappings_populated(self):
        from texts import BUTTON_MAPPINGS
        assert "menu" in BUTTON_MAPPINGS
        assert "back_to_tools" in BUTTON_MAPPINGS
        assert len(BUTTON_MAPPINGS) > 10


# =============================================================================
# GAME LOGIC TESTS
# =============================================================================

class TestXOXGame:
    """Test XOX (Tic Tac Toe) game logic"""
    
    def test_check_winner_horizontal(self):
        from handlers.games import check_winner
        
        board_x_wins = ["X", "X", "X", " ", " ", " ", " ", " ", " "]
        assert check_winner(board_x_wins) == "X"
    
    def test_check_winner_vertical(self):
        from handlers.games import check_winner
        
        board_o_wins = ["O", " ", " ", "O", " ", " ", "O", " ", " "]
        assert check_winner(board_o_wins) == "O"
    
    def test_check_winner_diagonal(self):
        from handlers.games import check_winner
        
        board_diag = ["X", " ", " ", " ", "X", " ", " ", " ", "X"]
        assert check_winner(board_diag) == "X"
    
    def test_no_winner(self):
        from handlers.games import check_winner
        
        board_ongoing = ["X", "O", " ", " ", "X", " ", " ", " ", " "]
        assert check_winner(board_ongoing) is None
    
    def test_bot_move_easy_returns_valid(self):
        from handlers.games import bot_move_easy
        
        board = ["X", " ", " ", " ", " ", " ", " ", " ", " "]
        move = bot_move_easy(board)
        assert move is not None
        assert board[move] == " "
    
    def test_bot_move_hard_blocks_win(self):
        from handlers.games import bot_move_hard
        
        # X is about to win, bot should block
        board = ["X", "X", " ", " ", "O", " ", " ", " ", " "]
        move = bot_move_hard(board)
        assert move == 2  # Block position


class TestMinimax:
    """Test minimax algorithm"""
    
    def test_minimax_winning_move(self):
        from handlers.games import minimax
        
        # O can win immediately
        board = ["X", "X", " ", "O", "O", " ", " ", " ", " "]
        score = minimax(board, True)  # O's turn
        assert score > 0  # O should win


# =============================================================================
# WEATHER CACHE TESTS
# =============================================================================

class TestWeatherCache:
    """Test weather caching functionality"""
    
    def test_cache_exists(self):
        from handlers.weather import _weather_cache, WEATHER_CACHE_TTL
        assert isinstance(_weather_cache, dict)
        assert WEATHER_CACHE_TTL.total_seconds() == 600  # 10 minutes


# =============================================================================
# DATABASE LANGUAGE CACHE TESTS
# =============================================================================

class TestLanguageCache:
    """Test language caching functionality"""
    
    def test_cache_exists(self):
        import database as db
        assert hasattr(db, '_user_lang_cache')
        assert isinstance(db._user_lang_cache, dict)


# =============================================================================
# ERROR MESSAGE CONSISTENCY TESTS
# =============================================================================

class TestErrorMessages:
    """Test error message consistency across languages"""
    
    def test_error_messages_exist(self):
        from texts import TEXTS
        
        error_keys = [
            "error_occurred", "unknown_command", 
            "weather_api_error", "video_download_error"
        ]
        
        for key in error_keys:
            if key in TEXTS:
                assert len(TEXTS[key]) >= 3, f"{key} missing languages"


# =============================================================================
# AI CHAT TESTS
# =============================================================================

class TestAIChat:
    """Test AI chat functionality"""
    
    def test_daily_limit_constant(self):
        from handlers.ai_chat import DAILY_LIMIT
        assert isinstance(DAILY_LIMIT, int)
        assert DAILY_LIMIT > 0
    
    def test_admin_unlimited_check(self):
        from handlers.ai_chat import ADMIN_DAILY_LIMIT
        assert ADMIN_DAILY_LIMIT >= 999


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

