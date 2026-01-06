
import logging
from typing import Callable, Dict, Any, Awaitable
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

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
                logger.error(f"Error handling state '{state_name}': {e}", exc_info=True)
                return False
        return False

# Global instance
router = StateRouter()
