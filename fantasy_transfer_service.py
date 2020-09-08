from dataclasses import dataclass
from typing import Optional

from fantasy_team_generator import FantasyTeam
from player import Player
from player_repository import PlayerRepository


@dataclass
class Transfer:
    remove: Player
    bring_in: Player

    @property
    def form_change(self) -> float:
        return self.bring_in.form - self.remove.form


class FantasyTransferService:

    @classmethod
    def suggest_transfer(cls, team: FantasyTeam) -> Optional[Transfer]:
        player_repository = PlayerRepository()
        best_transfer = None
        best_form_change = 0

        for player in player_repository.get_players():
            current_players = team.players_at(player.position)
            for current_player in current_players:
                if team.can_replace(current_player, player) and current_player.form < player.form:
                    if player.form - current_player.form > best_form_change:
                        best_transfer = Transfer(remove=current_player, bring_in=player)
                        best_form_change = player.form - current_player.form

        return best_transfer
