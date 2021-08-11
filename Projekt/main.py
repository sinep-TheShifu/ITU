#!/usr/bin/python3
import threading
import os.path
import json
import psutil

from datetime import timedelta
from flask import flash, Flask, jsonify, redirect, render_template, request, Response, send_file, send_from_directory, session, url_for
from flask_login import current_user, login_required, login_user, logout_user, LoginManager, UserMixin
from src.shared import User, list_users, list_processes, check_password, check_permissions, timers, monitors, get_timer_monitor, eprint
from src.timer import Timer, Actions
from src.resource_monitor import ResourceChecker, Monitor


app = Flask(__name__)
app.config["SECRET_KEY"] = "c7d6ee3e38c6ce4c50aedeedcf622b9f"
app.app_context().push()
login_manager = LoginManager()
login_manager.init_app(app)

# Website switch
# login_manager.login_view = "index"
login_manager.login_view = "roman_index"

login_manager.login_message = "You will need to log in to gain access to this page."
users = list_users()
threads = list()


@app.route("/")
def index():
    if current_user.is_authenticated:
        return render_template('index.html')
    return render_template('login.html')


@app.route("/roman/")
def roman_index():
    if current_user.is_authenticated:
        return render_template('rhome.html')
    return render_template('rauthenticate.html')


@app.route("/api/timer/start", methods=["POST"])
@login_required
def start_timer():
    if check_permissions(current_user.name, 1):
        eprint('User doesn\'t have permissions to start timer') # TODO debuging
        return json.dumps({'success': False}), 401, {'ContentType': 'application/json'}

    timer_data = request.get_json(force=True)
    time_sec = timer_data['time']
    action = Actions[timer_data['action']]
    path = timer_data['script']
    eprint('start_timer: JSON ok') # TODO debuging
    timer = get_timer_monitor(timers, current_user.name)
    if timer.is_running:
        eprint('Timer is already running')
        return json.dumps({'success': False}), 400, {'ContentType': 'application/json'}
    if timer is None:
        eprint('No timer found') # TODO debuging
        return json.dumps({'success': False}), 400, {'ContentType': 'application/json'}
    timer.set_timer(time_sec)
    timer.set_action(action)
    timer.set_script(path)
    eprint('Timer is set')  # TODO debuging
    t = threading.Thread(target=timer)
    threads.append((t, current_user, timer))
    t.daemon = True
    t.start()
    eprint('Timer is running')  # TODO debuging
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


@app.route("/api/get/processes")
@login_required
def get_processes():
    result = dict()
    for p in psutil.process_iter():
        result[p.pid] = p.name()
    return json.dumps(result), 200, {'ContentType': 'application/json'}


@app.route("/api/timer/stop")
@login_required
def stop_timer():
    if check_permissions(current_user.name, 1):
        return json.dumps({'success': False}), 401, {'ContentType': 'application/json'}

    timer = get_timer_monitor(timers, current_user.name)
    if timer:
        timer.stop = True
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    else:
        return json.dumps({'success': False}), 400, {'ContentType': 'application/json'}


@app.route("/api/timer/status")
@login_required
def stat_timer():
    timer = get_timer_monitor(timers, current_user.name)
    if timer is None:
        return json.dumps({'success': False}), 400, {'ContentType': 'application/json'}
    return json.dumps(timer.get_stat()), 200, {'ContentType': 'application/json'}


@app.route("/api/monitor/start", methods=["POST"])
@login_required
def start_monitor():  # list of monitors in json start every
    if check_permissions(current_user.name, 1):
        return json.dumps({'success': False}), 401, {'ContentType': 'application/json'}

    monitor_data = request.get_json(force=True)
    _monitors = [monitor for monitor in monitors if monitor.user == current_user.name]
    for monitor in _monitors:
        if monitor.is_running:
            monitor.stop = True
            monitors.remove(monitor)
        if monitor is None:
            monitors.remove(monitor)
    if isinstance(monitor_data, dict):
        time_sec = monitor_data['time']
        action = Actions[monitor_data['action']]
        resource = monitor_data['resource']
        value = monitor_data.get('value')
        path = monitor_data['script']
        monitor.set_monitor(resource, value, time_sec)
        monitor.set_action(Actions[action])
        monitor.set_script(path)
        t = threading.Thread(target=monitor)
        threads.append((t, current_user, monitor))
        t.daemon = True
        t.start()
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    else:
        for mon_data in monitor_data:
            time_sec = mon_data['time']
            action = Actions[mon_data['action']]
            resource = mon_data['resource']
            value = mon_data.get('value')
            path = mon_data['script']
            monitor = ResourceChecker(current_user.name)
            monitor.set_monitor(resource, value, time_sec)
            monitor.set_action(action)
            monitor.set_script(path)
            monitors.append(monitor)
            t = threading.Thread(target=monitor)
            threads.append((t, current_user, monitor))
            t.daemon = True
            t.start()
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


@app.route("/api/monitor/stop")
@login_required
def stop_monitor():
    if check_permissions(current_user.name, 1):
        return json.dumps({'success': False}), 401, {'ContentType': 'application/json'}

    _monitors = [monitor for monitor in monitors if monitor.user == current_user.name]
    if _monitors:
        for monitor in _monitors:
            monitor.stop = True
            monitors.remove(monitor)
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    else:
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


