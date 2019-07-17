import logging as log
from definitions import GameStatus


class GamesCollection(list):

    def get_local_games(self):
        local_games = []
        for game in self:
            if game.status in [GameStatus.Installed, GameStatus.Running]:
                local_games.append(game)
        return local_games

    def append(self, _):
        AssertionError('Method not available. Use extend')

    def extend(self, games):
        spaces = set([game.space_id for game in self if game.space_id])
        installs = set([game.install_id for game in self if game.install_id])

        for game in games:
            if game.space_id not in spaces and game.install_id not in installs:
                log.info(f"Adding new game to games collection {game.name} with space_id: {game.space_id} and install_id/launch_id: {game.install_id}/{game.launch_id}")
                super().append(game)
                continue
            if game.space_id in spaces or game.install_id in installs:
                for game_in_list in self:
                    if game.space_id == game_in_list.space_id or game.install_id == game_in_list.install_id:
                        if game.install_id and not game_in_list.install_id:
                            log.debug(f"Extending existing game entry {game_in_list} with launch id: {game.install_id}")
                            game_in_list.install_id = game.install_id
                            game_in_list.launch_id = game.launch_id
                        if game.space_id and not game_in_list.space_id:
                            log.debug(f"Extending existing game entry {game_in_list} with space id: {game.space_id}")
                            game_in_list.space_id = game.space_id
                        if game.status is not GameStatus.Unknown and game_in_list.status is GameStatus.Unknown:
                            game_in_list.status = game.status
                        if game.owned:
                            game_in_list.owned = game.owned



    def __getitem__(self, key):
        if type(key) == int:
            return super().__getitem__(key)
        elif type(key) == str:
            for i in self:
                if key in (i.launch_id, i.space_id):
                    return i
            raise KeyError(f'No game with id: {key}')
        else:
            raise TypeError(f'Excpected str or int, got {type(key)}')
