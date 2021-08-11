#!/usr/bin/python3

import time
import os

from src.shared import Actions, shutdown_event, key_from_val, eprint


class Timer:
    def __init__(self, username: str):
        self.user = username
        self.path = None        # path to script to be executed after time expires
        self.action = None      # Action to be executed
        self.time_set = 0       # time set to the timer
        self.time_left = 0      # time left after start of timer
        self.running = False    # whether timer is running or not
        self.stop = False       # whether timer should stop

    @property
    def is_running(self):
        return self.running

    def set_timer(self, time_set: int):
        self.time_set = self.time_left = time_set
        self.running = False
        self.stop = False

    def get_stat(self):
        return {
            'user': self.user,
            'time_set': self.time_set,
            'time_left': self.time_left,
            'script': self.path,
            'action': key_from_val(Actions, self.action),
            'running': self.running
        }

    def set_action(self, action: str):
        self.action = action

    def set_script(self, path: str):
        self.path = path

    def __call__(self):
        self.start()

    def start(self):
        assert self.time_set != 0
        assert self.running is False
        self.running = True
        for i in range(self.time_set):  # TODO notify
            if self.stop:
                self.running = False
                self.time_left = self.time_set
                self.stop = False
                break
            self.time_left -= 1
            time.sleep(1)
            if self.time_left == 0:
                self.do_action()
                return

    def do_action(self):
        action = self.action
        eprint(action)
        if self.path:  # TODO maybe check if exist
            os.system(f"/bin/su -s /bin/bash -c '{self.path}' {self.user}")
        if self.stop is True:
            self.running = False
            self.time_left = self.time_set
            self.stop = False
        if action:
            shutdown_event.set()
            os.system(action)
        else:
            self.time_left = self.time_set
            self.running = False  # whether timer is running or not
            self.stop = False  # whether timer should stop
