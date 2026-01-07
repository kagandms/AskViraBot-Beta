from dataclasses import dataclass, field, asdict, fields
from typing import List, Optional, Tuple, Any

@dataclass
class GameState:
    message_id: Optional[int] = None
    bet_amount: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        # Use fields(cls) to get ALL fields including inherited ones
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})

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
    
    # Inherit generic from_dict from GameState which now handles everything correctly
