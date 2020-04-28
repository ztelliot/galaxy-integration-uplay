import os
from definitions import System, SYSTEM
from galaxy.api.types import Cookie
UBISOFT_REGISTRY = "SOFTWARE\\Ubisoft"
STEAM_REGISTRY = "Software\\Valve\\Steam"
UBISOFT_REGISTRY_LAUNCHER = "SOFTWARE\\Ubisoft\\Launcher"
UBISOFT_REGISTRY_LAUNCHER_INSTALLS = "SOFTWARE\\Ubisoft\\Launcher\\Installs"

if SYSTEM == System.WINDOWS:
    UBISOFT_SETTINGS_YAML = os.path.join(os.getenv('LOCALAPPDATA'), 'Ubisoft Game Launcher', 'settings.yml')

UBISOFT_CONFIGURATIONS_BLACKLISTED_NAMES = ["gamename", "l1", '', 'ubisoft game', 'name']

CHROME_USERAGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36"
CLUB_APPID = "b8fde481-327d-4031-85ce-7c10a202a700"
CLUB_GENOME_ID = "fbd6791c-a6c6-4206-a75e-77234080b87b"

AUTH_PARAMS = {
    "window_title": "Login to Uplay",
    "window_width": 400,
    "window_height": 680,
    "start_uri": f"https://connect.ubi.com/Default/Login?appId={CLUB_APPID}&genomeId={CLUB_GENOME_ID}&nextUrl=https%3A%2F%2Fclub.ubisoft.com",
    "end_uri_regex": r"^https://club\.ubisoft\.com/.*"
}

# Adding these cookies disables the cookie disclaimer which blocked major part of the view.
COOKIES = [Cookie("thirdPartyOk", "ok", ".ubi.com"),
           Cookie("TC_OPTOUT", "0@@@005@@@ALL", ".ubi.com"),
           Cookie("TC_OPTOUT_categories", "18%2C19", ".ubi.com")]
