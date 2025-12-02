from flask import Blueprint, render_template
from functions.reports import count_todays_incidents
from dotenv import load_dotenv
import os

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')

if FLASK_PREFIX != '/homol':
    bp_filas = Blueprint('filas', __name__)

    @bp_filas.route(f'{FLASK_PREFIX}/filas')
    def filas():
        todays_incidents_count = count_todays_incidents()
        return render_template("filas.html", FLASK_PREFIX=FLASK_PREFIX,
                                             todays_incidents_count=todays_incidents_count,
                                             VERSAO=os.getenv('VERSION', 'development'))
