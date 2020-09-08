import json
from typing import Dict, Optional, Set, Generator

import requests

from consts import FANTASY_URL, PLAYER_URL, MINIMUM_MINUTES
from player import Player, Position


class PlayerRepository:

    def __init__(self, fetch_from_fpl: bool = False):
        self.players_by_id: Dict[int, Player] = {}

        if fetch_from_fpl:
            contents = requests.get(FANTASY_URL).json()
        else:
            with open('resources/fpl_database.json', 'r') as fpl_database:
                contents = json.loads(fpl_database.read())

        clubs_by_code = {
            club['code']: club['name']
            for club in contents['teams']
        }

        for player_json in contents['elements']:
            if float(player_json['selected_by_percent']) <= 2:
                continue

            player = Player(
                id=int(player_json['id']),
                name=player_json['web_name'],
                value=int(player_json['now_cost']),
                position=Position(value=player_json['element_type']),
                club=clubs_by_code[player_json['team_code']],
                selected_by_percent=float(player_json['selected_by_percent']),
                form=float(player_json['form'])
            )

            file_name = f"resources/players/{player.id}.json"

            try:
                f = open(file_name, 'r')
                player_result = json.loads(f.read())
                f.close()
            except IOError:
                player_result = requests.get(PLAYER_URL.format(player_id=player.id)).json()
                with open(file_name, 'w') as player_file:
                    player_file.write(str(player_result).replace("\'", "\"").replace("None", "\"None\"").replace("False", "\"False\"").replace("True", "\"True\""))

            try:
                previous_season = player_result['history_past'][-1]

                # General
                player.minutes_played = int(previous_season['minutes'])
                player.total_points = int(previous_season['total_points'])
                player.bonus_points = int(previous_season['bps'])
                player.yellow_cards = int(previous_season['yellow_cards'])
                player.red_cards = int(previous_season['red_cards'])
                player.penalties_missed = int(previous_season['penalties_missed'])

                # Offensive
                player.goals_scored = int(previous_season['goals_scored'])
                player.assists = int(previous_season['assists'])

                # Defensive
                player.clean_sheets = int(previous_season['clean_sheets'])
                player.goals_conceded = int(previous_season['goals_conceded'])
            except IndexError:
                print(f"Found no stats for {player.name}")

            if player.minutes_played >= MINIMUM_MINUTES or player.position == Position.GKP:
                self.players_by_id[player.id] = player

    def get_players(self) -> Set[Player]:
        return set(self.players_by_id.values())

    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        return self.players_by_id.get(player_id, None)

    def get_nyland_and_ryan(self) -> Set[Player]:
        return {player for player in self.get_players() if player.name in ("Ryan", "Nyland")}
