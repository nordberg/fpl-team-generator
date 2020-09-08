from fantasy_team_generator import FantasyTeamGenerator
from fantasy_transfer_service import FantasyTransferService
from player_repository import PlayerRepository

if __name__ == '__main__':
    repository = PlayerRepository()
    team, score = FantasyTeamGenerator().generate()

    if team is not None:
        print(f"Found team worth {team.value} with points per 90: {score}")
        print()
        print(team)
    else:
        print("Failed to find a team given the constraints")

    transfer = FantasyTransferService.suggest_transfer(team=team)

    if transfer:
        print(transfer)