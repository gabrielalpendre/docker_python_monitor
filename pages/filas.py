from flask import Blueprint, render_template
from dotenv import load_dotenv
import os

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')

if FLASK_PREFIX != '/homol':
    bp_filas = Blueprint('filas', __name__)

    @bp_filas.route(f'{FLASK_PREFIX}/filas')
    def filas():
        return render_template("filas.html", FLASK_PREFIX=FLASK_PREFIX)
