from flask import Blueprint, render_template
from dotenv import load_dotenv
from functions.reports import count_todays_incidents
from functions.services import get_server_info
import os

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')

if FLASK_PREFIX != '/homol':
    bp_tabelas = Blueprint('tabelas', __name__)

    @bp_tabelas.route(f'{FLASK_PREFIX}/tabelas')
    def tabelas():
        db_hostname, db_ip = get_server_info(return_db_info=True)
        todays_incidents_count = count_todays_incidents()
        return render_template("tabelas.html", db_hostname=db_hostname,
                                               todays_incidents_count=todays_incidents_count,
                                               VERSAO=os.getenv('VERSION', 'development'))