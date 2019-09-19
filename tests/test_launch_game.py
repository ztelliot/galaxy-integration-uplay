import asyncio
import unittest.mock as mock

from tests.conftest import NewGame


def test_launch_game_space_id(create_authenticated_plugin):
    loop = asyncio.get_event_loop()
    pg = create_authenticated_plugin()

    new_game = NewGame()
    new_game.status = "Installed"

    pg.user_can_perform_actions.return_value = True

    pg.games_collection.get_local_games.return_value = [new_game]

    pg.open_uplay_client = mock.create_autospec(pg.open_uplay_client)

    with mock.patch("plugin.subprocess.Popen") as pop:
        loop.run_until_complete(pg.launch_game("123"))
        pop.assert_called_with(f"start uplay://launch/{new_game.launch_id}", shell=True)

    pg.open_uplay_client.assert_not_called()


def test_launch_game_launch_id(create_authenticated_plugin):
    loop = asyncio.get_event_loop()
    pg = create_authenticated_plugin()

    new_game = NewGame()
    new_game.status = "Installed"

    pg.user_can_perform_actions.return_value = True

    pg.games_collection.get_local_games.return_value = [new_game]

    pg.open_uplay_client = mock.create_autospec(pg.open_uplay_client)

    with mock.patch("plugin.subprocess.Popen") as pop:
        loop.run_until_complete(pg.launch_game("321"))
        pop.assert_called_with(f"start uplay://launch/{new_game.launch_id}", shell=True)

    pg.open_uplay_client.assert_not_called()


def test_launch_game_not_installed(create_authenticated_plugin):
    loop = asyncio.get_event_loop()
    pg = create_authenticated_plugin()

    new_game = NewGame()

    pg.user_can_perform_actions.return_value = True

    pg.games_collection.get_local_games.return_value = [new_game]

    pg.open_uplay_client = mock.create_autospec(pg.open_uplay_client)

    with mock.patch("plugin.subprocess.Popen") as pop:
        loop.run_until_complete(pg.launch_game("321"))
        pop.assert_not_called()

    pg.open_uplay_client.assert_called()


