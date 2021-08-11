from threading import Event
import crypt
from sys import stderr
from psutil import process_iter
from flask_login import UserMixin
import os.path


timers = list()
monitors = list()


def get_timer_monitor(l: list, username: str):
    for t_m in l:
        if t_m.user == username:
            return t_m
    return None


shutdown_event = Event()

Actions = {
    "Poweroff": "poweroff",
    "Reboot": "reboot",
    "Hibernate": "systemctl hibernate",  # TBA
    "Suspend": "systemctl suspend",   # TBA
    "Script": None
}

Monitor = {
    'Network': 'net',
    'CPU': 'cpu',
    'RAM': 'ram',
    'Sound': 'audio',
    'Process': 'proc',
    'Display': 'disp'
}

# https://stackoverflow.com/questions/28195805/running-notify-send-as-root


def eprint(*args, **kwargs):
    print(*args, file=stderr, **kwargs)


def list_processes() -> list:
    processes = list()
    for proc in process_iter():
        processes.append({'name': proc.name(), 'pid': proc.pid})
    return processes


def list_users() -> list:
    lines = list()
    users = list()
    with open('/etc/shadow', 'rt') as f:
        lines = f.readlines()
    for line in lines:
        username = line.split(':')[0]
        users.append(User(username))
    return users


def check_permissions(username, level):
    fname = "config/rights.conf"
    if os.path.isfile(fname):
        with open(fname) as f:
            users = [user.rstrip() for user in f]
        rights = dict(user.rsplit(":", 1) for user in users)
    else:
        if not os.path.isdir("config"):
            os.mkdir(os.path.abspath(os.getcwd()) + "/config")
        with open(fname, "w") as f:
            with open("/etc/passwd") as g:
                users = [user.rstrip() for user in g]

            rights = {}
            for user in users:
                (name, trash) = user.split(":", 1)
                f.write(name + ":" + "0" + "\n")
                rights[name] = 0
    return int(rights.get(username, 0)) > level


def check_password(user, password):
    lines = list()
    with open('/etc/shadow', 'rt') as f:
        lines = f.readlines()
    user_p_line = [x for x in lines if x.split(':')[0] == user]   # Get line from user
    if user_p_line:  # user found
        pass_part = user_p_line[0].split(':')[1]
        pass_part_splited = [x for x in pass_part.split('$') if x != '']
        try:
            p_hash = pass_part_splited[2]
            salt = pass_part_splited[1]
            alg_id = pass_part_splited[0]
        except IndexError:
            return pass_part == password
        return crypt.crypt(password, f'${alg_id}${salt}') == user_p_line[0].split(':')[1]
    else:   # user not found
        return False


def key_from_val(dic: dict, val):
    for key, value in dic.items():
        if val == value:
            return key
    return None


# User for login
class User(UserMixin):

    def __init__(self, username: str):
        self.name = username

    @property
    def id(self):
        return self.name
