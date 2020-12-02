
class Data:
    SHORT_TIME = 5
    MEDIUM_TIME = 15
    LONG_TIME = 30


class FacebookData:
    BASE_URL = "https://www.facebook.com"
    LOGIN_PAGE = f"{BASE_URL}/login.php"
    RE_AUTH_PAGE = f"{BASE_URL}/login/reauth.php"
    APPLICATIONS_PAGE = f"{BASE_URL}/settings?tab=applications"


class User:
    def __init__(self, name, username, password, markers, cookies):
        self.name = name
        self.username = username
        self.password = password
        self.markers = markers
        self.cookies = cookies


Attacker = User(
    "attacker",
    "attacker@anonymous.com",
    "password",
    ["1", "2", "3"],
    "facebook_cookies"
)

Victim = User(
    "victim",
    "victim@anonymous.com",
    "password",
    ["1", "2", "3"],
    "facebook_victim_cookies"
)
