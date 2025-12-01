from flask import Blueprint, render_template
from functions.services import get_server_info
from dotenv import load_dotenv
import os

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')

bp_home = Blueprint('home', __name__)

@bp_home.route(f'{FLASK_PREFIX}/home')
def home():
    server_hostname, _ = get_server_info()
    return render_template("home.html", server_hostname=server_hostname, FLASK_PREFIX=FLASK_PREFIX)
