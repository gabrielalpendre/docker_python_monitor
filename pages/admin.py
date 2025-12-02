from flask import Blueprint, request, jsonify, render_template
from functions.admin import get_excluded_services, save_excluded_services, get_medium_execution_time
from functions.scheduler import get_scheduler_interval 
from functions.reports import count_todays_incidents
from functions.services import get_services
from dotenv import load_dotenv
import os

load_dotenv(override=True)

FLASK_PREFIX = os.getenv('PREFIX', '')
ADMIN_DIR = os.getenv('ADMIN_DIR', '')
VERSAO = os.getenv('VERSION', 'development')

bp_admin = Blueprint('admin', __name__)

@bp_admin.route(f'{FLASK_PREFIX}/admin', methods=['GET', 'POST'])
def admin():
    services = get_services()
    excluded_services = get_excluded_services()
    tempo_medio = get_medium_execution_time('scheduler')
    interval_data = get_scheduler_interval()
    todays_incidents_count = count_todays_incidents()
    current_interval = interval_data.get("interval_time") if isinstance(interval_data, dict) else interval_data

    if request.method == 'POST':
        form_type = request.json.get('form_type')
        if form_type == 'excludedForm':
            selected_services = request.json.get('excluded_services')
            save_excluded_services(selected_services)
            return jsonify({'message': 'Servico(s) excluidos!'})

    return render_template("admin.html",
                           services=services,
                           excluded_services=excluded_services,
                           tempo_medio=tempo_medio,
                           current_interval=current_interval,
                           FLASK_PREFIX=FLASK_PREFIX,
                           VERSAO=VERSAO,
                           todays_incidents_count=todays_incidents_count)
