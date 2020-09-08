import copy
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from random import shuffle
from typing import Set, Tuple, Dict, Optional, List

from consts import BUDGET
from player import Player, Position
from player_repository import PlayerRepository

NUM_PLAYERS_BY_POSITION = {
    Position.GKP: 2,
    Position.DEF: 5,
    Position.MID: 5,
    Position.FWD: 3
}

PLAYERS_FIELDED_BY_POSITION = {
    Position.GKP: 1,
    Position.DEF: 4,
    Position.MID: 4,
    Position.FWD: 2
}


@dataclass
class FantasyTeam:
    players: Set[Player] = field(default_factory=set)

    @property
    def score(self):
        return sum([100 * p.total_points__per_90 for p in self.players]) - sum([p.value for p in self.bench()])

    def players_at(self, position: Position) -> Set[Player]:
        return {player for player in self.players if player.position == position}

    def can_replace(self, current_player: Player, new_player: Player) -> bool:
        self.players.remove(current_player)
        self.players.add(new_player)
        can_replace = self.is_valid
        self.players.add(current_player)
        self.players.remove(new_player)
        return can_replace

    @property
    def goalkeepers(self) -> Set[Player]:
        return {player for player in self.players if player.position == Position.GKP}

    @property
    def defenders(self) -> Set[Player]:
        return {player for player in self.players if player.position == Position.DEF}

    @property
    def midfielders(self) -> Set[Player]:
        return {player for player in self.players if player.position == Position.MID}

    @property
    def forwards(self):
        return {player for player in self.players if player.position == Position.FWD}

    def starting_xi(self) -> Set[Player]:
        starting_xi: Set[Player] = set()

        for player in sorted(list(self.players),
                             key=lambda p: p.total_points__per_90,
                             reverse=True):
            if len([p for p in starting_xi if p.position == player.position]) < PLAYERS_FIELDED_BY_POSITION[player.position]:
                starting_xi.add(player)

        return starting_xi

    def bench(self) -> List[Player]:
        return sorted([player for player in self.players if player not in self.starting_xi()],
                      key=lambda p: p.total_points__per_90, reverse=True)

    @property
    def value(self) -> int:
        return sum([p.value for p in self.players])

    @property
    def is_valid(self) -> bool:
        for position in Position:
            expected = NUM_PLAYERS_BY_POSITION[position.value]
            actual = len(self.players_at(position))
            if not actual == expected:
                return False

        if not self.value <= BUDGET:
            return False

        c = Counter([p.club for p in self.players])
        club, num_of_players_from_club = c.most_common(1)[0]
        if not num_of_players_from_club <= 3:
            return False

        return True


    def __str__(self):
        starting = self.starting_xi()
        return f"{', '.join([str(p) for p in filter(lambda p: p.position == Position.GKP, starting)])}\n" \
               f"{', '.join([str(p) for p in filter(lambda p: p.position == Position.DEF, starting)])}\n" \
               f"{', '.join([str(p) for p in filter(lambda p: p.position == Position.MID, starting)])}\n" \
               f"{', '.join([str(p) for p in filter(lambda p: p.position == Position.FWD, starting)])}\n\n" \
               f"{', '.join([str(p) for p in self.bench()])}\n"


class FantasyTeamGenerator:

    def __init__(self):
        self.running_team = FantasyTeam()
        self.running_score = 0

    def generate(self) -> Tuple[FantasyTeam, int]:
        """
        Generate a team for the Fantasy Premier League competition.
        """
        player_repository = PlayerRepository()
        nyland_and_ryan = player_repository.get_nyland_and_ryan()
        self.running_team.players |= nyland_and_ryan
        best_team = FantasyTeam()
        for i in range(0, 2000):
            if i > 0:
                current_players = [p for p in self.running_team.players if p not in nyland_and_ryan]

                shuffle(current_players)

                current_players = set(current_players[3:])  # Remove three players at random to get out of local opt

                self.running_team.players = current_players | nyland_and_ryan
            for player in player_repository.get_players():
                if player.position == Position.GKP:
                    continue
                if self.can_add(player=player):
                    self.running_team.players.add(player)
                else:
                    replaced_player = self.find_replacement(player, self.running_team.players_at(player.position))
                    if replaced_player:
                        self.running_team.players.remove(replaced_player)
                        if self.can_add(player=player):
                            self.running_team.players.add(player)
                        else:
                            self.running_team.players.add(replaced_player)

            try:
                self._validate(self.running_team)
                print(f"Iteration {i}: Found team with score {self.running_team.score}")
                print(f"{self.running_team.score} cmp {best_team.score}")
                if self.running_team.score > best_team.score:
                    best_team = copy.deepcopy(self.running_team)
            except AssertionError as ae:
                print(f"Team failed: {ae}")

        return best_team, best_team.score

    def can_add(self, player: Player) -> bool:
        """
        Before adding a player, we must ensure that he can actually be added to the team
        """

        can_add = not self._position_already_filled(player.position)

        if self.running_club_count(club=player.club) >= 3:
            return False

        if self.running_team.value + player.value >= BUDGET:
            return False

        return can_add

    def running_club_count(self, club: str) -> int:
        """
        As we only allow three players from each club, we need to keep track of how many players we have from each club
        """
        count_by_club: Dict[str, int] = defaultdict(int)
        for player in self.running_team.players:
            count_by_club[player.club] += 1
        return count_by_club[club]

    @property
    def total_points_per_90(self) -> int:
        """
        Total points per 90 minutes based on the previous season for the team
        """
        return sum([player.total_points__per_90 for player in self.running_team.players])

    def find_replacement(self, new_player: Player, others: Set[Player]) -> Optional[Player]:
        """
        If we have filled our slots for midfielders, we might want to replace one of the midfielders with the new player
        if it's a better player.
        """
        remove_player: Optional[Player] = None
        for current_player in others:
            if new_player.is_better_than(current_player):
                remove_player = current_player

        return remove_player

    def _position_already_filled(self, position: Position) -> bool:
        """
        We are only allowed to have X number of players of a certain position
        """
        position_count = len(self.running_team.players_at(position=position))
        return position_count >= NUM_PLAYERS_BY_POSITION[position]

    @staticmethod
    def _validate(team: FantasyTeam):
        """
        We need to ensure that our team follows the rules of FPL
        """
        for position in Position:
            expected = NUM_PLAYERS_BY_POSITION[position.value]
            actual = len(team.players_at(position))
            assert actual == expected, f"Expected {expected} players at {position.name}, found {actual} "

        assert team.value <= BUDGET, f"Value {team.value} over budget {BUDGET}"

        c = Counter([p.club for p in team.players])
        club, num_of_players_from_club = c.most_common(1)[0]
        assert num_of_players_from_club <= 3, f"Too many players {num_of_players_from_club} from {club}"

