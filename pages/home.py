from flask import Blueprint, render_template
from functions.services import get_server_info
from functions.reports import count_todays_incidents
from dotenv import load_dotenv
import os

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')

bp_home = Blueprint('home', __name__)

@bp_home.route(f'{FLASK_PREFIX}/home')
def home():
    server_hostname, _ = get_server_info()
    todays_incidents_count = count_todays_incidents()
    return render_template("home.html", server_hostname=server_hostname, 
                                        FLASK_PREFIX=FLASK_PREFIX,
                                        todays_incidents_count=todays_incidents_count,
                                        VERSAO=os.getenv('VERSION', 'development'))
