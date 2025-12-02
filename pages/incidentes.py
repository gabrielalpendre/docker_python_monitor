from flask import Blueprint, render_template, request
from dotenv import load_dotenv
from functions.reports import load_incidents, count_todays_incidents
import os

load_dotenv(override=True)
FLASK_PREFIX = os.getenv('PREFIX', '')

bp_incidentes = Blueprint('incidentes', __name__)

@bp_incidentes.route(f'{FLASK_PREFIX}/incidentes', methods=['GET'])
def incidentes():
    filter_service = request.args.get('service')
    filter_type = request.args.get('type')
    history, services, types, type_map = load_incidents(filter_service, filter_type)
    todays_incidents_count = count_todays_incidents()

    return render_template("incidentes.html", history=history, 
                                              services=services, types=types, 
                                              type_map=type_map, 
                                              FLASK_PREFIX=FLASK_PREFIX, 
                                              todays_incidents_count=todays_incidents_count,
                                              VERSAO=os.getenv('VERSION', 'development'))
