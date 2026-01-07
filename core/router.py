import logging
import asyncio
from typing import Callable, Dict, Any, Awaitable, List, Tuple, Set

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
import state
from utils import cleanup_context

logger = logging.getLogger(__name__)

# --- STATE ROUTER SECTION ---

# Type alias for handler functions
StateHandler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[Any]]

class StateRouter:
    def __init__(self):
        self._handlers: Dict[str, StateHandler] = {}
        
    def register(self, state_name: str, handler: StateHandler):
        """Registers a handler for a specific state name."""
        self._handlers[state_name] = handler
        logger.debug(f"Registered handler for state: {state_name}")
        
    async def dispatch(self, state_name: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Dispatches the update to the handler registered for the given state.
        Returns True if a handler was found and executed, False otherwise.
        """
        handler = self._handlers.get(state_name)
        if handler:
            try:
                await handler(update, context)
                return True
            except Exception as e:
                # Use global error handler logic or log it here.
                # Ideally, we allow exception to bubble up to the global handler, 
                # but legacy code swallowed things. We log it nicely.
                logger.error(f"Error handling state '{state_name}': {e}", exc_info=True)
                return False
        return False

# Global StateRouter instance
router = StateRouter()


# --- BUTTON ROUTER REGISTRY ---

# Key -> Handler Function
button_handlers: Dict[str, Callable] = {}

# Key -> (Platform/Arg, Handler Function)
video_platform_handlers: Dict[str, Tuple[str, Callable]] = {}
format_handlers: Dict[str, Tuple[str, Callable]] = {}

LANGUAGE_BUTTONS = {"🇹🇷 türkçe", "🇬🇧 english", "🇷🇺 русский"}

def register_button(mapping_key: str, handler: Callable):
    """Registers a handler for a specific button mapping key."""
    button_handlers[mapping_key] = handler

def register_video_platform(mapping_key: str, platform: str, handler: Callable):
    """Registers a handler for a video platform button."""
    video_platform_handlers[mapping_key] = (platform, handler)

def register_format(mapping_key: str, format_type: str, handler: Callable):
    """Registers a handler for a format selection button."""
    format_handlers[mapping_key] = (format_type, handler)

