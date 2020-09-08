from dataclasses import dataclass, field
from enum import Enum


class Position(int, Enum):
    GKP = 1
    DEF = 2
    MID = 3
    FWD = 4


@dataclass
class Player:
    id: int
    name: str
    position: Position
    value: int
    club: str
    selected_by_percent: float
    form: float

    minutes_played: int = field(default=0)
    goals_scored: int = field(default=0)
    goals_conceded: int = field(default=0)
    assists: int = field(default=0)
    clean_sheets: int = field(default=0)
    total_points: int = field(default=0)
    bonus_points: int = field(default=0)
    yellow_cards: int = field(default=0)
    red_cards: int = field(default=0)
    penalties_missed: int = field(default=0)

    def is_better_than(self, other_player: 'Player') -> bool:
        return self.rating >= other_player.rating

    @property
    def goals_scored__per_90(self) -> float:
        if self.minutes_played == 0:
            return 0
        return (float(self.goals_scored) / float(self.minutes_played)) * 90

    @property
    def goals_conceded__per_90(self) -> float:
        if self.minutes_played == 0:
            return 0
        return (float(self.goals_conceded) / float(self.minutes_played)) * 90

    @property
    def total_points__per_90(self) -> float:
        if self.minutes_played == 0:
            return 0
        return (float(self.total_points) / float(self.minutes_played)) * 90

    @property
    def rating(self) -> float:
        return self.total_points__per_90

    def __hash__(self):
        return self.id

    def __str__(self):
        return f"{self.name} ({self.position.name}/{self.club}@{self.total_points__per_90:.2f}PPG)"