@app.route("/api/monitor/status")
@login_required
def stat_monitor():
    _monitors = [monitor for monitor in monitors if monitor.user == current_user.name]
    stat_monitors = list()
    for monitor in _monitors:
        stat_monitors.append(monitor.get_stat())
    if not _monitors:
        return json.dumps({'success': False}), 400, {'ContentType': 'application/json'}
    return json.dumps(stat_monitors), 200, {'ContentType': 'application/json'}


@app.route("/api/logout/")
@login_required
def logout():
    logout_user()
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


@app.route("/web/logout/")
@login_required
def web_logout():
    logout_user()
    return render_template("login.html", form=request.form)


@app.route("/roman/logout/")
@login_required
def roman_logout():
    logout_user()
    flash("You have been logged off.")
    return render_template("rauthenticate.html", form=request.form)


@app.route("/api/login", methods=["POST"])
def login():
    log_data = request.get_json(force=True)
    username = log_data['login']
    password = log_data['password']
    if check_permissions(username, 3):
        return json.dumps({'success': False}), 401, {'ContentType': 'application/json'}
    if check_password(username, password):
        user_to_login = None
        for user in users:
            if user.id == username:
                user_to_login = user
                break
        if user_to_login is not None:
            login_user(user_to_login)
            timer = get_timer_monitor(timers, user_to_login.name)
            if not timer:
                timers.append(Timer(user_to_login.name))
            return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
        else:
            return json.dumps({'success': False}), 403, {'ContentType': 'application/json'}
    else:
        return json.dumps({'success': False}), 401, {'ContentType': 'application/json'}


@app.route("/web/login", methods=["GET", "POST"])
def web_login():
    if current_user.is_authenticated:
        return render_template("index.html")
    if request.method == "GET":
        return render_template("login.html", form=request.form)

    username = request.form.get("login", None)
    password = request.form.get("password", None)

    if check_permissions(username, 3):
        return render_template("login.html", form=request.form)
    if check_password(username, password):
        user_to_login = None
        for user in users:
            if user.id == username:
                user_to_login = user
                break
        if user_to_login is not None:
            login_user(user_to_login)
            timers.append(Timer(user_to_login.name))
            # monitors.append(ResourceChecker(user_to_login.name))
            return render_template("index.html")
        else:
            return render_template("login.html", form=request.form)
    else:
        return render_template("login.html", form=request.form)


@app.route("/roman/login", methods=["GET", "POST"])
def roman_login():
    if current_user.is_authenticated:
        return render_template("rhome.html")
    if request.method == "GET":
        return render_template("rauthenticate.html", form=request.form)

    username = request.form.get("login", None)
    password = request.form.get("password", None)

    if check_permissions(username, 3):
        flash("You don't have permission to use this application. If you think you should have it, please contact your administrator to change it.")
        return render_template("rauthenticate.html", form=request.form)
    if check_password(username, password):
        user_to_login = None
        for user in users:
            if user.id == username:
                user_to_login = user
                break
        if user_to_login is not None:
            login_user(user_to_login)
            timers.append(Timer(user_to_login.name))
            monitors.append(ResourceChecker(user_to_login.name))
            return render_template("rhome.html")
        else:
            flash("Something went wrong. Please try again.")
            return render_template("rauthenticate.html", form=request.form)
    else:
        flash("Your credentials were incorrect. Please try again.")
        return render_template("rauthenticate.html", form=request.form)


@app.route("/api/permissions/view")
@login_required
def permissons_view():
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
    return json.dumps(rights), 200, {'ContentType': 'application/json'}


@app.route("/api/permissions/edit/<username>/<level>")
@login_required
def permissons_edit(username, level):
    if username == "root" and level != 0:
        return json.dumps({'success': False}), 403, {'ContentType': 'application/json'}

    fname = "config/rights.conf"
    if os.path.isfile(fname):
        with open(fname, 'r+') as f:
            users  = [user.rstrip() for user in f]
            rights = dict(user.rsplit(":", 1) for user in users)
            if rights.get(current_user.name, 0) != '0':
                return json.dumps({'success': False}), 401, {'ContentType': 'application/json'}

            if rights.get(username) is not None:
                rights[username] = level

            f.seek(0)
            for rname, rlevel in rights.items():
                f.write(rname + ":" + rlevel + "\n")
            f.truncate()
    else:
        if not os.path.isdir("config"):
            os.mkdir(os.path.abspath(os.getcwd()) + "/config")
        with open(fname, "w") as f:
            with open("/etc/passwd") as g:
                users = [user.rstrip() for user in g]

            for user in users:
                (name, trash) = user.split(":", 1)
                if name == username:
                    f.write(name + ":" + level + "\n")
                else:
                    f.write(name + ":" + "0" + "\n")
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


@login_manager.user_loader
def load_user(user_id):
    global users
    for user in users:
        if user.id == user_id:
            return user


@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=15)
    session.modified = True


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def default_lost(path):
    # Website switch
    '''
    if current_user.is_authenticated:
        return render_template('index.html')
    return render_template('login.html')
    '''
    if current_user.is_authenticated:
        return render_template('rhome.html')
    return render_template('rauthenticate.html')
    # '''


if __name__ == '__main__':
    from sys import argv
    debug = True
    host = '127.0.0.1'
    port = 5000
    if len(argv) > 2:
        if '-no-debug' in argv:
            debug = False
        host = argv[1].split(':')[0]
        port = int(argv[1].split(':')[1])
    elif len(argv) == 2:
        host = argv[1].split(':')[0]
        port = int(argv[1].split(':')[1])
    app.run(debug=debug, host=host, port=port)
