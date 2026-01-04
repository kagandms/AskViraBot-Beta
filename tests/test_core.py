"""
Basic Unit Tests for ViraBot
Run with: python -m pytest tests/ -v
"""

import pytest
from datetime import date

# Test database helper functions (mocked)
class TestDatabaseHelpers:
    """Test database utility functions"""
    
    def test_turkish_lower(self):
        """Test Turkish lowercase conversion"""
        from texts.common import turkish_lower
        
        assert turkish_lower("İSTANBUL") == "istanbul"
        assert turkish_lower("IŞIK") == "ışık"
        assert turkish_lower("Test") == "test"
        assert turkish_lower("ABC") == "abc"  # Normal letters
    
    def test_generate_mappings(self):
        """Test button mapping generator"""
        from texts.common import generate_mappings_from_buttons, turkish_lower
        
        test_buttons = {
            "tr": [["Test Buton"]],
            "en": [["Test Button"]]
        }
        
        mappings = generate_mappings_from_buttons(test_buttons)
        assert "test buton" in mappings
        assert "test button" in mappings


class TestStateConstants:
    """Test state module constants"""
    
    def test_state_constants_exist(self):
        """Verify all state constants are defined"""
        import state
        
        assert hasattr(state, 'PLAYING_XOX')
        assert hasattr(state, 'METRO_BROWSING')
        assert hasattr(state, 'AI_CHAT_ACTIVE')
        assert hasattr(state, 'WAITING_FOR_QR_DATA')


class TestConfigValues:
    """Test configuration values"""
    
    def test_font_path_format(self):
        """Test font path is properly formatted"""
        from config import FONT_PATH, BASE_DIR
        
        assert FONT_PATH.endswith(".ttf")
        assert BASE_DIR in FONT_PATH
    
    def test_notes_per_page(self):
        """Test pagination constant"""
        from config import NOTES_PER_PAGE
        
        assert isinstance(NOTES_PER_PAGE, int)
        assert NOTES_PER_PAGE > 0


class TestUtilsFunctions:
    """Test utility functions"""
    
    def test_is_back_button(self):
        """Test back button detection"""
        from utils import is_back_button
        
        # Should return True for back keywords
        assert is_back_button("geri") == True
        assert is_back_button("back") == True
        assert is_back_button("назад") == True
        assert is_back_button("🔙 Ana Menü") == True
        
        # Should return False for regular text
        assert is_back_button("hello") == False
        assert is_back_button("merhaba") == False
        assert is_back_button("") == False
        assert is_back_button(None) == False


class TestRateLimiter:
    """Test rate limiter functions"""
    
    def test_rate_limits_exist(self):
        """Verify rate limit categories exist"""
        from rate_limiter import RATE_LIMITS
        
        assert "general" in RATE_LIMITS
        assert "games" in RATE_LIMITS
        assert "heavy" in RATE_LIMITS
    
    def test_window_seconds(self):
        """Test rate limit window"""
        from rate_limiter import WINDOW_SECONDS
        
        assert WINDOW_SECONDS == 60  # 1 minute


class TestTexts:
    """Test text definitions"""
    
    def test_texts_have_all_languages(self):
        """Verify texts have tr, en, ru translations"""
        from texts import TEXTS
        
        # Sample a few keys
        for key in ["start", "menu_prompt", "unknown_command"]:
            if key in TEXTS:
                assert "tr" in TEXTS[key]
                assert "en" in TEXTS[key]
                assert "ru" in TEXTS[key]
    
    def test_button_mappings_exist(self):
        """Verify button mappings are populated"""
        from texts import BUTTON_MAPPINGS
        
        assert "menu" in BUTTON_MAPPINGS
        assert "back_to_tools" in BUTTON_MAPPINGS
        assert len(BUTTON_MAPPINGS) > 0


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
