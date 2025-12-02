from functions.services import get_server_info
from flask import Blueprint, render_template, jsonify, request
from functions.reports import count_todays_incidents
import os
import json

FLASK_PREFIX = os.getenv('PREFIX', '')
bp_reports = Blueprint('reports', __name__)
REPORTS_DIR = os.getenv('REPORTS_DIR', 'files/reports')


@bp_reports.route(f'{FLASK_PREFIX}/reports', methods=['GET'])
def reports():
    server_hostname, _ = get_server_info()
    todays_incidents_count = count_todays_incidents()
    available = {'services': set(), 'server': set()}
    for f in os.listdir(REPORTS_DIR):
        if f.endswith('_services_report.json'):
            date = f.split('_')[0]
            available['services'].add(date)
        elif f.endswith('_server_report.json'):
            date = f.split('_')[0]
            available['server'].add(date)

    available_list = {k: sorted(list(v), reverse=True) for k, v in available.items()}

    return render_template("reports.html", server_hostname=server_hostname, 
                                           available_list=available_list,
                                           todays_incidents_count=todays_incidents_count,
                                           VERSAO=os.getenv('VERSION', 'development'))


@bp_reports.route(f'{FLASK_PREFIX}/reports/data', methods=['GET'])
def reports_data():
    filename = request.args.get('file')
    if not filename:
        return jsonify({'error':'Arquivo não especificado'}),400
    filepath = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'error':f'Arquivo {filename} não encontrado'}),404
    with open(filepath,'r',encoding='utf-8') as f:
        data=json.load(f)
    return jsonify(data)