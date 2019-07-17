from datetime import datetime
import logging as log
from galaxy.http import HttpClient
import dateutil.parser

from galaxy.api.errors import (
    AuthenticationRequired, AccessDenied, UnknownError
)

from consts import CLUB_APPID, CHROME_USERAGENT


class BackendClient(HttpClient):
    def __init__(self, plugin):
        self._plugin = plugin
        self._auth_lost_callback = None
        self.token = None
        self.session_id = None
        self.refresh_token = None
        self.refresh_time = None
        self.user_id = None
        self.__refresh_in_progress = False
        super().__init__()
        self._session.headers = {
            'Authorization': None,
            'Ubi-AppId': CLUB_APPID,
            "User-Agent": CHROME_USERAGENT,
            'Ubi-SessionId': None
        }

    def set_auth_lost_callback(self, callback):
        self._auth_lost_callback = callback

    def is_authenticated(self):
        return self.token is not None

    async def _do_request(self, method, *args, **kwargs):
        if not kwargs or 'headers' not in kwargs:
            log.info("No headers in kwargs, using session headers")
            kwargs['headers'] = self._session.headers
        if 'add_to_headers' in kwargs:
            for header in kwargs['add_to_headers']:
                kwargs['headers'][header] = kwargs['add_to_headers'][header]
            kwargs.pop('add_to_headers')

        r = await super().request(method, *args, **kwargs)
        j = await r.json()  # all ubi endpoints return jsons
        log.info(f"Response status: {r}")
        return j

    async def _do_request_safe(self, method, *args, **kwargs):

        async def _refresh_and_request():
            await self._refresh_ticket()
            return await self._do_request(method, *args, **kwargs)

        if self.__refresh_in_progress:
            log.info(f'Refreshing already in progress. Calling url without refresh')
            return await self._do_request(method, *args, **kwargs)

        self.__refresh_in_progress = True
        result = {}
        try:
            if not self.refresh_token:
                result = await _refresh_and_request()
            else:
                log.debug(f'rememberMeTicket expiration time: {str(self.refresh_time)}')
                refresh_needed = self.refresh_time is None or datetime.now() > datetime.fromtimestamp(int(self.refresh_time))
                if refresh_needed:
                    await self._refresh_remember_me()
                    result = await _refresh_and_request()
                else:
                    try:
                        result = await _refresh_and_request()
                    except (AccessDenied, AuthenticationRequired):
                        # fallback for another reason than expired time or wrong calculation due to changing time zones
                        log.debug('Fallback refresh')
                        await self._refresh_remember_me()
                        result = await _refresh_and_request()
        except (AccessDenied, AuthenticationRequired) as e:
            log.debug(f"Unable to refresh authentication calling auth lost: {repr(e)}")
            if self._auth_lost_callback:
                self._auth_lost_callback()
            raise
        except Exception as e:
            log.debug("Refresh workflow has failed:" + repr(e))
            raise
        else:
            self._plugin.store_credentials(self.get_credentials())
        finally:
            self.__refresh_in_progress = False

        return result

    async def _do_options_request(self):
        await self._do_request('options', "https://public-ubiservices.ubi.com/v3/profiles/sessions", headers={
            "Origin": "https://connect.ubisoft.com",
            "Referer": "https://connect.ubisoft.com/login?appId=314d4fef-e568-454a-ae06-43e3bece12a6",
            "User-Agent": CHROME_USERAGENT,
        })

    async def _refresh_remember_me(self):
        log.debug('Refreshing rememberMeTicket')
        await self._do_options_request()
        j = await self._do_request(
            'post',
            f'https://public-ubiservices.ubi.com/v3/profiles/sessions',
            headers={
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US;en;q=0.5',
                'Authorization': f"rm_v1 t={self.refresh_token}",
                'Content-Type': 'application/json',
                'Ubi-AppId': CLUB_APPID,
                'User-Agent': CHROME_USERAGENT,
                'Host': 'public-ubiservices.ubi.com',
                'Origin': 'https://connect.ubisoft.com',
                'Referer': 'https://connect.ubisoft.com',
            },
            json={"rememberMe": True}
        )
        self._handle_authorization_response(j)

    async def _refresh_ticket(self):
        log.debug('Refreshing ticket')
        await self._do_options_request()
        j = await self._do_request(
            'put',
            f'https://public-ubiservices.ubi.com/v3/profiles/sessions',
            headers={
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US;en;q=0.5',
                'Authorization': f"Ubi_v1 t={self.token}",
                'Content-Type': 'application/json',
                'Ubi-AppId': CLUB_APPID,
                'User-Agent': CHROME_USERAGENT,
                'Host': 'public-ubiservices.ubi.com',
                'Origin': 'https://connect.ubisoft.com',
                'Referer': 'https://connect.ubisoft.com',
            })
        self._handle_authorization_response(j)

    def _handle_authorization_response(self, j):
        refresh_time = datetime.now() + (dateutil.parser.parse(j['expiration']) - dateutil.parser.parse(j['serverTime']))
        j['refreshTime'] = round(refresh_time.timestamp())
        self.restore_credentials(j)

    def restore_credentials(self, data):
        self.token = data['ticket']
        self.session_id = data['sessionId']
        self.user_id = data['userId']
        self.refresh_time = data.get('refreshTime', '0')
        if data.get('rememberMeTicket'):
            self.refresh_token = data['rememberMeTicket']

        self._session.headers = {
            'Ubi-AppId': CLUB_APPID,
            "Authorization": f"Ubi_v1 t={self.token}",
            "Ubi-SessionId": self.session_id
        }
        self._plugin.store_credentials(self.get_credentials())

    def get_credentials(self):
        return {
            "ticket": self.token,
            "sessionId": self.session_id,
            "rememberMeTicket": self.refresh_token,
            "userId": self.user_id,
            "refreshTime": self.refresh_time
        }

    async def authorise_with_stored_credentials(self, credentials):
        self.restore_credentials(credentials)
        user_data = await self.get_user_data()
        await self.post_sessions()
        return user_data

    async def authorise_with_cookies(self, cookies):
        user_data = {}
        tasty_cookies = ['user_id', 'user_name', 'ticket', 'rememberMeTicket', 'sessionId']
        for cookie in cookies:
            if cookie['name'] in tasty_cookies:
                user_data[cookie['name']] = cookie['value']
        user_data['userId'] = user_data.pop('user_id')
        user_data['username'] = user_data.pop('user_name')

        self.restore_credentials(user_data)
        await self.post_sessions()
        return user_data

    async def get_user_data(self):
        return await self._do_request_safe('get', f"https://public-ubiservices.ubi.com/v3/users/{self.user_id}")

    async def get_friends(self):
        r = await self._do_request_safe('get', f'https://api-ubiservices.ubi.com/v2/profiles/me/friends')
        return r

    async def get_club_titles(self):
        return await self._do_request_safe('get', "https://public-ubiservices.ubi.com/v1/profiles/me/club/aggregation/website/games/owned")

    async def get_game_stats(self, space_id):
        url = f"https://public-ubiservices.ubi.com/v1/profiles/{self.user_id}/statscard?spaceId={space_id}"
        headers = {}
        headers['Ubi-RequestedPlatformType'] = "uplay"
        headers['Ubi-LocaleCode'] = "en-GB"

        try:
            j = await self._do_request('get', url, add_to_headers=headers)
        except UnknownError:  # 412: no stats available for this user
            return {}
        return j

    async def get_applications(self, spaces):
        space_string = ','.join(space['spaceId'] for space in spaces)
        j = await self._do_request_safe('get', f"https://api-ubiservices.ubi.com/v2/applications?spaceIds={space_string}")
        return j

    async def get_challenges(self, space_id):
        j = await self._do_request_safe('get', f"https://public-ubiservices.ubi.com/v1/profiles/{self.user_id}/club/actions?limit=100&locale=en-US&spaceId={space_id}")
        return j

    async def get_configuration(self):
        r = await self._do_request_safe('get', f'https://uplaywebcenter.ubi.com/v1/configuration')
        return r.json()

    async def post_sessions(self):
        headers = {}
        headers['Content-Type'] = 'application/json'
        j = await self._do_request_safe('post', f"https://public-ubiservices.ubi.com/v2/profiles/sessions", add_to_headers=headers)
        return j
