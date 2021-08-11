import glob
import os
import subprocess
import threading
import time
import psutil

from collections import deque
from src.shared import Actions, Monitor, eprint, shutdown_event, key_from_val


class ResourceChecker:
    def __init__(self, username: str):
        # read from /proc/meminfo
        self.user = username
        self.monitor = None  # One of Monitor
        self.path = None
        self.action = None
        self.monitor_time = None  # Time in seconds or None for proccess monitoring
        self.monitor_value = None  # Kb/s - network; % usage for ram and cpu; pid of proces
        self.running = False
        self.stop = False

    @property
    def is_running(self):
        return self.running

    def is_set(self):
        return self.monitor is not None

    def get_stat(self):
        return {
            'user': self.user,
            'monitor': key_from_val(Monitor, self.monitor),
            'script': self.path,
            'action': key_from_val(Actions, self.action),
            'running': self.running,
            'value': self.monitor_value,
            'time': self.monitor_time
        }

    def do_action(self):
        action = self.action
        eprint(action)
        if self.path:  # TODO maybe check if exist
            os.system(f"/bin/su -s /bin/bash -c '{self.path}' {self.user}")
        if action:
            shutdown_event.set()
            os.system(action)
        else:
            self.running = False  # whether timer is running or not
            self.stop = False  # whether timer should stop

    def set_action(self, action: str):  # TODO check
        self.action = action

    def set_script(self, path: str):  # TODO check
        self.path = path

    def set_monitor(self, resource: str, value=None, _time: int = None):
        self.monitor = Monitor.get(resource)
        assert self.monitor is not None
        if self.monitor == 'net':
            assert _time is not None or value is not None
            self.monitor_time = _time
            self.monitor_value = value
        elif self.monitor == 'cpu':
            assert _time is not None or value is not None
            self.monitor_time = _time
            self.monitor_value = value
        elif self.monitor == 'ram':
            assert _time is not None or value is not None
            self.monitor_time = _time
            self.monitor_value = value
        elif self.monitor == 'audio':
            assert _time is not None
            self.monitor_time = _time
        elif self.monitor == 'proc':
            assert value is not None
            self.monitor_value = value
        elif self.monitor == 'disp':
            assert _time is not None
            self.monitor_time = _time
        else:
            raise ValueError(f'Bad argument{self.monitor}')

    def __call__(self):
        self.start_monitor()

    def start_monitor(self):
        self.running = True
        if self.monitor == 'net':
            self.monitor_net()
        elif self.monitor == 'cpu':
            self.monitor_cpu()
        elif self.monitor == 'ram':
            self.monitor_ram()
        elif self.monitor == 'audio':
            self.monitor_audio()
        elif self.monitor == 'proc':
            self.monitor_proc()
        elif self.monitor == 'disp':
            self.monitor_disp()

    def monitor_cpu(self):
        
        while self.stop is False or not shutdown_event.is_set():
            if psutil.cpu_percent(interval=self.monitor_time) <= self.monitor_value:
                self.do_action()
                return
            time.sleep(1)

    def monitor_net(self):
        
        transfer_rate = deque(maxlen=1)
        event = threading.Event()
        t = threading.Thread(target=network_usage,
                             kwargs={'rate': transfer_rate, 'interval': 1, 'e': event})
        t.daemon = True
        t.start()
        n_usage = list()
        while self.stop is False or not shutdown_event.is_set():
            time.sleep(1)
            try:
                upload = transfer_rate[-1][0]
                download = transfer_rate[-1][1]
            except IndexError:
                ...
            else:
                n_usage.append(upload + download)
            if len(n_usage) >= self.monitor_time:
                n_usage.pop(0)
            if len(n_usage) == self.monitor_time:
                avg = sum(n_usage) / len(n_usage)
                if avg < self.monitor_value:
                    event.set()
                    self.do_action()
                    return

    def monitor_ram(self):
        
        l_usage = list()
        while self.stop is False or not shutdown_event.is_set():
            l_usage.append(psutil.virtual_memory().percent)
            if len(l_usage) > self.monitor_time:
                l_usage = l_usage.pop(0)
            if len(l_usage) == self.monitor_time:
                avg = sum(l_usage) / len(l_usage)
                if avg < self.monitor_value:
                    self.do_action()
                    return
            time.sleep(1)

    def monitor_audio(self):
        
        count = 0
        while self.stop is False or not shutdown_event.is_set():
            out = subprocess.call(['grep', 'state:'] + glob.glob('/proc/asound/card*/pcm*/sub*/status'))
            if out == 1:  # grep return 0 when 'state:' is found; 1 when not found
                count += 1
            elif out == 0:
                count = 0
            if count == self.monitor_time:
                self.do_action()
                return
            time.sleep(1)

    def monitor_proc(self):
        
        while self.stop is False or not shutdown_event.is_set():
            if psutil.pid_exists(self.monitor_value):
                process = psutil.Process(self.monitor_value)
                stat = process.status()
                if stat is psutil.STATUS_DEAD:
                    self.do_action()
                    return
            else:
                self.do_action()
                return
            time.sleep(5)

    def monitor_disp(self):
        
        os.putenv('DISPLAY', ':0.0')
        os.environ['DISPLAY'] = ':0.0'
        count = 0
        stdout = ''
        while self.stop is False or not shutdown_event.is_set():
            xset = subprocess.Popen(['xset', 'q'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            try:
                stdout = xset.communicate(timeout=15)  # [0]
            except subprocess.TimeoutExpired as e:
                xset.kill()
                eprint(str(e))
            if xset.returncode == 0:
                sed = subprocess.Popen(['sed', 'ne', "'s/^[ ]*Monitor is //p'"], stdout=subprocess.PIPE,
                                       stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
                try:
                    stdout = sed.communicate(input=stdout[0], timeout=15)[0]
                except subprocess.TimeoutExpired as e:
                    xset.kill()
                    eprint(str(e))
                else:
                    if stdout == 'Off':
                        count += 1
                    else:
                        count = 0
            if count * 2 >= self.monitor_time:
                self.do_action()
                return
            time.sleep(2)


def network_usage(rate: deque, interval: int, e: threading.Event):
    t0 = time.time()
    counter = psutil.net_io_counters()
    tot = (counter.bytes_sent, counter.bytes_recv)
    while not e.is_set() or not shutdown_event.is_set():
        last_tot = tot
        time.sleep(interval)
        counter = psutil.net_io_counters()
        t1 = time.time()
        tot = (counter.bytes_sent, counter.bytes_recv)
        ul, dl = [(now - last) / (t1 - t0) / 1000.0
                  for now, last in zip(tot, last_tot)]
        rate.append((ul, dl))
        t0 = time.time()
