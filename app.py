from pages.admin import bp_admin
from pages.logs import bp_logs
from pages.home import bp_home
from pages.reports import bp_reports
from pages.incidentes import bp_incidentes
from backend.services import bp_stats
from backend.services import bp_stats_status
from backend.services import bp_server
from backend.admin import bp_reset_log
from backend.admin import bp_m_time
from backend.admin import bp_set_interval
from backend.alert import bp_load_config
from backend.alert import bp_toggle_alert
from backend.alert import bp_get_a_schedule
from backend.alert import bp_upd_a_schedule
from backend.alert import bp_test_alert
from backend.alert import bp_send_alert
from backend.api import create_api_blueprint
from backend.docs import setup_swagger
from functions.scheduler import run_scheduler_in_background
from functions.log import setup_logger, log_message
from flask import Flask, redirect
from dotenv import load_dotenv
import socket
import signal
import sys
import os

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')
FLASK_PORT = int(os.getenv("FLASK_PORT", 4005))

def start_flask():
    app = Flask(__name__)
    log_message('warning', "### Iniciando o servidor Flask...")
    os.makedirs("files", exist_ok=True)
    app.register_blueprint(bp_admin)
    app.register_blueprint(bp_m_time)
    app.register_blueprint(bp_reset_log)
    app.register_blueprint(bp_set_interval)
    app.register_blueprint(bp_logs)
    app.register_blueprint(bp_home)
    app.register_blueprint(bp_reports)
    app.register_blueprint(bp_incidentes)
    app.register_blueprint(bp_stats)
    app.register_blueprint(bp_stats_status)
    app.register_blueprint(bp_server)
    app.register_blueprint(bp_load_config)
    app.register_blueprint(bp_toggle_alert)
    app.register_blueprint(bp_get_a_schedule)
    app.register_blueprint(bp_upd_a_schedule)
    app.register_blueprint(bp_test_alert)
    app.register_blueprint(bp_send_alert)
    app.register_blueprint(create_api_blueprint(app))
    if FLASK_PREFIX != '/homol':
        from pages.tabelas import bp_tabelas
        from backend.queryes import bp_queryes
        from backend.queryes import bp_queryes_status
        from pages.filas import bp_filas
        from backend.queues import bp_queues
        from backend.queues import bp_queues_status
        app.register_blueprint(bp_tabelas)
        app.register_blueprint(bp_queryes)
        app.register_blueprint(bp_queryes_status)
        app.register_blueprint(bp_filas)
        app.register_blueprint(bp_queues)
        app.register_blueprint(bp_queues_status)
    
    setup_swagger(app)

    @app.route('/')
    def index():
        return redirect(f'{FLASK_PREFIX}/home')
    if FLASK_PREFIX:
        @app.route(f'{FLASK_PREFIX}')
        def home_redirect():
            return redirect(f'{FLASK_PREFIX}/home')
    app.run(host='0.0.0.0', port=FLASK_PORT)

def shutdown_gracefully(signal, frame):
    log_message(f'warning', "### Encerrando o servidor Flask e o agendador...")
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown_gracefully)
signal.signal(signal.SIGTERM, shutdown_gracefully)

if __name__ == "__main__":
    run_scheduler_in_background()
    setup_logger()
    start_flask()
    ip = os.getenv('SERVER_IP', socket.gethostbyname(socket.gethostname()))
    print(f"http://{ip}:{FLASK_PORT}")