import asyncio
import json
from unittest.mock import patch

import pytest
from galaxy.api.consts import LicenseType
from galaxy.api.types import Game, LicenseInfo


@pytest.fixture
def result_owned_club_games():
    data = json.loads('''{"jsonrpc": "2.0", "id": "3", "result": {"owned_games": [{"game_id": "6678eff0-1293-4f87-8c8c-06a4ca646068", "game_title": "Assassin's Creed\u00ae Unity", "dlcs": [], "license_info": {"license_type": "SinglePurchase"}}, {"game_id": "f40e304d-8e8d-4343-8270-d06487c35add", "game_title": "Far Cry\u00ae 5", "dlcs": [], "license_info": {"license_type": "SinglePurchase"}}, {"game_id": "6edd234a-abff-4e90-9aab-b9b9c6e49ff7", "game_title": "Tom Clancy's The Division\u2122 ", "dlcs": [], "license_info": {"license_type": "SinglePurchase"}}, {"game_id": "1d1273d9-2120-4e55-8d98-66e08781258e", "game_title": "Trackmania Turbo", "dlcs": [], "license_info": {"license_type": "SinglePurchase"}}, {"game_id": "50228b8c-bbaa-4c32-83c6-2831a1ac317c", "game_title": "Far Cry\u00ae 3", "dlcs": [], "license_info": {"license_type": "SinglePurchase"}}, {"game_id": "4bd0476b-acec-446d-b526-23a0209101ca", "game_title": "Far Cry\u00ae 3 Blood Dragon", "dlcs": [], "license_info": {"license_type": "SinglePurchase"}}]}}\n''')
    return [
        Game(
            game['game_id'],
            game['game_title'],
            [],
            LicenseInfo(LicenseType.SinglePurchase)
        ) for game in data['result']['owned_games']
    ]


def test_owned_games_club_only(create_authenticated_plugin, result_owned_club_games):
    loop = asyncio.get_event_loop()
    pg = create_authenticated_plugin()

    pg._game_ownership_is_glitched.return_value = False

    pg.user_can_perform_actions = True

    # do not try parse local games
    with patch('os.path.exists', lambda _: False):
        result = loop.run_until_complete(pg.get_owned_games())
    assert result == result_owned_club_games



