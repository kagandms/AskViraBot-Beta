
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple, Any

@dataclass
class GameState:
    message_id: Optional[int] = None
    bet_amount: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

@dataclass
class TKMState(GameState):
    game: str = "tkm"

@dataclass
class SlotState(GameState):
    game: str = "slot"

@dataclass
class BlackjackState(GameState):
    deck: List[Tuple[str, str]] = field(default_factory=list)
    player_hand: List[Tuple[str, str]] = field(default_factory=list)
    dealer_hand: List[Tuple[str, str]] = field(default_factory=list)
    game: str = "blackjack"
    
    def to_dict(self) -> dict:
        # Tuples might need serialization if JSON doesn't support them well (it converts to list)
        # But standard asdict handles this by converting validation... 
        # Actually standard python json.dump converts tuples to lists.
        # So when we read back, they are lists.
        # We need to ensure we treat them as lists or convert back to tuples.
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        # Filter keys
        valid_data = {k: v for k, v in data.items() if k in cls.__annotations__ or k in GameState.__annotations__}
        
        # Convert hands from lists to tuples if necessary (though tuples are immutable)
        # JSON loads as lists. Python List[Tuple] type hint ensures static analysis but runtime it's list.
        # We can explicitly convert if needed, but for now list is fine as long as code handles it.
        # Our blackjack code accesses elements via index, so lists are fine.
        return cls(**valid_data)
